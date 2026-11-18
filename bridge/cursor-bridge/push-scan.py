#!/usr/bin/env python3
"""Scan every commit of a range before a push.

  python push-scan.py [<base>]

The base is one revision. When it is omitted, the base is the remote-tracking
branch that origin's HEAD names. The base commit itself is outside the range.

A path of this computer is a drive letter, a colon and one or more slashes,
then a segment; a Users directory or a home directory followed by a segment;
or the application-data segment with a slash directly before or after it.
A segment that begins with an angle bracket is a placeholder and passes.
An account name is a whole word, in any letter case. Names come from the
profile folder, the login, and the optional per-computer names file. They
are never taken from the command line and never printed.

Exit 0 when the range is clean, 1 when any place holds a hit, 2 when the
range, git or the names file cannot be read.
"""
import argparse
import difflib
import os
import re
import subprocess
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bridge_env

# Built from parts so the source holds none of the shapes the scan looks for.
_SLASH = "/"
_BACK = chr(92)
_USERS = _SLASH + "Us" + "ers" + _SLASH
_HOME = _SLASH + "ho" + "me" + _SLASH
_APPDATA = "App" + "Data"
_NULL_PATH = _SLASH + "dev" + _SLASH + "null"


class ScanError(Exception):
    def __init__(self, reason):
        self.reason = reason


def say(line):
    sys.stdout.buffer.write((line + "\n").encode("utf-8", errors="replace"))
    sys.stdout.buffer.flush()


def git(sub, args, options=None, feed=None):
    argv = ["git", "--no-pager", "--no-replace-objects", "-c", "color.ui=never", "-c", "log.showSignature=false", "-c", "log.showRoot=true", "-c", "diff.suppressBlankEmpty=false"]
    if options:
        argv.extend(options)
    argv.append(sub)
    argv.extend(args)
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            timeout=bridge_env.GIT_TIMEOUT,
            creationflags=bridge_env.NO_WINDOW,
            input=feed,
        )
    except FileNotFoundError:
        raise ScanError("git cannot be started")
    except subprocess.TimeoutExpired:
        raise ScanError("git %s took longer than %ss" % (sub, bridge_env.GIT_TIMEOUT))
    except OSError:
        raise ScanError("git cannot be started")
    out = proc.stdout if proc.stdout is not None else b""
    return proc.returncode, out


def git_text(sub, args):
    code, out = git(sub, args)
    return code, out.decode("utf-8", errors="replace")


def git_need(sub, args):
    code, out = git_text(sub, args)
    if code != 0:
        raise ScanError("git %s failed (exit %d)" % (sub, code))
    return out


def _bound(ch):
    return bool(ch) and (ch.isalpha() or ch.isdigit())


def _segment_start(ch):
    return ch.isalpha() or ch.isdigit() or ch in "_.-\x1b\x0e" or (not ch.isascii() and not ch.isspace())


def has_path(text):
    """A drive path, a Users or home directory with a segment, or the application-data segment."""
    n = len(text)
    i = 0
    while i < n:
        ch = text[i]
        if ch.isascii() and ch.isalpha() and (i == 0 or not _bound(text[i - 1])):
            if i + 2 < n and text[i + 1] == ":" and text[i + 2] in (_SLASH, _BACK):
                j = i + 2
                while j < n and text[j] in (_SLASH, _BACK):
                    j += 1
                if j < n and _segment_start(text[j]):
                    return True
        i += 1
    for prefix in (_USERS, _HOME):
        start = 0
        while True:
            found = text.find(prefix, start)
            if found < 0:
                break
            j = found + len(prefix)
            if j < n and _segment_start(text[j]):
                return True
            start = found + 1
    start = 0
    while True:
        found = text.find(_APPDATA, start)
        if found < 0:
            break
        before = found > 0 and text[found - 1] in (_SLASH, _BACK)
        after_at = found + len(_APPDATA)
        after = after_at < n and text[after_at] in (_SLASH, _BACK)
        if before or after:
            return True
        start = found + 1
    return False


def _caseless(text):
    return unicodedata.normalize("NFKC", unicodedata.normalize("NFKC", text).casefold())


def has_name(text, names):
    folded = _caseless(text)
    for name in names:
        if not name:
            continue
        pattern = re.compile("(?<![^\\W_])" + re.escape(_caseless(name)) + "(?![^\\W_])")
        if pattern.search(folded):
            return True
    return False


def kinds_of(text, names):
    found = []
    if has_path(text):
        found.append("path")
    if has_name(text, names):
        found.append("name")
    return found


def kinds_of_parts(parts, names):
    return kinds_of("\n".join(parts), names)


