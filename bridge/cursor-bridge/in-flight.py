#!/usr/bin/env python3
"""Append one clock-stamped line to the Workspace in-flight log.

  python in-flight.py <text>
  python in-flight.py --file <path>
  python in-flight.py --pass <name> <reviewer> [--round <n>] [--cause <cause>]

The Workspace is the current folder, or its nearest parent, that holds
docs/PROJECT_STATUS.md. The log is that folder's run/supervisor/in-flight.md.
Exactly one source is accepted. Exit 0 prints each line written. Exit 2
writes nothing.
"""
import argparse
import datetime
import errno
import os
import re
import sys
import time
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bridge_env

REVIEWERS = (
    "review-a",
    "review-b",
    "security-auditor",
    "design-auditor",
    "plan-critic",
    "design-critic-b",
    "supervisor",
)
FILE_LIMIT = 65536
LOCK_SECONDS = 10
LOG_NAME = os.path.join("run", "supervisor", "in-flight.md")


class FlightParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.buffer.write(("in-flight: REFUSED - %s\n" % message).encode("utf-8", "replace"))
        raise SystemExit(2)


def say(line):
    sys.stdout.buffer.write((line + "\n").encode("utf-8"))
    sys.stdout.buffer.flush()


def refuse(reason):
    sys.stderr.buffer.write(("in-flight: REFUSED - %s\n" % reason).encode("utf-8"))
    return 2


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


def _strip_spaces(text):
    start = 0
    end = len(text)
    while start < end and unicodedata.category(text[start]) == "Zs":
        start += 1
    while end > start and unicodedata.category(text[end - 1]) == "Zs":
        end -= 1
    return text[start:end]


def _blank(line):
    return all(unicodedata.category(ch) == "Zs" for ch in line)


def _forbidden(text):
    return any(unicodedata.category(ch) in ("Cc", "Cf", "Zl", "Zp") for ch in text)


def _file_lines(text):
    lines = []
    buf = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "\r":
            lines.append("".join(buf))
            buf = []
            i += 2 if i + 1 < n and text[i + 1] == "\n" else 1
            continue
        if ch == "\n":
            lines.append("".join(buf))
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    lines.append("".join(buf))
    return lines


def _paused_body(line):
    i = 0
    while i < len(line) and unicodedata.category(line[i]) == "Zs":
        i += 1
    body = line[i:]
    if len(body) >= 7 and body[:7].lower() == "paused:":
        return body
    return None


def _text_and_pauses(raw, from_file):
    if from_file:
        rows = _file_lines(raw)
    else:
        rows = [raw]
    pauses = []
    kept = []
    for row in rows:
        body = _paused_body(row)
        if body is not None:
            pauses.append(body)
        if not _blank(row):
            kept.append(row)
    return _strip_spaces(" ".join(kept)), pauses


def _same(a, b):
    return os.path.normcase(os.path.normpath(a)) == os.path.normcase(os.path.normpath(b))


def _at_or_under(child, parent):
    child = os.path.normcase(os.path.normpath(child))
    parent = os.path.normcase(os.path.normpath(parent))
    try:
        return os.path.commonpath([child, parent]) == parent
    except ValueError:
        return False


def _reparse(path):
    try:
        if os.path.islink(path):
            return True
        if os.path.isjunction(path):
            return True
    except OSError:
        return False
    return False


def _through_link(supervisor, given):
    """The file is a symbolic link, or a folder between supervisor and the file is a link or junction."""
    sup_real = os.path.realpath(supervisor)
    path = given if os.path.isabs(given) else os.path.join(os.getcwd(), given)
    drive, tail = os.path.splitdrive(path)
    parts = tail.replace("/", os.sep).replace("\\", os.sep).split(os.sep)
    current = (drive + os.sep) if drive else os.sep
    for part in parts:
        if part == "" or part == ".":
            continue
        if part == "..":
            parent = os.path.dirname(current.rstrip(os.sep))
            if parent:
                current = parent
            continue
        nxt = os.path.join(current, part)
        if _reparse(nxt):
            try:
                parent_real = os.path.realpath(current)
            except OSError:
                parent_real = ""
            if parent_real and _at_or_under(parent_real, sup_real):
                return True
        current = nxt
    return False


def _read_source(workspace, given):
    if "\x00" in given:
        return None, "the file is not under run/supervisor"
    supervisor = os.path.join(workspace, "run", "supervisor")
    if _through_link(supervisor, given):
        return None, "the path reaches the file through a link"
    try:
        file_real = os.path.realpath(given)
        sup_real = os.path.realpath(supervisor)
        log_real = os.path.realpath(os.path.join(supervisor, "in-flight.md"))
    except OSError:
        return None, "the file cannot be read"
    if not _at_or_under(file_real, sup_real) or _same(file_real, sup_real):
        return None, "the file is not under run/supervisor"
    if _same(file_real, log_real):
        return None, "the file is the in-flight log"
    if os.path.isdir(file_real):
        return None, "the path is a folder"
    if not os.path.isfile(file_real):
        return None, "the file is missing"
    flags = os.O_RDONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(os.path.abspath(given), flags)
    except OSError:
        return None, "the file cannot be read"
    try:
        data = b""
        while len(data) <= FILE_LIMIT:
            piece = os.read(fd, FILE_LIMIT + 1 - len(data))
            if not piece:
                break
            data += piece
    except OSError:
        return None, "the file cannot be read"
    finally:
        os.close(fd)
    if len(data) > FILE_LIMIT:
        return None, "the file is larger than 65536 bytes"
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return None, "the file is not utf-8"
    return text, None


