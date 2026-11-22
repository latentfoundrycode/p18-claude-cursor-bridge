"""TASK-075, the supervisor's acceptance tests (R-095): a signed-out Cursor tool is told from a failing model.

enforces: docs/REQUIREMENTS.md R-095; docs/BUILD_PLAN.md, TASK-075's Done when; docs/DESIGN.md, C3.

The Cursor command-line tool's own sign-in line is read from tests/fixtures/cursor/sign-in-required.txt, the line as
the tool printed it in the run that met it (ISS-020, 2026-10-30), no account name in it. Forms pinned:
- the probe, shape (a): the stand-in cursor-agent prints the line on standard error and exits 1;
- the probe, shape (b): the stand-in prints the line on standard output and exits 0;
- `--record-failure <model>` reading the line from `--stderr-file`, from `--stdout-file`, and from `--stderr-file`
  after a failure of the same model already counted inside the window (today that second failure marks the model);
- in each: one output line exactly `SIGN-IN  the Cursor command-line tool is signed out: run cursor-agent login`
  (two spaces after SIGN-IN), exit 5, the state file (<git common dir>/bridge/roster-state.json), the tracked
  docs/ROSTER.json and docs/ROSTER.resolved.json byte-identical before and after, no RESOLVED line, and no probe of
  the second profile (no output line naming its probe, no call of the stand-in with its models), where the roster's
  two profiles hold only native-pool models so that today the second profile is tried.
Guards, green on today's code as well: a model's reply holding the words "authentication required" inside a
sentence is answered as today (the profile resolves, exit 0, no SIGN-IN line), and an error file whose text is a
model's sentence holding those words mid-line is counted as today (exit 4 for a first failure, the failure written
to the state file, no SIGN-IN line). The tool's line is matched as the tool prints it, never by a model's words.

Not pinned: the wording of any line beyond the SIGN-IN line; whether the probe stops after the builder's probe or
after both of the first profile's probes; on which stream the SIGN-IN line is printed.

Isolation: every run of roster-check.py is a subprocess in a git repository under pytest's tmp_path, its HOME,
USERPROFILE, LOCALAPPDATA and APPDATA folders under tmp_path (the scratch home holds the `.cursor` folder the agent
home links to), and its cursor-agent a stand-in written under tmp_path and placed first on PATH (a cursor-agent.cmd
running this interpreter on Windows, an executable script elsewhere); PATH entries that hold another cursor-agent
are dropped, so the real tool is never run and nothing reaches the network. The stand-in accepts and ignores the
probe's arguments (-p -f --model <id> <prompt>) and logs each call. The state file is seeded before each run:
load_roster writes an absent one, which this increment does not change.
"""
import json
import os
import re
import stat
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "roster-check.py")
FIXTURE = os.path.join(HERE, "fixtures", "cursor", "sign-in-required.txt")
SIGN_IN = "SIGN-IN  the Cursor command-line tool is signed out: run cursor-agent login"

FIRST = ("composer-2.5", "grok-4.7-high")
SECOND = ("grok-4.6", "composer-1.5")
ROSTER = {
    "reset_day": 16,
    "review_a": "claude-opus-5-5",
    "profiles": [
        {"name": "native", "builder": FIRST[0], "review_b": FIRST[1]},
        {"name": "second", "builder": SECOND[0], "review_b": SECOND[1]},
    ],
}
SEED_STATE = {"other_pool": "available", "last_resolved": "2026-11-20T09:00 UTC"}
SEED_RESOLVED = {"profile": "native", "builder": FIRST[0], "review_a": "claude-opus-5-5", "review_b": FIRST[1],
                 "families": {"builder": "cursor", "review_a": "anthropic", "review_b": "xai"},
                 "other_pool": "available", "probed": True, "resolved_at": "2026-11-20T09:00 UTC", "reset_day": 16}
MODEL_SENTENCE = "OK - no authentication required here"
MODEL_ERROR_SENTENCE = "The model wrote: no authentication required here, so the step went on."