def profile_name():
    home = os.path.expanduser("~").rstrip(_SLASH + _BACK)
    if not home:
        return ""
    return os.path.basename(home)


def login_name():
    name = os.environ.get("USERNAME")
    if name is None or name == "":
        name = os.environ.get("USER")
    if name is None or name == "":
        return ""
    return name


def read_names_file():
    path = os.path.join(os.path.expanduser("~"), ".cursor-bridge", "names.txt")
    if not os.path.exists(path):
        return []
    if not os.path.isfile(path):
        raise ScanError("the names file cannot be read")
    try:
        handle = open(path, "rb")
    except OSError:
        raise ScanError("the names file cannot be read")
    try:
        raw = handle.read()
    except OSError:
        raise ScanError("the names file cannot be read")
    finally:
        handle.close()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise ScanError("the names file cannot be read")
    if text.startswith("\ufeff"):
        text = text[1:]
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            lines.append(stripped)
    return lines


def deduped_names():
    raw = []
    profile = profile_name()
    if profile:
        raw.append(profile)
    login = login_name()
    if login:
        raw.append(login)
    raw.extend(read_names_file())
    seen = set()
    ordered = []
    for name in raw:
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(name)
    return ordered


def owner_of(url):
    url = url.strip()
    if not url:
        return ""
    scheme = url.find("://")
    if scheme >= 0:
        rest = url[scheme + 3:]
        slash = rest.find(_SLASH)
        if slash < 0:
            return ""
        path = rest[slash + 1:]
    else:
        colon = url.find(":")
        if colon < 0 or "@" not in url[:colon]:
            return ""
        path = url[colon + 1:]
    parts = [part for part in path.split(_SLASH) if part]
    if len(parts) < 2:
        return ""
    return parts[-2]


def local_part(email):
    if not email or "@" not in email:
        return ""
    local, _sep, _domain = email.partition("@")
    return local


def git_config_value(key):
    code, out = git_text("config", ["--get", key])
    if code == 1:
        return ""
    if code != 0:
        raise ScanError("git config failed (exit %d)" % code)
    lines = out.splitlines()
    if not lines:
        return ""
    return lines[0]


def public_names():
    found = []
    code, out = git_text("remote", ["get-url", "origin"])
    if code == 0:
        lines = out.splitlines()
        owner = owner_of(lines[0]) if lines else ""
        if owner:
            found.append(owner)
    cfg_name = git_config_value("user.name")
    if cfg_name:
        found.append(cfg_name)
    cfg_email = git_config_value("user.email")
    local = local_part(cfg_email)
    if local:
        found.append(local)
    return found, cfg_name, cfg_email


def select_names(ordered, public):
    """Skip a short name (N1) and drop a public name (N2). Return the names searched and the notes."""
    public_keys = set(name.lower() for name in public)
    notes = []
    kept = []
    dropped = 0
    for index, name in enumerate(ordered, start=1):
        if len(name) < 4:
            notes.append("push-scan: note - name #%d is shorter than four characters and is skipped" % index)
            continue
        if name.lower() in public_keys:
            dropped += 1
            continue
        kept.append(name)
    if dropped:
        notes.append("push-scan: note - %d name(s) dropped as public with the repository" % dropped)
    return kept, notes


def carries_identity(name, email, cfg_name, cfg_email):
    if not cfg_name or not cfg_email or not email:
        return False
    return name == cfg_name and email.lower() == cfg_email.lower()


def split_ident(rest):
    end = rest.rfind("> ")
    start = rest.rfind(" <", 0, end if end >= 0 else len(rest))
    if start < 0 or end < 0 or end < start:
        return rest, ""
    return rest[:start], rest[start + 2:end]


def parse_commit(text):
    lines = [line[:-1] if line.endswith("\r") else line for line in text.split("\n")]
    author = ("", "")
    committer = ("", "")
    index = 0
    while index < len(lines):
        line = lines[index]
        index += 1
        if line == "":
            break
        if line.startswith("author "):
            author = split_ident(line[len("author "):])
        elif line.startswith("committer "):
            committer = split_ident(line[len("committer "):])
    message = "\n".join(lines[index:])
    return author, committer, message


def unquote_git(token):
    if len(token) < 2 or token[0] != '"' or token[-1] != '"':
        return token
    body = token[1:-1]
    raw = bytearray()
    index = 0
    simple = {
        "n": b"\n", "t": b"\t", "\\": b"\\", '"': b'"',
        "a": b"\a", "b": b"\b", "f": b"\f", "v": b"\v", "r": b"\r",
    }
    while index < len(body):
        ch = body[index]
        if ch != "\\":
            raw.extend(ch.encode("utf-8"))
            index += 1
            continue
        index += 1
        if index >= len(body):
            break
        esc = body[index]
        index += 1
        if esc in simple:
            raw.extend(simple[esc])
        elif "0" <= esc <= "7":
            digits = esc
            for _extra in range(2):
                if index < len(body) and "0" <= body[index] <= "7":
                    digits += body[index]
                    index += 1
                else:
                    break
            value = int(digits, 8)
            if value > 255:
                raise ScanError("the patch cannot be read")
            raw.append(value)
        else:
            raw.extend(esc.encode("utf-8"))
    return raw.decode("utf-8", errors="surrogateescape")