def _pass_text(args):
    name, reviewer = args.pass_name
    if re.fullmatch(bridge_env.GRAMMAR_ID_PATTERN, name) is None:
        return None, "the name is not an id"
    if reviewer not in REVIEWERS:
        return None, "the reviewer is outside the list"
    if args.round is not None and (args.round < 1 or args.round > 999):
        return None, "the round is outside 1 to 999"
    if args.cause is not None and args.cause not in bridge_env.ROUND_CAUSES:
        return None, "the cause is outside the round causes"
    parts = ["PASS", name]
    if args.round is not None:
        parts.append("r%d" % args.round)
    parts.append(reviewer)
    if args.cause is not None:
        parts.append(args.cause)
    return " ".join(parts), None


def prepare(args):
    """(workspace, lines, error). error is set when nothing may be written."""
    if args.round is not None or args.cause is not None:
        if args.pass_name is None:
            return None, None, "a round or a cause needs --pass"
    sources = (args.text is not None, bool(args.file), args.pass_name is not None)
    if sum(sources) == 0:
        return None, None, "no text"
    if sum(sources) > 1:
        return None, None, "more than one source"
    try:
        cwd = os.getcwd()
    except OSError:
        return None, None, "no Workspace"
    workspace = bridge_env.workspace_of(cwd)
    if not workspace:
        return None, None, "no Workspace"
    if args.pass_name is not None:
        text, err = _pass_text(args)
        if err:
            return None, None, err
        return workspace, [stamp() + " " + text], None
    if args.file:
        raw, err = _read_source(workspace, args.file)
        if err:
            return None, None, err
        text, pauses = _text_and_pauses(raw, True)
    else:
        text, pauses = _text_and_pauses(args.text, False)
    if text == "":
        return None, None, "no text"
    if _forbidden(text):
        return None, None, "a control character"
    return workspace, [stamp() + " " + text] + pauses, None


def _contended(exc):
    if isinstance(exc, BlockingIOError):
        return True
    return exc.errno in (errno.EACCES, errno.EAGAIN, errno.EDEADLOCK)


def _acquire(fd, seconds):
    deadline = time.monotonic() + seconds
    while True:
        try:
            if sys.platform == "win32":
                import msvcrt
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except OSError as exc:
            if not _contended(exc):
                raise
            left = deadline - time.monotonic()
            if left <= 0:
                return False
            time.sleep(min(0.05, left))


def _release(fd):
    try:
        if sys.platform == "win32":
            import msvcrt
            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_UN)
    except OSError:
        pass


def append_log(path, lines):
    """Append every line of this run in one write. None on success, otherwise a reason."""
    payload = "".join(line + "\n" for line in lines).encode("utf-8")
    folder = os.path.dirname(path)
    held = False
    fd = None
    try:
        os.makedirs(folder, exist_ok=True)
        fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_APPEND, 0o666)
        if not _acquire(fd, LOCK_SECONDS):
            return "the log was busy"
        held = True
        size = os.lseek(fd, 0, os.SEEK_END)
        if size:
            os.lseek(fd, size - 1, os.SEEK_SET)
            if os.read(fd, 1) != b"\n":
                payload = b"\n" + payload
        os.write(fd, payload)
        return None
    except OSError:
        return "the log cannot be written"
    finally:
        if held and fd is not None:
            _release(fd)
        if fd is not None:
            os.close(fd)


def build_parser():
    parser = FlightParser(
        prog="in-flight.py",
        description="Append one clock-stamped line to the Workspace in-flight log.")
    parser.add_argument("text", nargs="?", help="the line's text, one argument")
    parser.add_argument("--file", help="a file under run/supervisor/ whose lines become the text")
    parser.add_argument("--pass", nargs=2, metavar=("NAME", "REVIEWER"), dest="pass_name",
                        help="record a review pass of NAME by REVIEWER")
    parser.add_argument("--round", type=int, help="the pass round, a whole number from 1 to 999")
    parser.add_argument("--cause", help="the round cause, one word")
    return parser


def main():
    try:
        workspace, lines, err = prepare(build_parser().parse_args())
        if err:
            return refuse(err)
        err = append_log(os.path.join(workspace, LOG_NAME), lines)
        if err:
            return refuse(err)
        for line in lines:
            say(line)
        return 0
    except SystemExit:
        raise
    except Exception:
        return refuse("internal error")


if __name__ == "__main__":
    sys.exit(main())