def sign_in_bytes():
    with open(FIXTURE, "rb") as f:
        data = f.read()
    data.decode("ascii")
    return data


def write_json(path, data):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def read_bytes(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return f.read()


def holds_cursor_agent(folder):
    return any(os.path.isfile(os.path.join(folder, n)) for n in ("cursor-agent", "cursor-agent.cmd", "cursor-agent.exe"))


class Workspace:
    def __init__(self, tmp_path):
        self.tmp = tmp_path
        home = tmp_path / "home"
        local = home / "AppData" / "Local"
        roaming = home / "AppData" / "Roaming"
        for d in (home / ".cursor", local, roaming):
            d.mkdir(parents=True, exist_ok=True)
        self.bin = tmp_path / "bin"
        self.bin.mkdir()
        self.calls = tmp_path / "calls.jsonl"
        env = {k: v for k, v in os.environ.items() if k != "ROSTER_NOW"}
        env["HOME"] = env["USERPROFILE"] = str(home)
        env["LOCALAPPDATA"] = str(local)
        env["APPDATA"] = str(roaming)
        rest = [p for p in env.get("PATH", "").split(os.pathsep) if p and not holds_cursor_agent(p)]
        env["PATH"] = os.pathsep.join([str(self.bin)] + rest)
        self.env = env
        self.repo = tmp_path / "Workspace"
        (self.repo / "docs").mkdir(parents=True)
        self.roster = self.repo / "docs" / "ROSTER.json"
        self.resolved = self.repo / "docs" / "ROSTER.resolved.json"
        write_json(self.roster, ROSTER)
        write_json(self.resolved, SEED_RESOLVED)
        self.git("init", "-q", "-b", "task-1")
        self.git("add", "-A")
        self.git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "checkpoint")
        self.state = self.repo / ".git" / "bridge" / "roster-state.json"
        self.seed_state(SEED_STATE)

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.repo)] + list(args), check=True, capture_output=True, env=self.env)

    def seed_state(self, data):
        self.state.parent.mkdir(parents=True, exist_ok=True)
        write_json(self.state, data)

    def stand_in(self, stdout=b"", stderr=b"", code=0):
        """A cursor-agent that logs its arguments, prints the given bytes and exits with `code`."""
        script = self.tmp / "cursor_agent_stand_in.py"
        script.write_text(
            "import json, sys\n"
            "with open(%r, 'a', encoding='utf-8') as f:\n"
            "    f.write(json.dumps(sys.argv[1:]) + '\\n')\n"
            "sys.stdout.buffer.write(%r); sys.stdout.flush()\n"
            "sys.stderr.buffer.write(%r); sys.stderr.flush()\n"
            "sys.exit(%d)\n" % (str(self.calls), stdout, stderr, code), encoding="ascii")
        if sys.platform == "win32":
            cmd = self.bin / "cursor-agent.cmd"
            cmd.write_bytes(('@echo off\r\n"%s" "%s" %%*\r\nexit /b %%ERRORLEVEL%%\r\n' % (sys.executable, script)).encode("ascii"))
        else:
            exe = self.bin / "cursor-agent"
            exe.write_text("#!%s\n" % sys.executable + script.read_text(encoding="ascii"), encoding="ascii")
            exe.chmod(exe.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    def run(self, *args, now=None):
        env = dict(self.env)
        if now:
            env["ROSTER_NOW"] = now
        p = subprocess.run([sys.executable, PROG, str(self.roster)] + list(args), capture_output=True, text=True,
                           env=env, cwd=str(self.repo), timeout=300)
        return p.returncode, p.stdout + p.stderr

    def snapshot(self):
        return {"state": read_bytes(self.state), "roster": read_bytes(self.roster), "resolved": read_bytes(self.resolved)}

    def called_models(self):
        models = []
        if self.calls.is_file():
            for line in self.calls.read_text(encoding="utf-8").splitlines():
                argv = json.loads(line)
                if "--model" in argv and argv.index("--model") + 1 < len(argv):
                    models.append(argv[argv.index("--model") + 1])
        return models

    def error_file(self, name, data):
        f = self.tmp / name
        f.write_bytes(data)
        return str(f)


@pytest.fixture
def ws(tmp_path):
    return Workspace(tmp_path)


def lines_of(out):
    return [line.rstrip() for line in out.splitlines()]


def assert_signed_out(ws, rc, out, before):
    assert rc == 5, "a signed-out tool ends with exit 5: " + out
    assert SIGN_IN in lines_of(out), "the SIGN-IN line, exactly: " + out
    assert not any(line.lstrip().startswith("RESOLVED") for line in lines_of(out)), "no profile resolves: " + out
    after = ws.snapshot()
    assert after["state"] == before["state"], "no failure is written against a model or a pool: the state file is byte-identical"
    assert after["roster"] == before["roster"], "the tracked roster is unchanged"
    assert after["resolved"] == before["resolved"], "the resolved file is unchanged"


def assert_no_second_profile_probe(ws, out):
    for line in lines_of(out):
        if line.lstrip().startswith("probe"):
            assert not any(re.search(r"(?<![\w.-])%s(?![\w.-])" % re.escape(m), line) for m in SECOND), \
                "the second profile is never probed: " + out
    called = ws.called_models()
    assert called, "the probe ran the stand-in"
    assert not set(called) & set(SECOND), "the stand-in was called with the second profile's models: %r" % called


def test_r095_probe_sign_in_line_on_stderr_with_a_non_zero_exit(ws):
    ws.stand_in(stderr=sign_in_bytes(), code=1)
    before = ws.snapshot()
    rc, out = ws.run()
    assert_signed_out(ws, rc, out, before)
    assert_no_second_profile_probe(ws, out)


def test_r095_probe_sign_in_line_on_stdout_with_exit_0(ws):
    ws.stand_in(stdout=sign_in_bytes(), code=0)
    before = ws.snapshot()
    rc, out = ws.run()
    assert_signed_out(ws, rc, out, before)
    assert_no_second_profile_probe(ws, out)


def test_r095_record_failure_reads_the_sign_in_line_in_a_stderr_file(ws):
    err = ws.error_file("call.err", sign_in_bytes())
    before = ws.snapshot()
    rc, out = ws.run("--record-failure", FIRST[0], "--stderr-file", err)
    assert_signed_out(ws, rc, out, before)


def test_r095_record_failure_reads_the_sign_in_line_in_a_stdout_file(ws):
    out_file = ws.error_file("call.out", sign_in_bytes())
    before = ws.snapshot()
    rc, out = ws.run("--record-failure", FIRST[0], "--stdout-file", out_file)
    assert_signed_out(ws, rc, out, before)


def test_r095_record_failure_after_a_counted_failure_marks_nothing(ws):
    """Today a second failure of the model inside the window marks it unavailable (exit 3); the sign-in line
    is not the model's failure, so nothing is counted or marked."""
    ws.seed_state(dict(SEED_STATE, failures={FIRST[0]: {"count": 1, "last": "2026-11-22T10:00 UTC"}}))
    err = ws.error_file("call.err", sign_in_bytes())
    before = ws.snapshot()
    rc, out = ws.run("--record-failure", FIRST[0], "--stderr-file", err, now="2026-11-22T10:30")
    assert_signed_out(ws, rc, out, before)


def test_r095_a_model_reply_holding_the_words_is_answered_as_today(ws):
    """Guard: the words inside a model's sentence are not the tool's line."""
    ws.stand_in(stdout=(MODEL_SENTENCE + "\n").encode("ascii"), code=0)
    rc, out = ws.run()
    assert rc == 0 and "RESOLVED profile 'native'" in out, out
    assert not any(line.lstrip().startswith("SIGN-IN") for line in lines_of(out)), out


def test_r095_a_model_sentence_in_an_error_file_is_counted_as_today(ws):
    """Guard: an error file whose text is a model's sentence holding the words mid-line is a first failure."""
    err = ws.error_file("call.err", (MODEL_ERROR_SENTENCE + "\n").encode("ascii"))
    before = ws.snapshot()
    rc, out = ws.run("--record-failure", FIRST[0], "--stderr-file", err)
    assert rc == 4, "a first failure, counted as today: " + out
    assert not any(line.lstrip().startswith("SIGN-IN") for line in lines_of(out)), out
    after = ws.snapshot()
    assert after["state"] != before["state"], "the failure is written to the state file as today"
    state = json.loads(after["state"].decode("utf-8"))
    assert state.get("failures", {}).get(FIRST[0], {}).get("count") == 1, state


def test_r095_the_tools_whole_line_quoted_inside_a_model_sentence_is_counted_as_today(ws):
    """Guard: the tool's line is matched as a whole line as the tool prints it, so a model's sentence that quotes
    the whole of it after other words is a first failure, counted as today."""
    line = sign_in_bytes().decode("ascii").strip()
    err = ws.error_file("call.err", ("The tool said: " + line + " and stopped.\n").encode("ascii"))
    before = ws.snapshot()
    rc, out = ws.run("--record-failure", FIRST[0], "--stderr-file", err)
    assert rc == 4, "a first failure, counted as today: " + out
    assert not any(l.lstrip().startswith("SIGN-IN") for l in lines_of(out)), out
    assert ws.snapshot()["state"] != before["state"], "the failure is written to the state file as today"


# Round 2 (the reviews of round 1). On standard output the tool's line is the tool's only when it is the whole of the
# output: a signed-out tool runs no model, so it prints nothing else there, while a model's reply may quote the line on
# a line of its own. On standard error, and in --stderr-file, any whole line counts, since launcher lines such as
# bridge-run's may come before it. Lines are split at the line feed alone and trimmed of spaces, tabs, CR and LF
# alone, so no other separator starts a line. The probe reads the tool's output as UTF-8.

LAUNCHER_LINE = "bridge-run: slot taken 2026-11-22T05:27:40Z"
SEPARATORS = [chr(0x0b), chr(0x0c), chr(0x1c), chr(0x85), chr(0x2028)]


def tool_line():
    return sign_in_bytes().decode("ascii").strip()


def assert_counted_as_today(ws, rc, out, before):
    assert rc == 4, "a first failure, counted as today: " + out
    assert not any(l.lstrip().startswith("SIGN-IN") for l in lines_of(out)), out
    after = ws.snapshot()
    assert after["state"] != before["state"], "the failure is written to the state file as today"
    state = json.loads(after["state"].decode("utf-8"))
    assert state.get("failures", {}).get(FIRST[0], {}).get("count") == 1, state


def test_r095_r2_probe_a_reply_quoting_the_line_on_a_line_of_its_own_is_answered_as_today(ws):
    """A model's reply on standard output that puts the tool's line on a line of its own after its own words is
    answered off-script, as today: the profile resolves and no SIGN-IN line is printed."""
    ws.stand_in(stdout=("Sure. The tool would print:\n" + tool_line() + "\n").encode("ascii"), code=0)
    rc, out = ws.run()
    assert rc == 0 and "RESOLVED profile 'native'" in out, out
    assert not any(l.lstrip().startswith("SIGN-IN") for l in lines_of(out)), out


def test_r095_r2_record_failure_a_stdout_file_with_the_line_after_other_lines_is_counted_as_today(ws):
    out_file = ws.error_file("call.out", ("I will explain the error.\n" + tool_line() + "\n").encode("ascii"))
    before = ws.snapshot()
    rc, out = ws.run("--record-failure", FIRST[0], "--stdout-file", out_file)
    assert_counted_as_today(ws, rc, out, before)


def test_r095_r2_record_failure_a_stdout_file_quoting_the_line_beside_a_model_stderr_is_counted_as_today(ws):
    """The two files are read apart: a model's words on standard error do not make a quoted line on standard
    output the tool's."""
    err = ws.error_file("call.err", (MODEL_ERROR_SENTENCE + "\n").encode("ascii"))
    out_file = ws.error_file("call.out", ("Here is what it said:\n" + tool_line() + "\n").encode("ascii"))
    before = ws.snapshot()
    rc, out = ws.run("--record-failure", FIRST[0], "--stderr-file", err, "--stdout-file", out_file)
    assert_counted_as_today(ws, rc, out, before)


@pytest.mark.parametrize("sep", SEPARATORS, ids=["vt", "ff", "fs", "nel", "ls"])
def test_r095_r2_record_failure_a_separator_other_than_the_line_feed_starts_no_line(ws, sep):
    err = ws.error_file("call.err", ("note" + sep + tool_line() + "\n").encode("utf-8"))
    before = ws.snapshot()
    rc, out = ws.run("--record-failure", FIRST[0], "--stderr-file", err)
    assert_counted_as_today(ws, rc, out, before)


def test_r095_r2_probe_a_reply_beyond_ascii_is_read_as_utf8(ws):
    """A model's reply holding a character beyond ASCII (A with acute, bytes C3 81) is read as UTF-8 and answered
    off-script, never lost as no reply."""
    ws.stand_in(stdout=b"\xc3\x81\n", code=0)
    rc, out = ws.run()
    assert rc == 0 and "RESOLVED profile 'native'" in out, out
    assert "Traceback" not in out and "UnicodeDecodeError" not in out, out


def test_r095_r2_probe_a_reply_beyond_the_consoles_code_page_is_answered_and_printed_in_ascii(ws):
    """A reply holding a character outside the console's code page (an emoji, bytes F0 9F 98 80) is answered
    off-script and the program's own output stays ASCII, so reading the reply as UTF-8 never makes printing it fail."""
    ws.stand_in(stdout=b"\xf0\x9f\x98\x80\n", code=0)
    env = dict(ws.env)
    p = subprocess.run([sys.executable, PROG, str(ws.roster)], capture_output=True, env=env, cwd=str(ws.repo),
                       timeout=300)
    out = (p.stdout + p.stderr).decode("ascii", errors="replace")
    assert p.returncode == 0 and "RESOLVED profile 'native'" in out, out
    assert "Traceback" not in out, out
    p.stdout.decode("ascii")


def test_r095_r2_guard_a_stderr_file_with_a_launcher_line_first_is_signed_out(ws):
    """Guard: on standard error the tool's line counts as any whole line, CRLF endings included."""
    err = ws.error_file("call.err", (LAUNCHER_LINE + "\r\n" + tool_line() + "\r\n").encode("ascii"))
    before = ws.snapshot()
    rc, out = ws.run("--record-failure", FIRST[0], "--stderr-file", err)
    assert_signed_out(ws, rc, out, before)


def test_r095_r2_guard_a_stdout_file_of_the_line_alone_with_blank_lines_is_signed_out(ws):
    """Guard: on standard output the line alone counts, blank lines and CRLF endings around it included."""
    out_file = ws.error_file("call.out", ("\r\n" + tool_line() + "\r\n\r\n").encode("ascii"))
    before = ws.snapshot()
    rc, out = ws.run("--record-failure", FIRST[0], "--stdout-file", out_file)
    assert_signed_out(ws, rc, out, before)


def test_r095_r2_guard_the_line_on_stderr_beside_a_model_stdout_is_signed_out(ws):
    """Guard: the tool's line in the --stderr-file is the tool's whatever the --stdout-file holds."""
    err = ws.error_file("call.err", sign_in_bytes())
    out_file = ws.error_file("call.out", (MODEL_ERROR_SENTENCE + "\n").encode("ascii"))
    before = ws.snapshot()
    rc, out = ws.run("--record-failure", FIRST[0], "--stderr-file", err, "--stdout-file", out_file)
    assert_signed_out(ws, rc, out, before)


def test_r095_r2_guard_the_probe_line_alone_on_stdout_with_blank_lines_is_signed_out(ws):
    ws.stand_in(stdout=("\r\n" + tool_line() + "\r\n").encode("ascii"), code=0)
    before = ws.snapshot()
    rc, out = ws.run()
    assert_signed_out(ws, rc, out, before)
    assert_no_second_profile_probe(ws, out)