def strip_side(path, side):
    prefix = side + _SLASH
    if path.startswith(prefix):
        return path[len(prefix):]
    return path


def _patch_lines(text):
    lines = []
    for line in text.split("\n"):
        if line.endswith("\r"):
            line = line[:-1]
        lines.append(line)
    return lines


def _whole_digits(text):
    if not text:
        return False
    for ch in text:
        if ch < "0" or ch > "9":
            return False
    return True


def _path_from_rest(rest, strip_b):
    """The whole rest of a header line: one trailing tab, then git quoting, then an optional b/ prefix."""
    if rest.endswith("\t"):
        rest = rest[:-1]
    if len(rest) >= 2 and rest[0] == '"' and rest[-1] == '"':
        path = unquote_git(rest)
    else:
        path = rest
    if strip_b:
        path = strip_side(path, "b")
    return path


def _parse_hunk_header(header):
    """New-side start and count, and each old side's count. Raises when the numbers cannot be read."""
    n_at = 0
    while n_at < len(header) and header[n_at] == "@":
        n_at += 1
    if n_at < 2:
        raise ScanError("the patch cannot be read")
    rest = header[n_at:]
    close_at = rest.find("@")
    if close_at < 0:
        raise ScanError("the patch cannot be read")
    end = close_at
    while end < len(rest) and rest[end] == "@":
        end += 1
    if end - close_at != n_at:
        raise ScanError("the patch cannot be read")
    tokens = rest[:close_at].split()
    if not tokens:
        raise ScanError("the patch cannot be read")
    old_counts = []
    new_start = None
    new_count = None
    for token in tokens:
        if len(token) < 2 or token[0] not in "+-":
            raise ScanError("the patch cannot be read")
        sign = token[0]
        body = token[1:]
        if "," in body:
            start_text, count_text = body.split(",", 1)
            if not _whole_digits(start_text) or not _whole_digits(count_text):
                raise ScanError("the patch cannot be read")
            start = int(start_text, 10)
            count = int(count_text, 10)
        else:
            if not _whole_digits(body):
                raise ScanError("the patch cannot be read")
            start = int(body, 10)
            count = 1
        if start < 0 or count < 0:
            raise ScanError("the patch cannot be read")
        if sign == "+":
            if new_start is not None:
                raise ScanError("the patch cannot be read")
            new_start = start
            new_count = count
        else:
            if new_start is not None:
                raise ScanError("the patch cannot be read")
            old_counts.append(count)
    if new_start is None or len(old_counts) != n_at - 1:
        raise ScanError("the patch cannot be read")
    return len(old_counts), new_start, new_count, old_counts


def _blank_section():
    return {
        "path": None,
        "header": None,
        "pre_ids": None,
        "result_id": None,
        "has_hunks": False,
        "has_binary": False,
        "added": [],
    }


def _take_quoted(text):
    if not text.startswith('"'):
        raise ScanError("the patch cannot be read")
    index = 1
    while index < len(text):
        if text[index] == "\\":
            if index + 1 >= len(text):
                break
            index += 2
            continue
        if text[index] == '"':
            return text[:index + 1], text[index + 1:]
        index += 1
    raise ScanError("the patch cannot be read")


def _diff_git_path(rest):
    """The path of a ``diff --git`` header whose two sides name one file."""
    if rest.startswith('"'):
        left_tok, after = _take_quoted(rest)
        if not after.startswith(" "):
            raise ScanError("the patch cannot be read")
        right_tok, tail = _take_quoted(after[1:])
        if tail:
            raise ScanError("the patch cannot be read")
        left = strip_side(unquote_git(left_tok), "a")
        right = strip_side(unquote_git(right_tok), "b")
        if left != right:
            raise ScanError("the patch cannot be read")
        return left
    found = None
    start = 0
    while True:
        at = rest.find(" b/", start)
        if at < 0:
            break
        left = rest[:at]
        right = rest[at + 1:]
        if left.startswith("a/") and right.startswith("b/") and left[2:] == right[2:]:
            path = left[2:]
            if found is not None and found != path:
                raise ScanError("the patch cannot be read")
            found = path
        start = at + 1
    if found is None:
        raise ScanError("the patch cannot be read")
    return found


def _parse_index_line(line, hash_len):
    rest = line[len("index "):]
    parts = rest.split(" ")
    if not parts or not parts[0] or len(parts) > 2:
        raise ScanError("the patch cannot be read")
    if len(parts) == 2 and not _is_mode(parts[1]):
        raise ScanError("the patch cannot be read")
    token = parts[0]
    halves = token.split("..")
    if len(halves) != 2 or not halves[1]:
        raise ScanError("the patch cannot be read")
    pre = halves[0].split(",") if halves[0] else []
    if not pre:
        raise ScanError("the patch cannot be read")
    for oid in pre:
        if not _is_oid(oid, hash_len):
            raise ScanError("the patch cannot be read")
    if not _is_oid(halves[1], hash_len):
        raise ScanError("the patch cannot be read")
    return pre, halves[1]


def _finish_section(section):
    if section is None:
        return None
    if section["path"] is None and section["header"] is not None:
        section["path"] = _diff_git_path(section["header"])
    if section["path"] is None and (section["has_hunks"] or section["has_binary"] or section["added"]):
        raise ScanError("the patch cannot be read")
    if section["path"] is None:
        return None
    return section


def added_lines(text, hash_len):
    """Added lines of a patch, and every new path the patch names.

    Each added line is (new path, line number in the new file, text).
    A body line is never read as a header. A line that begins with ``diff `` ends the hunk.
    """
    found = []
    named = []
    sections = []
    section = None
    new_path = None
    in_hunk = False
    new_line = 1
    n_cols = 1
    remain_new = 0
    remain_old = []
    for line in _patch_lines(text):
        if line.startswith("diff "):
            in_hunk = False
            finished = _finish_section(section)
            if finished is not None:
                sections.append(finished)
            section = _blank_section()
            new_path = None
            if line.startswith("diff --cc "):
                new_path = _path_from_rest(line[len("diff --cc "):], False)
                named.append(new_path)
                section["path"] = new_path
            elif line.startswith("diff --combined "):
                new_path = _path_from_rest(line[len("diff --combined "):], False)
                named.append(new_path)
                section["path"] = new_path
            elif line.startswith("diff --git "):
                section["header"] = line[len("diff --git "):]
            continue
        if in_hunk:
            if line.startswith("\\"):
                continue
            if len(line) < n_cols:
                raise ScanError("the patch cannot be read")
            prefix = line[:n_cols]
            for ch in prefix:
                if ch not in " +-":
                    raise ScanError("the patch cannot be read")
            in_result = "-" not in prefix
            if in_result:
                if remain_new <= 0:
                    raise ScanError("the patch cannot be read")
                remain_new -= 1
                for index, ch in enumerate(prefix):
                    if ch == " ":
                        if remain_old[index] <= 0:
                            raise ScanError("the patch cannot be read")
                        remain_old[index] -= 1
                    elif ch != "+":
                        raise ScanError("the patch cannot be read")
                if "+" in prefix and new_line >= 1:
                    if new_path is None:
                        raise ScanError("the patch cannot be read")
                    found.append((new_path, new_line, line[n_cols:]))
                    if section is not None:
                        section["added"].append((new_line, line[n_cols:]))
                new_line += 1
            else:
                if "+" in prefix:
                    raise ScanError("the patch cannot be read")
                for index, ch in enumerate(prefix):
                    if ch == "-":
                        if remain_old[index] <= 0:
                            raise ScanError("the patch cannot be read")
                        remain_old[index] -= 1
                    elif ch != " ":
                        raise ScanError("the patch cannot be read")
            if remain_new == 0 and all(count == 0 for count in remain_old):
                in_hunk = False
            continue
        if line.startswith("rename to "):
            new_path = _path_from_rest(line[len("rename to "):], False)
            named.append(new_path)
            if section is not None:
                section["path"] = new_path
            continue
        if line.startswith("+++ "):
            path = _path_from_rest(line[len("+++ "):], True)
            if path == _NULL_PATH:
                new_path = None
            else:
                new_path = path
                named.append(new_path)
                if section is not None:
                    section["path"] = new_path
            continue
        if line.startswith("index ") and section is not None:
            if section["pre_ids"] is not None:
                raise ScanError("the patch cannot be read")
            section["pre_ids"], section["result_id"] = _parse_index_line(line, hash_len)
            continue
        if line.startswith("Binary files ") and section is not None:
            section["has_binary"] = True
            continue
        if line.startswith("@@"):
            n_cols, new_line, remain_new, remain_old = _parse_hunk_header(line)
            in_hunk = remain_new != 0 or any(count != 0 for count in remain_old)
            if section is not None:
                section["has_hunks"] = True
            continue
    if in_hunk:
        raise ScanError("the patch cannot be read")
    finished = _finish_section(section)
    if finished is not None:
        sections.append(finished)
    return found, named, sections


def _is_oid(text, size):
    if len(text) != size:
        return False
    for ch in text:
        if ch not in "0123456789abcdef":
            return False
    return True


def _is_mode(text):
    if len(text) != 6:
        return False
    for ch in text:
        if ch < "0" or ch > "7":
            return False
    int(text, 8)
    return True


def _ordinary_two_paths(status):
    """False for one path, True for a rename or copy score, None when the status is not allowed."""
    if status in ("A", "D", "M", "T"):
        return False
    if status[:1] in ("R", "C") and 2 <= len(status) <= 4 and _whole_digits(status[1:]):
        int(status[1:], 10)
        return True
    return None


def parse_raw_records(raw, n_parents, hash_len):
    """One record per path from ``git show -z --raw --no-abbrev``."""
    merge = n_parents > 1
    colons_needed = n_parents if merge else 1
    slots = colons_needed + 1
    parts = raw.split(b"\0")
    if parts and parts[-1] == b"":
        parts.pop()
    records = []
    seen = set()
    index = 0
    while index < len(parts):
        head = parts[index]
        index += 1
        try:
            text = head.decode("ascii")
        except UnicodeDecodeError:
            raise ScanError("the patch cannot be read")
        colon = 0
        while colon < len(text) and text[colon] == ":":
            colon += 1
        if colon != colons_needed or colon == len(text):
            raise ScanError("the patch cannot be read")
        fields = text[colon:].split(" ")
        if len(fields) != slots * 2 + 1 or "" in fields:
            raise ScanError("the patch cannot be read")
        modes = fields[:slots]
        oids = fields[slots:slots * 2]
        status = fields[-1]
        for mode in modes:
            if not _is_mode(mode):
                raise ScanError("the patch cannot be read")
        for oid in oids:
            if not _is_oid(oid, hash_len):
                raise ScanError("the patch cannot be read")
        if merge:
            if len(status) != n_parents:
                raise ScanError("the patch cannot be read")
            for ch in status:
                if ch not in "ADMTRC":
                    raise ScanError("the patch cannot be read")
            two = False
        else:
            two = _ordinary_two_paths(status)
            if two is None:
                raise ScanError("the patch cannot be read")
        if index >= len(parts):
            raise ScanError("the patch cannot be read")
        first = parts[index]
        index += 1
        if two:
            if index >= len(parts):
                raise ScanError("the patch cannot be read")
            new_raw = parts[index]
            index += 1
        else:
            new_raw = first
        path = new_raw.decode("utf-8", "surrogateescape")
        if path in seen:
            raise ScanError("the patch cannot be read")
        seen.add(path)
        records.append({"status": status, "path": path, "modes": modes, "ids": oids})
    return records


def hit_line(short, place, kind):
    return "push-scan: HIT %s %s %s" % (short, place, kind)


def _checked_short(text):
    if text.endswith("\n"):
        text = text[:-1]
    if text.endswith("\r"):
        text = text[:-1]
    if not text:
        raise ScanError("internal error")
    for ch in text:
        if ch not in "0123456789abcdef":
            raise ScanError("internal error")
    return text


def quote_path(path):
    """Print a path as itself, or quoted, so a control character cannot forge a line."""
    needs = False
    for ch in path:
        if ch == '"' or ch == "\\" or unicodedata.category(ch) in ("Cc", "Cf", "Zl", "Zp"):
            needs = True
            break
    if not needs:
        return path
    simple = {
        "\a": "\\a", "\b": "\\b", "\t": "\\t", "\n": "\\n",
        "\v": "\\v", "\f": "\\f", "\r": "\\r", '"': '\\"', "\\": "\\\\",
    }
    parts = ['"']
    for ch in path:
        if ch in simple:
            parts.append(simple[ch])
        elif unicodedata.category(ch) in ("Cc", "Cf", "Zl", "Zp"):
            for byte in ch.encode("utf-8"):
                parts.append("\\%03o" % byte)
        else:
            parts.append(ch)
    parts.append('"')
    return "".join(parts)


def _parent_count(text):
    count = 0
    for line in text.split("\n"):
        if line.endswith("\r"):
            line = line[:-1]
        if line == "":
            break
        if line.startswith("parent "):
            count += 1
    return count


def _one_line(out, failed):
    text = out.decode("utf-8", "replace")
    lines = []
    for line in text.split("\n"):
        if line.endswith("\r"):
            line = line[:-1]
        if line != "":
            lines.append(line)
    if len(lines) != 1:
        raise ScanError(failed)
    return lines[0]


def repository_ids():
    """The empty tree's id and the repository's hash length, once per run."""
    code, out = git("rev-parse", ["--show-object-format"])
    if code != 0:
        raise ScanError("git rev-parse failed (exit %d)" % code)
    kind = _one_line(out, "the patch cannot be read")
    if kind == "sha1":
        hash_len = 40
    elif kind == "sha256":
        hash_len = 64
    else:
        raise ScanError("the patch cannot be read")
    code, out = git("hash-object", ["-t", "tree", "--stdin"], feed=b"")
    if code != 0:
        raise ScanError("git hash-object failed (exit %d)" % code)
    empty = _one_line(out, "the patch cannot be read")
    if not _is_oid(empty, hash_len):
        raise ScanError("the patch cannot be read")
    return empty, hash_len


def _read_blob(oid):
    code, out = git("cat-file", ["blob", "--end-of-options", oid])
    if code != 0:
        raise ScanError("git cat-file failed (exit %d)" % code)
    return out


def classify_blob(data):
    """``marked``, ``binary`` or ``text`` from the blob's own bytes."""
    if data.startswith(b"\xff\xfe") or data.startswith(b"\xfe\xff"):
        return "marked"
    if b"\x00" in data[:8000]:
        return "binary"
    return "text"


def _zero_id(oid):
    for ch in oid:
        if ch != "0":
            return False
    return True


def _blob_text_lines(data, kind):
    if kind == "utf-16":
        codec = "utf-16-le" if data.startswith(b"\xff\xfe") else "utf-16-be"
        text = data[2:].decode(codec, "replace")
    else:
        text = data.decode("utf-8", "replace")
    return _patch_lines(text)


def _blob_views(data, kind):
    """Lines of each view, or ``None`` when the blob contributes no line."""
    if kind == "binary":
        return None
    if kind == "marked":
        return {
            "nul": _blob_text_lines(data.replace(b"\x00", b""), "text"),
            "utf16": _blob_text_lines(data, "utf-16"),
        }
    return {"nul": _blob_text_lines(data, "text")}


def _lines_of(views, name):
    if views is None:
        return []
    found = views.get(name)
    if found is None:
        return views["nul"]
    return found


def _preimage_lines(oid, mode):
    if _zero_id(oid) or mode == "160000":
        return None
    data = _read_blob(oid)
    return _blob_views(data, classify_blob(data))


def _trim_ends(pre_lines, result_lines):
    """Common leading and trailing lines, one to one, never overlapping."""
    lead = 0
    shorter = len(pre_lines)
    if len(result_lines) < shorter:
        shorter = len(result_lines)
    while lead < shorter and pre_lines[lead] == result_lines[lead]:
        lead += 1
    trail = 0
    pre_left = len(pre_lines) - lead
    result_left = len(result_lines) - lead
    while (
        trail < pre_left
        and trail < result_left
        and pre_lines[-1 - trail] == result_lines[-1 - trail]
    ):
        trail += 1
    return lead, pre_lines[lead:len(pre_lines) - trail], result_lines[lead:len(result_lines) - trail]


def _over_read(pre_count, result_count, work):
    """True when this pair is past the line-pair bounds. An over-read adds nothing."""
    product = pre_count * result_count
    if product > 1000000 or work[0] + product > 10000000:
        return True
    work[0] = work[0] + product
    return False


def _added_positions(pre_lines, result_lines, work):
    lead, pre_middle, result_middle = _trim_ends(pre_lines, result_lines)
    if _over_read(len(pre_middle), len(result_middle), work):
        positions = set()
        for at in range(len(result_middle)):
            positions.add(lead + at)
        return positions
    matcher = difflib.SequenceMatcher(None, pre_middle, result_middle, autojunk=False)
    positions = set()
    for tag, _i1, _i2, j1, j2 in matcher.get_opcodes():
        if tag == "insert" or tag == "replace":
            for at in range(j1, j2):
                positions.add(lead + at)
    return positions


def line_diff_added(record, result_data, result_kind, work):
    """Result lines added against every preimage, as (1-based line, text)."""
    result_views = _blob_views(result_data, result_kind)
    if result_kind == "marked":
        names = ("nul", "utf16")
    else:
        names = ("nul",)
    preimages = []
    for oid, mode in zip(record["ids"][:-1], record["modes"][:-1]):
        preimages.append(_preimage_lines(oid, mode))
    by_number = {}
    for name in names:
        result_lines = result_views[name]
        common = None
        for views in preimages:
            positions = _added_positions(_lines_of(views, name), result_lines, work)
            if common is None:
                common = positions
            else:
                common = common & positions
        if common is None:
            common = set(range(len(result_lines)))
        for at in common:
            text = result_lines[at]
            held = by_number.get(at)
            if held is None:
                by_number[at] = [text]
            elif text not in held:
                held.append(text)
    found = []
    for at in sorted(by_number):
        found.append((at + 1, "\n".join(by_number[at])))
    return found


def _needs_index(section):
    return section["has_hunks"] or section["has_binary"]


def _match_index(section, pre_ids, result_id):
    if section["pre_ids"] is None or section["result_id"] is None:
        raise ScanError("the patch and the file list disagree")
    if section["pre_ids"] != list(pre_ids) or section["result_id"] != result_id:
        raise ScanError("the patch and the file list disagree")


def _type_change_addition(record, sections):
    if len(sections) != 2:
        raise ScanError("the patch and the file list disagree")
    zero = "0" * len(record["ids"][-1])
    deletion = None
    addition = None
    for section in sections:
        if section["result_id"] == zero:
            if deletion is not None:
                raise ScanError("the patch and the file list disagree")
            deletion = section
        elif section["pre_ids"] == [zero]:
            if addition is not None:
                raise ScanError("the patch and the file list disagree")
            addition = section
        else:
            raise ScanError("the patch and the file list disagree")
    if deletion is None or addition is None:
        raise ScanError("the patch and the file list disagree")
    if deletion["added"]:
        raise ScanError("the patch cannot be read")
    if deletion["pre_ids"] != record["ids"][:-1]:
        raise ScanError("the patch and the file list disagree")
    if addition["result_id"] != record["ids"][-1]:
        raise ScanError("the patch and the file list disagree")
    return addition


def _by_class(record, section, work):
    data = _read_blob(record["ids"][-1])
    kind = classify_blob(data)
    if kind == "binary":
        return [], 1
    if kind == "text" and section is not None and section["has_hunks"]:
        return list(section["added"]), 0
    for pre in record["ids"][:-1]:
        if pre == record["ids"][-1]:
            return [], 0
    return line_diff_added(record, data, kind, work), 0


def _gitlink_lines(record, sections):
    """A mode ``160000`` result, before any blob read, for every status."""
    if record["status"] == "T":
        addition = _type_change_addition(record, sections)
        return list(addition["added"]), 0
    if len(sections) > 1:
        raise ScanError("the patch cannot be read")
    section = sections[0] if sections else None
    if section is not None and _needs_index(section):
        _match_index(section, record["ids"][:-1], record["ids"][-1])
    if section is None:
        return [], 0
    return list(section["added"]), 0


def _lines_for_record(record, sections, work):
    if record["modes"][-1] == "160000":
        return _gitlink_lines(record, sections)
    if record["status"] == "T":
        addition = _type_change_addition(record, sections)
        return _by_class(record, addition, work)
    if len(sections) > 1:
        raise ScanError("the patch cannot be read")
    section = sections[0] if sections else None
    result = record["ids"][-1]
    if _zero_id(result):
        if section is not None and _needs_index(section):
            _match_index(section, record["ids"][:-1], result)
        if section is not None and section["added"]:
            raise ScanError("the patch cannot be read")
        return [], 0
    if section is None:
        if len(record["ids"]) > 2:
            return [], 0
        raise ScanError("the patch and the file list disagree")
    if _needs_index(section):
        _match_index(section, record["ids"][:-1], result)
    return _by_class(record, section, work)


def _content_by_path(records, sections, work):
    grouped = {}
    known = set()
    for record in records:
        known.add(record["path"])
        grouped.setdefault(record["path"], [])
    for section in sections:
        if section["path"] not in known:
            raise ScanError("the patch and the file list disagree")
        grouped[section["path"]].append(section)
    lines_by_path = {}
    binary_count = 0
    for record in records:
        lines, binary = _lines_for_record(record, grouped[record["path"]], work)
        lines_by_path[record["path"]] = lines
        binary_count += binary
    return lines_by_path, binary_count


def scan_commit(full, names, cfg_name, cfg_email, empty_tree, hash_len, work):
    short = _checked_short(git_need("rev-parse", ["--short", "--end-of-options", full]))
    code, commit_text = git_text("cat-file", ["-p", "--end-of-options", full])
    if code != 0:
        raise ScanError("git cat-file failed (exit %d)" % code)
    author, committer, message = parse_commit(commit_text)
    show_options = [
        "--attr-source=" + empty_tree,
        "-c", "core.attributesFile=",
        "-c", "core.quotePath=true",
    ]
    code, status_raw = git(
        "show",
        ["-z", "--raw", "--no-abbrev", "-M", "--format=", "--no-ext-diff", "--no-textconv",
         "--no-color", "--no-relative",
         "--ignore-submodules=none", "--submodule=short",
         "--end-of-options", full],
        options=show_options,
    )
    if code != 0:
        raise ScanError("git show failed (exit %d)" % code)
    code, patch_raw = git(
        "show",
        ["--cc", "--full-index", "-M", "--format=", "--no-ext-diff", "--no-textconv",
         "--no-color", "--no-relative", "--src-prefix=a/", "--dst-prefix=b/",
         "--ignore-submodules=none", "--submodule=short",
         "--end-of-options", full],
        options=show_options,
    )
    if code != 0:
        raise ScanError("git show failed (exit %d)" % code)
    patch = patch_raw.decode("utf-8", "replace")
    records = parse_raw_records(status_raw, _parent_count(commit_text), hash_len)
    _found, named_paths, sections = added_lines(patch, hash_len)
    lines_by_path, binary_count = _content_by_path(records, sections, work)
    hits = []
    for kind in kinds_of(message, names):
        hits.append(hit_line(short, "message", kind))
    if not carries_identity(author[0], author[1], cfg_name, cfg_email):
        for kind in kinds_of_parts(author, names):
            hits.append(hit_line(short, "author", kind))
    if not carries_identity(committer[0], committer[1], cfg_name, cfg_email):
        for kind in kinds_of_parts(committer, names):
            hits.append(hit_line(short, "committer", kind))
    seen = set()
    for position, record in enumerate(records, start=1):
        status = record["status"]
        path = record["path"]
        seen.add(path)
        hidden = bool(kinds_of(path, names) or kinds_of(quote_path(path), names))
        if status[:1] in ("A", "R"):
            for kind in kinds_of(path, names):
                hits.append(hit_line(short, "file #%d" % position, kind))
        for number, content in lines_by_path.get(path, []):
            for kind in kinds_of(content, names):
                if hidden:
                    place = "line #%d:%d" % (position, number)
                else:
                    place = "line %s:%d" % (quote_path(path), number)
                hits.append(hit_line(short, place, kind))
    for path in named_paths:
        if path not in seen:
            raise ScanError("the patch and the file list disagree")
    return short, hits, binary_count


def default_base():
    code, out = git_text("symbolic-ref", ["--quiet", "refs/remotes/origin/HEAD"])
    if code != 0:
        raise ScanError('origin/HEAD is not set; name the base, e.g. origin/main')
    ref = out.strip()
    prefix = "refs/remotes/"
    if ref.startswith(prefix):
        return ref[len(prefix):]
    return ref


def ensure_repository():
    code, out = git_text("rev-parse", ["--is-inside-work-tree"])
    if code != 0 or out.strip() != "true":
        raise ScanError("not inside a git repository")


def ensure_commit(base):
    code, _out = git("rev-parse", ["--verify", "--quiet", "--end-of-options", base + "^{commit}"])
    if code != 0:
        raise ScanError("the base is not a commit here")


def execute(args):
    base = args.base
    if base is not None and base.startswith("-"):
        raise ScanError('the base must not begin with "-"')
    ensure_repository()
    if base is None:
        base = default_base()
    ensure_commit(base)
    ordered = deduped_names()
    public, cfg_name, cfg_email = public_names()
    names, notes = select_names(ordered, public)
    listed = git_need("rev-list", ["--reverse", "--end-of-options", base + "..HEAD"])
    commits = [line for line in listed.splitlines() if line]
    empty_tree, hash_len = repository_ids()
    hit_lines = []
    commits_hit = 0
    binary_total = 0
    work = [0]
    for full in commits:
        _short, hits, binary_count = scan_commit(full, names, cfg_name, cfg_email, empty_tree, hash_len, work)
        binary_total += binary_count
        if hits:
            commits_hit += 1
            hit_lines.extend(hits)
    for line in notes:
        say(line)
    for line in hit_lines:
        say(line)
    if binary_total:
        say("push-scan: note - %d binary file(s) not read" % binary_total)
    count = len(commits)
    if hit_lines:
        say("push-scan: FOUND - %d hit(s) in %d of %d commit(s)" % (len(hit_lines), commits_hit, count))
        return 1
    say("push-scan: OK - %d commit(s)" % count)
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        description="Read each commit of a range and report a path of this computer or an account name, by the place it was found, without printing the text.")
    parser.add_argument(
        "base", nargs="?",
        help="revision the range starts after; when omitted, the remote-tracking branch origin's HEAD names")
    return parser


def main():
    args = build_parser().parse_args()
    try:
        return execute(args)
    except ScanError as err:
        say("push-scan: CANNOT SCAN - " + err.reason)
        return 2
    except Exception:
        say("push-scan: CANNOT SCAN - internal error")
        return 2


if __name__ == "__main__":
    sys.exit(main())
