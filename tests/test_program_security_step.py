"""TASK-077's acceptance tests, the supervisor's (R-097; D-004): `evaluate-reports.py security`, the Sunday evaluation's
security step as a program, and the per-computer projects file `~/.cursor-bridge/projects.json` it and `pace-report.py` read.
enforces: docs/DESIGN.md, Change: the program release, C13, and "The weekly dependency scan" (the three kinds and green);
bridge/commands/evaluate-reports.md, step 1b; docs/diagrams/D-004-context-dfd.md, the flows from the evaluation to GitHub
(GET only) and to security.md beside the Workspace; docs/BUILD_PLAN.md, TASK-077, Done when. The builder reads and runs these
tests and never edits them.

How each case runs. Each builds its own scratch bridge root (a folder holding Reports/ and Workspace/, which bridge_root finds
from the working folder), its own home (HOME and USERPROFILE point there, so `~/.cursor-bridge/projects.json` is the case's),
its own project roots, each with a Workspace git checkout whose `origin` names github.com/OWNER/REPO (https or ssh form), and
its own ledger. The program is loaded from bridge/cursor-bridge/evaluate-reports.py and its `main()` run with
`security --date 2026-11-22 [...]`, the working folder inside the scratch bridge root. Every GitHub read goes through
`bridge_env.GH_COMMAND` (the seam of every GitHub reader of the bridge since TASK-064), which the case points at a stand-in:
the stand-in records each call's arguments, answers a path by the longest route that is a substring of it (so per_page,
page, created and state queries and `--paginate` do not change the route) from tests/fixtures/github/security-*.json, and
answers an unrouted path as GitHub's 404. The stand-in applies no `--jq` or `--template` (the program parses the reply), and
answers `--include` with a status line. PATH holds no real gh and no token is in the environment, so no case reaches GitHub.

Fixtures: captured 2026-11-22 from this repository by the supervisor with gh 2.97.0 by `gh api` GET (the workflows list,
the runs of dependency-scan.yml created on or after 2026-11-08, the jobs of run 43721483811, the OSV-Scanner step's lines of
that success run's log with its escape bytes, the vulnerability-alerts 204 and the empty open-alerts list), and built from
those by the fields each header names (a failed run, its job and its logs for exit 1 and exit 128, a cancelled run, a run in
progress, no run, the workflow disabled or absent, the alerts off, one open alert, a 403).

Pinned: the command and its options (`security`, `--date`, `--seed-from`, the last named in the docstring); the projects
file's place and form (an absent or malformed file named and refused with exit 2, nothing written, no read made); no
drive-letter path in the program's code or strings; a project's repository read from its Workspace's origin remote, `no remote`
and no read without one; every read a `gh api` GET with no field and no other method, the five reads by their paths; one
section per project in Reports/Evaluations/<date>/security.md headed by the project's name, its kind in the words `finding`
(with a `DEP-` increment as its remedy), `scanner failure` (with `gh workflow run dependency-scan.yml --repo OWNER/REPO`),
`no completed run` (with `gh workflow enable dependency-scan.yml` where the workflow is disabled, the rerun command where no
run is listed), `not configured`, `no remote` or `green`, matched case-insensitively; the word `green` never in the section of
a project that is not green; `alerts off` on a 404 with the second call not made, each open alert by its number and package,
none open said so; a failed read (a 403 or gh exiting non-zero) a finding in the project's section with the login's scope as
its remedy (the Security tab for an alerts read), never an empty section, never green, no token copied; from a job log only
the exit line `dependency-scan: OSV-Scanner exit <digits>` (the log's other text and its escape bytes never in the file, the
file ASCII with no control character but line feed and carriage return); the window in the ledger's
`_meta.security.<project>` (`last_run_read`, the createdAt of the newest completed run read, `none` or null before any;
`finding_standing`, a run id or null), runs created no later than `last_run_read` left out, a finding carried until a later
run ends success, the ledger untouched when security.md cannot be written, its other keys kept; `--seed-from` seeding the
window from a hand-written section's table by the backticked owner/repo; `pace-report.py` with no roots reading the same file.

Not pinned: the section's wording beyond the kind words, the alert's number and package and the remedy commands; the heading
level and the order of sections; the time limit's value (the program's reads stand under one, windowless, as bridge_env's
do); the exit code of a run that writes its file (0 is pinned only where every project is green); whether a success run's
jobs are listed; the date the runs query carries; whether a run's exit line itself is quoted in the file."""
import ast
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tokenize

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
BRIDGE = os.path.normpath(os.path.join(HERE, os.pardir, "bridge", "cursor-bridge"))
PROG = os.path.join(BRIDGE, "evaluate-reports.py")
PACE = os.path.join(BRIDGE, "pace-report.py")
FIXTURES = os.path.join(HERE, "fixtures", "github")
DATE = "2026-11-22"
NEW_RUN = "43721483811"                 # the captured run of 2026-11-15
NEW_RUN_AT = "2026-11-15T13:54:53Z"
OLD_RUN = "42484637835"                 # the captured run of 2026-11-08
OLD_RUN_AT = "2026-11-08T13:22:14Z"
JOB = "132834224595"
SENTINEL = "SENTINEL-T077-LOG-TEXT"
FAKE_TOKEN = "ghp_T077FakeTokenNeverCopied0123456789abcd"
RERUN = "gh workflow run dependency-scan.yml --repo OWNER/REPO"
ENABLE = "gh workflow enable dependency-scan.yml"
DRIVE_RX = re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/]")
# The basenames of the four project paths the program held before TASK-077 (none of them may be read any more).
OLD_PROJECT_DIRS = ("ck04k02s01-reangle-prototype", "p19-technical-documentation-provider",
                    "pk02k02s02-short-form-video-factory")

STANDIN = r'''
import json, os, sys
config = json.load(open(sys.argv[1], encoding="utf-8"))
args = sys.argv[2:]
with open(config["log"], "a", encoding="utf-8") as fh:
    fh.write(json.dumps(args) + "\n")
def refuse(why):
    sys.stderr.write("standin gh: refused - " + why + "\n")
    sys.exit(99)
if not args or args[0] != "api":
    refuse("not gh api: %r" % (args,))
path, include = None, False
i = 1
while i < len(args):
    a = args[i]
    if a in ("-X", "--method"):
        if i + 1 >= len(args) or args[i + 1].upper() != "GET":
            refuse("not a GET: %r" % (args,))
        i += 2
        continue
    if a.startswith("--method=") or (a.startswith("-X") and len(a) > 2):
        value = a.split("=", 1)[1] if a.startswith("--method=") else a[2:]
        if value.upper() != "GET":
            refuse("not a GET: %r" % (args,))
        i += 1
        continue
    if a in ("-f", "-F", "--field", "--raw-field", "--input") or a.startswith(("--field=", "--raw-field=", "--input=")) \
            or (a[:2] in ("-f", "-F") and len(a) > 2):
        refuse("a field or an input is no plain GET: %r" % (args,))
    if a in ("-q", "--jq", "-t", "--template") or a.startswith(("--jq=", "--template=")):
        refuse("the stand-in applies no --jq or --template; the program parses the reply")
    if a in ("-i", "--include"):
        include = True
        i += 1
        continue
    if a in ("-H", "--header", "--hostname", "--cache", "-p", "--preview"):
        i += 2
        continue
    if not a.startswith("-") and path is None:
        path = a
    i += 1
if path is None:
    refuse("no path: %r" % (args,))
path = path.lstrip("/")
hits = sorted((k for k in config["routes"] if k in path), key=len, reverse=True)
name = config["routes"][hits[0]] if hits else None
def emit(status, reason, body):
    if include:
        sys.stdout.buffer.write(("HTTP/2.0 %d %s\r\n\r\n" % (status, reason)).encode("ascii"))
    if body is None or body == "":
        return
    data = body if isinstance(body, str) else json.dumps(body)
    sys.stdout.buffer.write(data.encode("utf-8"))
if name is None:
    emit(404, "Not Found", {"message": "Not Found", "status": "404"})
    sys.stderr.write("gh: Not Found (HTTP 404)\n")
    sys.exit(1)
if name == "!crash":
    sys.stderr.write("error connecting to api.github.com (token %s)\n" % config["token"])
    sys.exit(1)
doc = json.load(open(os.path.join(config["fixtures"], name), encoding="utf-8"))
emit(doc["status"], {200: "OK", 204: "No Content", 403: "Forbidden", 404: "Not Found"}.get(doc["status"], ""), doc["body"])
sys.stdout.flush()
if doc["gh_stderr"]:
    sys.stderr.write(doc["gh_stderr"] + "\n")
sys.exit(doc["gh_exit"])
'''


def fixture(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as fh:
        return json.load(fh)


def routes(repo="OWNER/REPO", workflows="security-workflows.json", runs="security-runs.json", jobs="security-jobs.json",
           log="security-log-success.json", vuln="security-vulnerability-alerts-on.json", alerts="security-alerts-none.json"):
    """One repository's routes; a value of None leaves that read unanswered (GitHub's 404); "!crash" makes gh exit 1."""
    r = {
        "repos/%s/actions/workflows" % repo: workflows,
        "repos/%s/actions/workflows/dependency-scan.yml/runs" % repo: runs,
        "repos/%s/actions/runs/%s/jobs" % (repo, NEW_RUN): jobs,
        "repos/%s/actions/jobs/%s/logs" % (repo, JOB): log,
        "repos/%s/vulnerability-alerts" % repo: vuln,
        "repos/%s/dependabot/alerts" % repo: alerts,
    }
    return {k: v for k, v in r.items() if v}


def path_of(call):
    """The API path of one recorded call (the first argument after `api` that is no option or option value)."""
    skip = False
    for a in call[1:]:
        if skip:
            skip = False
            continue
        if a in ("-X", "--method", "-H", "--header", "--hostname", "--cache", "-p", "--preview", "-q", "--jq", "-t", "--template"):
            skip = True
            continue
        if a.startswith("-"):
            continue
        return a.lstrip("/")
    return ""


def no_gh_path():
    """PATH without any folder that holds a gh, so a read that bypasses the stand-in cannot reach GitHub."""
    keep = []
    for d in os.environ.get("PATH", "").split(os.pathsep):
        if not d:
            continue
        if any(os.path.exists(os.path.join(d, n)) for n in ("gh", "gh.exe", "gh.cmd", "gh.bat")):
            continue
        keep.append(d)
    return os.pathsep.join(keep)


def heading_sections(text):
    """[(heading line, level, body lines)] of a markdown file."""
    out = []
    for line in text.splitlines():
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            out.append([line, len(m.group(1)), []])
        elif out:
            out[-1][2].append(line)
    return out


class Bench:
    """One case's scratch world: the bridge root, the home, the projects, the ledger and the stand-in."""

    def __init__(self, tmp_path, monkeypatch, capsys):
        self.tmp, self.mp, self.capsys = tmp_path, monkeypatch, capsys
        self.root = tmp_path / "bridge"
        (self.root / "Reports").mkdir(parents=True)
        (self.root / "Workspace").mkdir()
        self.home = tmp_path / "home"
        self.home.mkdir()
        self.projects_file = self.home / ".cursor-bridge" / "projects.json"
        monkeypatch.setenv("HOME", str(self.home))
        monkeypatch.setenv("USERPROFILE", str(self.home))
        for name in ("GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN", "GH_HOST"):
            monkeypatch.delenv(name, raising=False)
        (tmp_path / "gh-config-empty").mkdir()
        monkeypatch.setenv("GH_CONFIG_DIR", str(tmp_path / "gh-config-empty"))
        monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
        monkeypatch.setenv("PATH", no_gh_path())
        assert shutil.which("git"), "test setup: git must stay on PATH once the folders holding gh are left out"
        assert not shutil.which("gh"), "test setup: a real gh is still on PATH"
        self.log = tmp_path / "gh-calls.jsonl"
        self.standin = tmp_path / "standin_security_gh.py"
        self.standin.write_text(STANDIN, encoding="utf-8")
        self.mod = None

    # ---- the world
    def project(self, name, origin="https://github.com/OWNER/REPO.git"):
        """A project root with a Workspace git checkout whose origin is `origin` (None: no remote)."""
        root = self.tmp / "projects" / (re.sub(r"[^a-z0-9]+", "-", name.lower()) + "-root")
        ws = root / "Workspace"
        ws.mkdir(parents=True)
        self.git(ws, "init", "-q")
        if origin:
            self.git(ws, "remote", "add", "origin", origin)
        return root

    def git(self, cwd, *args):
        p = subprocess.run(["git"] + list(args), cwd=str(cwd), capture_output=True, text=True)
        assert p.returncode == 0, "test setup: git %s failed: %s" % (" ".join(args), p.stderr)

    def write_projects(self, mapping=None, raw=None):
        self.projects_file.parent.mkdir(parents=True, exist_ok=True)
        text = raw if raw is not None else json.dumps({k: str(v) for k, v in mapping.items()})
        self.projects_file.write_text(text, encoding="utf-8")

    def write_ledger(self, security=None, extra=None):
        data = {"_meta": {"last_extract": "2026-11-15", "last_collect": "2026-11-15"}}
        if security is not None:
            data["_meta"]["security"] = security
        data.update(extra or {})
        self.ledger_path.write_text(json.dumps(data, indent=1, sort_keys=True), encoding="utf-8")
        return self.ledger_path.read_bytes()

    @property
    def ledger_path(self):
        return self.root / "Reports" / "ledger.json"

    def ledger(self):
        return json.loads(self.ledger_path.read_text(encoding="utf-8"))

    def window(self, name):
        sec = (self.ledger().get("_meta") or {}).get("security")
        assert isinstance(sec, dict), "the ledger's _meta holds no security object: %r" % self.ledger().get("_meta")
        assert name in sec, "the ledger's _meta.security holds no entry for %s: %r" % (name, sec)
        return sec[name]

    @property
    def out_dir(self):
        return self.root / "Reports" / "Evaluations" / DATE

    @property
    def security_md(self):
        return self.out_dir / "security.md"

    # ---- the run
    def load(self):
        self.mp.syspath_prepend(BRIDGE)
        spec = importlib.util.spec_from_file_location("evaluate_reports_t077", PROG)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.mod = mod
        return mod

    def run(self, route_map=None, *extra):
        """Run `evaluate-reports.py security --date DATE <extra>`; returns (exit code, everything printed)."""
        mod = self.load()
        cfg = self.tmp / "standin-routes.json"
        cfg.write_text(json.dumps({"routes": route_map or {}, "fixtures": FIXTURES, "log": str(self.log),
                                   "token": FAKE_TOKEN}), encoding="utf-8")
        if self.log.exists():
            self.log.unlink()
        self.mp.setattr(mod.bridge_env, "GH_COMMAND", [sys.executable, str(self.standin), str(cfg)])
        self.mp.chdir(str(self.root / "Workspace"))
        self.mp.setattr(sys, "argv", ["evaluate-reports.py", "security", "--date", DATE] + list(extra))
        self.capsys.readouterr()
        try:
            rc = mod.main()
        except SystemExit as e:
            rc = e.code
        got = self.capsys.readouterr()
        return rc, got.out + got.err

    def calls(self):
        if not self.log.exists():
            return []
        return [json.loads(l) for l in self.log.read_text(encoding="utf-8").splitlines() if l.strip()]

    def paths(self):
        return [path_of(c) for c in self.calls()]

    def report(self, out=""):
        assert self.security_md.is_file(), "security.md was not written at %s; the program printed:\n%s" % (self.security_md, out)
        return self.security_md.read_text(encoding="utf-8")

    def section(self, name, out=""):
        """The section headed by the project's name: from its heading to the next heading of its level or higher."""
        text = self.report(out)
        secs = heading_sections(text)
        hits = [i for i, s in enumerate(secs) if re.search(r"\b%s\b" % re.escape(name), s[0])]
        assert len(hits) == 1, "security.md must hold exactly one heading naming %s; it holds %d:\n%s" % (name, len(hits), text)
        i = hits[0]
        level = secs[i][1]
        body = list(secs[i][2])
        for s in secs[i + 1:]:
            if s[1] <= level:
                break
            body += [s[0]] + s[2]
        sec = "\n".join([secs[i][0]] + body)
        assert any(l.strip() for l in body), "the section of %s is empty (never an empty section):\n%s" % (name, text)
        return sec


@pytest.fixture
def bench(tmp_path, monkeypatch, capsys):
    return Bench(tmp_path, monkeypatch, capsys)


def one_project(bench, name="Alpha", origin="https://github.com/OWNER/REPO.git", last_run_read=OLD_RUN_AT, finding=None):
    """The usual world: one project, its window starting after the run of 2026-11-08; returns the ledger's bytes."""
    root = bench.project(name, origin)
    bench.write_projects({name: root})
    return bench.write_ledger({name: {"last_run_read": last_run_read, "finding_standing": finding}})


def has(word, text):
    return re.search(word, text, re.I) is not None


def assert_get_only(bench):
    calls = bench.calls()
    for c in calls:
        assert c and c[0] == "api", "a gh call that is not gh api: %r" % (c,)
        for i, a in enumerate(c):
            if a in ("-X", "--method"):
                assert i + 1 < len(c) and c[i + 1].upper() == "GET", "a request other than GET: %r" % (c,)
            if a.startswith("--method=") or (a.startswith("-X") and len(a) > 2):
                assert a.upper().endswith("GET"), "a request other than GET: %r" % (c,)
            assert a not in ("-f", "-F", "--field", "--raw-field", "--input"), "a field or an input on a read: %r" % (c,)
            assert not a.startswith(("--field=", "--raw-field=", "--input=")), "a field or an input on a read: %r" % (c,)
            assert not (a[:2] in ("-f", "-F") and len(a) > 2), "a field on a read: %r" % (c,)


def assert_clean_file(bench, out=""):
    """ASCII, no control character but LF (and CR), no log text, no escape byte, no token."""
    data = bench.security_md.read_bytes() if bench.security_md.is_file() else None
    assert data is not None, "security.md was not written; the program printed:\n%s" % out
    bad = sorted(set(b for b in data if b >= 128 or (b < 32 and b not in (10, 13)) or b == 127))
    assert not bad, "security.md holds non-ASCII or control bytes %r" % bad
    text = data.decode("ascii")
    assert SENTINEL not in text, "log text beyond the exit line entered security.md:\n%s" % text
    assert FAKE_TOKEN not in text and "ghp_" not in text, "a token entered security.md"


# ---------------------------------------------------------------- the fixtures


def test_r097_every_security_fixture_says_how_it_was_made_and_holds_no_account():
    """The recorded replies: each captured or built, the header saying from what, the request with OWNER/REPO, no token,
    no account name, no path of this computer."""
    names = sorted(n for n in os.listdir(FIXTURES) if n.startswith("security-") and n.endswith(".json"))
    want = {"security-workflows.json", "security-runs.json", "security-jobs.json", "security-log-success.json",
            "security-vulnerability-alerts-on.json", "security-alerts-none.json", "security-runs-failed.json",
            "security-jobs-failed.json", "security-log-finding.json", "security-log-exit128.json",
            "security-runs-cancelled.json", "security-runs-in-progress.json", "security-runs-none.json",
            "security-workflows-disabled.json", "security-workflows-absent.json", "security-vulnerability-alerts-off.json",
            "security-alerts-one.json", "security-forbidden.json"}
    assert want <= set(names), "fixtures missing: %s" % sorted(want - set(names))
    for n in names:
        doc = fixture(n)
        text = json.dumps(doc)
        assert set(doc) == {"fixture", "note", "request", "status", "gh_exit", "gh_stderr", "body"}, n
        assert doc["fixture"] in ("captured", "built"), n
        if doc["fixture"] == "captured":
            assert doc["note"].startswith("captured 2026-11-22 from this repository by the supervisor"), n
            assert "gh 2.97.0" in doc["note"] and "gh api GET" in doc["note"], n
        else:
            assert re.search(r"from the captured security-[\w-]+\.json", doc["note"]), n
        assert doc["request"].startswith("repos/OWNER/REPO/"), n
        assert "latentfoundrycode" not in text and "p18-claude-cursor-bridge" not in text, n
        assert not re.search(r"gh[pousr]_[A-Za-z0-9]{8,}|github_pat_", text), n
        assert not DRIVE_RX.search(text.replace("\\\\", "\\")), n
    assert "\x1b" in fixture("security-log-success.json")["body"], "the captured log keeps its escape bytes"
    assert "dependency-scan: OSV-Scanner exit $code" in fixture("security-log-success.json")["body"]
    assert not re.search(r"dependency-scan: OSV-Scanner exit \d", fixture("security-log-success.json")["body"]), \
        "a success run prints no exit line"


# ---------------------------------------------------------------- the program's source


def test_r097_the_program_holds_no_drive_letter_path():
    """The four project paths are gone: no string literal or code of evaluate-reports.py names a drive-letter path."""
    with open(PROG, "rb") as fh:
        toks = list(tokenize.tokenize(fh.readline))
    hits = [(t.start[0], t.string[:80]) for t in toks if t.type != tokenize.COMMENT and DRIVE_RX.search(t.string)]
    assert not hits, "evaluate-reports.py still names a drive-letter path (line, text): %r" % hits


def test_r097_the_docstring_names_the_command_and_the_seed_option():
    """The docstring names `security` and the option that seeds the window once, `--seed-from`."""
    with open(PROG, encoding="utf-8") as fh:
        doc = ast.get_docstring(ast.parse(fh.read())) or ""
    assert "evaluate-reports.py security" in doc, "the docstring names no `evaluate-reports.py security` command"
    assert "--seed-from" in doc, "the docstring does not name the --seed-from option"
    assert "projects.json" in doc, "the docstring does not name ~/.cursor-bridge/projects.json"


# ---------------------------------------------------------------- the projects file


def test_r097_an_absent_projects_file_is_named_and_stops_with_exit_2(bench):
    """No ~/.cursor-bridge/projects.json: one line naming the file and saying what it holds, exit 2, nothing written, no read."""
    before = bench.write_ledger({})
    rc, out = bench.run(routes())
    assert "projects.json" in out and ".cursor-bridge" in out, "the refusal does not name ~/.cursor-bridge/projects.json:\n%s" % out
    assert has(r"\bobject\b", out) and has(r"project name", out) and has(r"root", out), \
        "the refusal does not say the file holds a JSON object of project name to project root:\n%s" % out
    assert rc == 2, "exit %r, not 2:\n%s" % (rc, out)
    assert not bench.out_dir.exists(), "something was written under Reports/Evaluations/%s" % DATE
    assert bench.ledger_path.read_bytes() == before, "the ledger changed"
    assert bench.calls() == [], "a read was made: %r" % bench.calls()


MALFORMED = {
    "not JSON": ('{"Alpha": ', r"json"),
    "not an object": ('["Alpha"]', r"object"),
    "a value not a string": ('{"Alpha": 3}', r"string"),
    "an empty key": ('{"": "somewhere"}', r"empty"),
}


@pytest.mark.parametrize("case", sorted(MALFORMED))
def test_r097_a_malformed_projects_file_is_refused_with_its_reason(bench, case):
    """A projects file not JSON, not an object, with a value not a string or an empty key: refused with the reason, exit 2,
    nothing written, no read."""
    raw, reason = MALFORMED[case]
    bench.write_projects(raw=raw)
    before = bench.write_ledger({})
    rc, out = bench.run(routes())
    assert "projects.json" in out, "the refusal does not name the projects file:\n%s" % out
    assert has(reason, out), "the refusal of a file %s does not give its reason (%s):\n%s" % (case, reason, out)
    assert rc == 2, "exit %r, not 2:\n%s" % (rc, out)
    assert not bench.out_dir.exists(), "something was written under Reports/Evaluations/%s" % DATE
    assert bench.ledger_path.read_bytes() == before, "the ledger changed"
    assert bench.calls() == [], "a read was made: %r" % bench.calls()


def test_r097_collect_reads_its_projects_from_the_same_file(bench):
    """Guard: `collect` reads the projects of ~/.cursor-bridge/projects.json, not a list held in the program."""
    root = bench.project("Alpha")
    docs = root / "Documents"
    docs.mkdir()
    (docs / "Alpha Issues During Development and Their Solutions.md").write_text(
        "# Alpha - Issues During Development and Their Solutions\n\n## ISS-001 - The first issue\nContext: the first.\n",
        encoding="utf-8")
    bench.write_projects({"Alpha": root})
    bench.write_ledger({})
    mod = bench.load()
    bench.mp.chdir(str(bench.root / "Workspace"))
    bench.mp.setattr(sys, "argv", ["evaluate-reports.py", "collect"])
    bench.capsys.readouterr()
    try:
        rc = mod.main()
    except SystemExit as e:
        rc = e.code
    got = bench.capsys.readouterr()
    out = got.out + got.err
    assert "Alpha issues: 1 entries" in out, "collect did not read the project the projects file names:\n%s" % out
    for old in ("reAngle", "Video Factory", "TDP issues"):
        assert old not in out, "collect still read a project the program held (%s):\n%s" % (old, out)
    assert rc == 0, out


# ---------------------------------------------------------------- the reads


@pytest.mark.parametrize("origin", ["https://github.com/OWNER/REPO.git", "git@github.com:OWNER/REPO.git"])
def test_r097_green_reads_by_get_and_moves_the_window_after_the_write(bench, origin):
    """The window's last completed run success, no finding standing, the alerts on with none open: green; the five reads are
    gh api GETs of the paths named; the window moves to the run read, its finding null; other ledger keys kept."""
    root = bench.project("Alpha", origin)
    bench.write_projects({"Alpha": root})
    bench.write_ledger({"Alpha": {"last_run_read": OLD_RUN_AT, "finding_standing": None}},
                       extra={"Alpha/ISS-001": {"evaluated": "2026-11-15", "fingerprint": "abc", "outcome": "fixed", "reason": "x"}})
    rc, out = bench.run(routes())
    sec = bench.section("Alpha", out)
    assert has(r"\bgreen\b", sec), "the section does not say green:\n%s" % sec
    assert any(has(r"\balert", l) and (has(r"\b(no|none|nothing|0)\b[^\n]*\bopen\b", l) or has(r"\bopen\b[^\n]*\b(none|0)\b", l))
               for l in sec.splitlines()), "the section does not say no alert is open:\n%s" % sec
    assert rc == 0, "exit %r for an all-green run:\n%s" % (rc, out)
    assert_clean_file(bench, out)
    assert_get_only(bench)
    paths = bench.paths()
    assert any(p.startswith("repos/OWNER/REPO/actions/workflows") and "dependency-scan.yml/runs" not in p for p in paths), \
        "the workflows list was not read: %r" % paths
    runs = [p for p in paths if p.startswith("repos/OWNER/REPO/actions/workflows/dependency-scan.yml/runs")]
    assert runs, "the runs of dependency-scan.yml were not read: %r" % paths
    assert all("created=" in p and (">=" in p or "%3E%3D" in p.upper()) for p in runs), "the runs read carries no created>= query: %r" % runs
    vuln = [i for i, p in enumerate(paths) if p.startswith("repos/OWNER/REPO/vulnerability-alerts")]
    alerts = [i for i, p in enumerate(paths) if p.startswith("repos/OWNER/REPO/dependabot/alerts")]
    assert vuln and alerts and vuln[0] < alerts[0], "the alerts' two calls were not made in order: %r" % paths
    assert all("state=open" in paths[i] for i in alerts), "the alerts read is not of the open alerts: %r" % paths
    assert not any("/logs" in p for p in paths), "a success run's log was read: %r" % paths
    w = bench.window("Alpha")
    assert w.get("last_run_read") == NEW_RUN_AT, "the window did not move to the newest completed run read: %r" % w
    assert w.get("finding_standing") is None, "a finding stands after a green window: %r" % w
    led = bench.ledger()
    assert led.get("Alpha/ISS-001", {}).get("outcome") == "fixed", "the ledger's verdicts were not kept"
    assert led["_meta"].get("last_extract") == "2026-11-15", "the ledger's other _meta keys were not kept"


def test_r097_a_finding_names_a_dep_increment_and_only_the_exit_line_enters(bench):
    """A completed run of the window ended failure with exit 1: a finding, its remedy a DEP- increment; the finding stands in
    the ledger; the log's other text and escape bytes never enter the file."""
    one_project(bench)
    rc, out = bench.run(routes(runs="security-runs-failed.json", jobs="security-jobs-failed.json", log="security-log-finding.json"))
    sec = bench.section("Alpha", out)
    assert has(r"\bfinding\b", sec), "the section does not say finding:\n%s" % sec
    assert "DEP-" in sec, "the finding's remedy names no DEP- increment:\n%s" % sec
    assert not has(r"scanner failure", sec), "exit 1 read as a scanner failure (the script's own lines are no exit line):\n%s" % sec
    assert not has(r"\bgreen\b", sec), "a finding's section says green:\n%s" % sec
    assert_clean_file(bench, out)
    assert_get_only(bench)
    paths = bench.paths()
    assert any(p.startswith("repos/OWNER/REPO/actions/runs/%s/jobs" % NEW_RUN) for p in paths), "the failed run's jobs were not read: %r" % paths
    assert any(p.startswith("repos/OWNER/REPO/actions/jobs/%s/logs" % JOB) for p in paths), "the failed job's log was not read: %r" % paths
    w = bench.window("Alpha")
    assert str(w.get("finding_standing")) == NEW_RUN, "the finding does not stand in the ledger: %r" % w
    assert w.get("last_run_read") == NEW_RUN_AT, "the window did not move: %r" % w


SCANNER_FAILURES = {
    "a failure with exit 128": dict(runs="security-runs-failed.json", jobs="security-jobs-failed.json", log="security-log-exit128.json"),
    "a failure with no exit line": dict(runs="security-runs-failed.json", jobs="security-jobs-failed.json", log="security-log-success.json"),
    "a cancelled run": dict(runs="security-runs-cancelled.json"),
}


@pytest.mark.parametrize("case", sorted(SCANNER_FAILURES))
def test_r097_a_scanner_failure_names_the_rerun(bench, case):
    """The window's last completed run proved nothing (another exit code, no exit line, a conclusion other than success and
    failure): a scanner failure with the rerun's one command; no DEP- increment, not green."""
    one_project(bench)
    rc, out = bench.run(routes(**SCANNER_FAILURES[case]))
    sec = bench.section("Alpha", out)
    assert has(r"scanner failure", sec), "%s is not reported as a scanner failure:\n%s" % (case, sec)
    assert RERUN in sec, "the scanner failure's remedy is not `%s`:\n%s" % (RERUN, sec)
    assert "DEP-" not in sec, "a scanner failure reported with a DEP- increment:\n%s" % sec
    assert not has(r"\bgreen\b", sec), "a scanner failure's section says green:\n%s" % sec
    assert_clean_file(bench, out)
    assert_get_only(bench)
    w = bench.window("Alpha")
    assert w.get("finding_standing") is None, "a scanner failure stood as a finding: %r" % w
    assert w.get("last_run_read") == NEW_RUN_AT, "the window did not move to the completed run read: %r" % w


NO_COMPLETED = {
    "the workflow disabled": (dict(workflows="security-workflows-disabled.json"), ENABLE),
    "no run listed": (dict(runs="security-runs-none.json"), RERUN),
    "only a run in progress": (dict(runs="security-runs-in-progress.json"), None),
}


@pytest.mark.parametrize("case", sorted(NO_COMPLETED))
def test_r097_no_completed_run_is_a_finding_of_its_own_with_its_remedy(bench, case):
    """The workflow disabled (whatever its runs show), no run listed, or only runs in progress: no completed run, never green,
    with its remedy; the window keeps its start where no run completed."""
    kw, remedy = NO_COMPLETED[case]
    one_project(bench)
    rc, out = bench.run(routes(**kw))
    sec = bench.section("Alpha", out)
    assert has(r"no completed run", sec), "%s is not reported as no completed run:\n%s" % (case, sec)
    assert not has(r"\bgreen\b", sec), "%s reported green (silence is not green):\n%s" % (case, sec)
    if remedy:
        assert remedy in sec, "the remedy `%s` is not in the section:\n%s" % (remedy, sec)
    assert_clean_file(bench, out)
    assert_get_only(bench)
    if case != "the workflow disabled":
        w = bench.window("Alpha")
        assert w.get("last_run_read") == OLD_RUN_AT, "the window moved though no run of it completed: %r" % w


def test_r097_a_project_without_the_workflow_is_not_configured(bench):
    """No dependency-scan workflow listed: not configured, and no run is read."""
    one_project(bench)
    rc, out = bench.run(routes(workflows="security-workflows-absent.json"))
    sec = bench.section("Alpha", out)
    assert has(r"not configured", sec), "the section does not say not configured:\n%s" % sec
    assert not has(r"\bgreen\b", sec), "a project without the workflow reported green:\n%s" % sec
    assert_get_only(bench)
    assert not any("/runs" in p for p in bench.paths()), "a run was read for a project without the workflow: %r" % bench.paths()


def test_r097_a_project_without_a_remote_is_written_no_remote_and_nothing_is_read(bench):
    """A Workspace with no origin remote: no remote, and no call is made for it."""
    one_project(bench, origin=None)
    rc, out = bench.run(routes())
    sec = bench.section("Alpha", out)
    assert has(r"no remote", sec), "the section does not say no remote:\n%s" % sec
    assert not has(r"\bgreen\b", sec), "a project without a remote reported green:\n%s" % sec
    assert bench.calls() == [], "a read was made for a project with no remote: %r" % bench.calls()


# ---------------------------------------------------------------- the alerts


def test_r097_alerts_off_on_a_404_and_the_second_call_not_made(bench):
    """vulnerability-alerts answers 404: alerts off, and the open alerts are not listed."""
    one_project(bench)
    rc, out = bench.run(routes(vuln="security-vulnerability-alerts-off.json"))
    sec = bench.section("Alpha", out)
    assert has(r"alerts off", sec), "the section does not say alerts off:\n%s" % sec
    assert_get_only(bench)
    paths = bench.paths()
    assert any(p.startswith("repos/OWNER/REPO/vulnerability-alerts") for p in paths), "the first alerts call was not made: %r" % paths
    assert not any("dependabot/alerts" in p for p in paths), "the open alerts were listed after a 404: %r" % paths


def test_r097_an_open_alert_is_named_by_its_number_and_package(bench):
    """One open alert: the section names it by its number and its package."""
    one_project(bench)
    rc, out = bench.run(routes(alerts="security-alerts-one.json"))
    sec = bench.section("Alpha", out)
    assert re.search(r"(?<!\d)41(?!\d)", sec), "the open alert's number (41) is not in the section:\n%s" % sec
    assert "requests" in sec, "the open alert's package (requests) is not in the section:\n%s" % sec
    assert_clean_file(bench, out)
    assert_get_only(bench)


# ---------------------------------------------------------------- a read that fails


FAILED_READS = {
    "the workflows list refused (403)": ("repos/OWNER/REPO/actions/workflows", "security-forbidden.json", False),
    "the runs list refused (403)": ("repos/OWNER/REPO/actions/workflows/dependency-scan.yml/runs", "security-forbidden.json", False),
    "the alerts' first call refused (403)": ("repos/OWNER/REPO/vulnerability-alerts", "security-forbidden.json", True),
    "the open alerts refused (403)": ("repos/OWNER/REPO/dependabot/alerts", "security-forbidden.json", True),
    "gh exiting non-zero on the workflows list": ("repos/OWNER/REPO/actions/workflows", "!crash", False),
    "gh exiting non-zero on the open alerts": ("repos/OWNER/REPO/dependabot/alerts", "!crash", True),
}


@pytest.mark.parametrize("case", sorted(FAILED_READS))
def test_r097_a_failed_read_is_a_finding_with_its_remedy_never_green(bench, case):
    """A read refused or failed: a finding in the project's section with the login's scope as its remedy (the Security tab
    for an alerts read), never an empty section, never green, no token copied."""
    route, answer, alerts = FAILED_READS[case]
    one_project(bench)
    r = routes()
    r[route] = answer
    rc, out = bench.run(r)
    sec = bench.section("Alpha", out)
    assert has(r"\bfinding\b", sec), "%s is not a finding in the section:\n%s" % (case, sec)
    assert has(r"\bscope\b", sec), "%s: the remedy does not name the login's scope:\n%s" % (case, sec)
    if alerts:
        assert has(r"security tab", sec), "%s: the remedy does not name the repository's Security tab:\n%s" % (case, sec)
    assert not has(r"\bgreen\b", sec), "%s reported green:\n%s" % (case, sec)
    assert FAKE_TOKEN not in out, "a token was printed"
    assert_clean_file(bench, out)
    assert_get_only(bench)


# ---------------------------------------------------------------- the window


def test_r097_runs_read_before_are_left_out_of_the_window(bench):
    """last_run_read at the newest listed run: both listed runs are older or equal, so the window holds none."""
    one_project(bench, last_run_read=NEW_RUN_AT)
    rc, out = bench.run(routes())
    sec = bench.section("Alpha", out)
    assert has(r"no completed run", sec), "runs read before were read again:\n%s" % sec
    assert RERUN in sec, "no run in the window and no rerun command:\n%s" % sec
    assert bench.window("Alpha").get("last_run_read") == NEW_RUN_AT


def test_r097_a_finding_stands_until_a_later_run_ends_success(bench):
    """A finding standing and no completed run in the window: still reported, by its run, and kept in the ledger."""
    one_project(bench, last_run_read=NEW_RUN_AT, finding=int(OLD_RUN))
    rc, out = bench.run(routes())
    sec = bench.section("Alpha", out)
    assert has(r"\bfinding\b", sec) and OLD_RUN in sec, "the standing finding (run %s) is not reported:\n%s" % (OLD_RUN, sec)
    assert "DEP-" in sec, "the standing finding's remedy names no DEP- increment:\n%s" % sec
    assert not has(r"\bgreen\b", sec), "a standing finding reported green:\n%s" % sec
    assert str(bench.window("Alpha").get("finding_standing")) == OLD_RUN, "the standing finding was dropped: %r" % bench.window("Alpha")


def test_r097_a_later_success_clears_the_standing_finding(bench):
    """A finding standing and a later run of the window ended success: green, the finding cleared."""
    one_project(bench, last_run_read=OLD_RUN_AT, finding=int(OLD_RUN))
    rc, out = bench.run(routes())
    sec = bench.section("Alpha", out)
    assert has(r"\bgreen\b", sec), "a later success did not clear the finding:\n%s" % sec
    w = bench.window("Alpha")
    assert w.get("finding_standing") is None and w.get("last_run_read") == NEW_RUN_AT, "the window after a success: %r" % w


def test_r097_the_ledger_moves_only_after_security_md_is_written(bench):
    """security.md cannot be written (a file stands where the evaluation folder must be): the reads made, the ledger
    byte-identical, the exit non-zero."""
    before = one_project(bench, finding=None)
    (bench.root / "Reports" / "Evaluations").mkdir(parents=True)
    bench.out_dir.write_text("a file where the folder must be\n", encoding="utf-8")
    rc, out = bench.run(routes(runs="security-runs-failed.json", jobs="security-jobs-failed.json", log="security-log-finding.json"))
    assert bench.calls(), "no read was made, so the order of the write and the ledger was not tried:\n%s" % out
    assert rc not in (0, None), "exit %r though security.md could not be written:\n%s" % (rc, out)
    assert bench.ledger_path.read_bytes() == before, "the ledger moved though security.md was not written"


SEED_SAMPLE = """# Evaluation of 2026-11-15

## 5. Dependency scan

Read on 2026-11-15, read-only, under step 1b.

| Project | Repository | Workflow | Kind | last run read | Remedy |
|---|---|---|---|---|---|
| The alpha project | `OWNER/REPO` | `dependency-scan` active | **green**: one run in the window | `last run read: %s` | none |
| The bravo project | `OWNER/OTHER` | `dependency-scan` active | **not configured** | `last run read: none` | the calibration |

## 6. Security alerts
""" % NEW_RUN_AT


def test_r097_seed_from_takes_the_window_from_the_last_hand_written_section(bench):
    """--seed-from <evaluation file>: each project's last run read taken from the table's row of its owner/repo; a time
    leaves the runs read before out of the window, `none` reads every listed run."""
    alpha = bench.project("Alpha", "https://github.com/OWNER/REPO.git")
    bravo = bench.project("Bravo", "https://github.com/OWNER/OTHER.git")
    bench.write_projects({"Alpha": alpha, "Bravo": bravo})
    bench.write_ledger(None)
    sample = bench.tmp / "2026-11-15.md"
    sample.write_text(SEED_SAMPLE, encoding="utf-8")
    r = routes("OWNER/REPO")
    r.update(routes("OWNER/OTHER"))
    rc, out = bench.run(r, "--seed-from", str(sample))
    a, b = bench.section("Alpha", out), bench.section("Bravo", out)
    assert has(r"no completed run", a), "Alpha's window was not seeded from its row (%s):\n%s" % (NEW_RUN_AT, a)
    assert has(r"\bgreen\b", b), "Bravo's window (seeded none) did not read the listed runs:\n%s" % b
    assert bench.window("Alpha").get("last_run_read") == NEW_RUN_AT
    assert bench.window("Bravo").get("last_run_read") == NEW_RUN_AT
    assert_get_only(bench)


def test_r097_one_section_per_project(bench):
    """Three projects, green, a finding and no remote: three sections, each headed by its project's name and of its kind."""
    alpha = bench.project("Alpha", "https://github.com/OWNER/REPO.git")
    bravo = bench.project("Bravo", "https://github.com/OWNER/OTHER.git")
    charlie = bench.project("Charlie", None)
    bench.write_projects({"Alpha": alpha, "Bravo": bravo, "Charlie": charlie})
    window = {"last_run_read": OLD_RUN_AT, "finding_standing": None}
    bench.write_ledger({"Alpha": dict(window), "Bravo": dict(window), "Charlie": {"last_run_read": None, "finding_standing": None}})
    r = routes("OWNER/REPO")
    r.update(routes("OWNER/OTHER", runs="security-runs-failed.json", jobs="security-jobs-failed.json", log="security-log-finding.json"))
    rc, out = bench.run(r)
    a, b, c = bench.section("Alpha", out), bench.section("Bravo", out), bench.section("Charlie", out)
    assert has(r"\bgreen\b", a) and not has(r"\bgreen\b", b) and not has(r"\bgreen\b", c), "green in the wrong section"
    assert has(r"\bfinding\b", b) and "DEP-" in b, "Bravo's finding is not in its section:\n%s" % b
    assert "DEP-" not in a, "Alpha's section carries Bravo's finding:\n%s" % a
    assert has(r"no remote", c), "Charlie's section does not say no remote:\n%s" % c
    assert_clean_file(bench, out)
    assert_get_only(bench)
    assert str(bench.window("Bravo").get("finding_standing")) == NEW_RUN
    assert bench.window("Alpha").get("finding_standing") is None


# ---------------------------------------------------------------- pace-report


def run_pace(bench):
    env = dict(os.environ)
    p = subprocess.run([sys.executable, PACE, "--weeks", "1"], cwd=str(bench.root / "Workspace"), env=env,
                       capture_output=True, text=True, timeout=600)
    return p.returncode, p.stdout + p.stderr


def test_r097_pace_report_with_no_roots_reads_the_projects_file(bench):
    """pace-report.py with no roots: the projects of ~/.cursor-bridge/projects.json, none of the paths the program held."""
    alpha = bench.project("Alpha")
    bench.write_projects({"Alpha": alpha})
    rc, out = run_pace(bench)
    assert re.search(r"^#+ .*(Alpha|alpha-root)", out, re.M), "pace-report did not report the project the file names:\n%s" % out
    for old in OLD_PROJECT_DIRS:
        assert old not in out, "pace-report still read a path the program held (%s):\n%s" % (old, out)


def test_r097_pace_report_with_no_roots_names_an_absent_projects_file(bench):
    """pace-report.py with no roots and no projects file: it says so, naming the file, and reads none of the old paths."""
    rc, out = run_pace(bench)
    assert "projects.json" in out, "pace-report does not name the absent projects file:\n%s" % out
    for old in OLD_PROJECT_DIRS:
        assert old not in out, "pace-report still read a path the program held (%s):\n%s" % (old, out)


# ================================================================ round 2: the supervisor's rulings (handoff/TASK-077-r2.md)

import datetime
import traceback

EARLY = "2026-11-01T00:00:00Z"          # a window start before both captured runs, so both are of the window


def run_caught(bench, route_map=None, *extra):
    """bench.run, with an exception out of main() turned into printed text (a Traceback the cases assert against)."""
    try:
        return bench.run(route_map, *extra)
    except Exception:
        got = bench.capsys.readouterr()
        return "raised", got.out + got.err + traceback.format_exc()


def main_caught(bench, argv):
    """Run the program's main() with argv (no stand-in), the working folder in the scratch bridge root."""
    mod = bench.load()
    bench.mp.chdir(str(bench.root / "Workspace"))
    bench.mp.setattr(sys, "argv", argv)
    bench.capsys.readouterr()
    try:
        rc = mod.main()
        tb = ""
    except SystemExit as e:
        rc, tb = e.code, ""
    except Exception:
        rc, tb = "raised", traceback.format_exc()
    got = bench.capsys.readouterr()
    return rc, got.out + got.err + tb


def fail_gh_call(bench, marker, how):
    """Make the gh call whose arguments hold `marker` time out (how="timeout") or fail to start (how="start")."""
    real = subprocess.run

    def fake(cmd, *a, **k):
        if isinstance(cmd, (list, tuple)) and str(bench.standin) in [str(x) for x in cmd] \
                and any(marker in str(x) for x in cmd):
            if how == "timeout":
                raise subprocess.TimeoutExpired(cmd, k.get("timeout") or 30)
            raise FileNotFoundError(2, "No such file or directory", "gh")
        return real(cmd, *a, **k)

    bench.mp.setattr(subprocess, "run", fake)


def record_git_calls(bench):
    """Record (argv, env) of every git call made through subprocess.run from here on."""
    seen = []
    real = subprocess.run

    def fake(cmd, *a, **k):
        if isinstance(cmd, (list, tuple)) and cmd and os.path.basename(str(cmd[0])).lower() in ("git", "git.exe"):
            seen.append(([str(x) for x in cmd], k.get("env")))
        return real(cmd, *a, **k)

    bench.mp.setattr(subprocess, "run", fake)
    return seen


def standing_line(run_id, text):
    return re.search(r"finding standing\W+run\W+%s\b" % re.escape(str(run_id)), text, re.I) is not None


def says_no_alert_open(sec):
    return any(has(r"\balert", l) and (has(r"\b(no|none|nothing|0)\b[^\n]*\bopen\b", l) or has(r"\bopen\b[^\n]*\b(none|0)\b", l))
               for l in sec.splitlines())


def failure_line(sec, read, how):
    """A line of the section naming the read and how it failed (Ruling 5's phrase, its wording beyond these not pinned)."""
    return any(has(read, l) and has(how, l) for l in sec.splitlines())


def utc(text):
    return datetime.datetime.fromisoformat(text[:-1] + "+00:00" if text.endswith("Z") else text)


# ---------------------------------------------------------------- Rulings 1-3: every failed run read, the standing finding


def test_r097_an_earlier_exit_1_failure_stands_beside_a_later_cancelled_run(bench):
    """A window of [a failure whose log reads exit 1, a later cancelled run]: the week's kind is a scanner failure with the
    rerun command, and beside it the finding stands by the failed run's id; the failed run's jobs and its failed job's log are
    read; the ledger holds that id standing and last_run_read at the cancelled run's time.
    enforces: handoff/TASK-077-r2.md Ruling 1; handoff/TASK-077.md R5 (c), R6."""
    one_project(bench, last_run_read=EARLY)
    r = routes(runs="security-runs-failed-then-cancelled.json", log="security-log-finding.json")
    r["repos/OWNER/REPO/actions/runs/%s/jobs" % OLD_RUN] = "security-jobs-failed-older.json"
    rc, out = bench.run(r)
    sec = bench.section("Alpha", out)
    assert standing_line(OLD_RUN, sec), "the exit-1 failure of run %s does not stand beside the week's kind:\n%s" % (OLD_RUN, sec)
    assert has(r"scanner failure", sec) and RERUN in sec, "the week's kind (the cancelled run) is not a scanner failure with `%s`:\n%s" % (RERUN, sec)
    assert not has(r"\bgreen\b", sec), "a section with a finding says green:\n%s" % sec
    paths = bench.paths()
    assert any(p.startswith("repos/OWNER/REPO/actions/runs/%s/jobs" % OLD_RUN) for p in paths), "the failed run's jobs were not read: %r" % paths
    assert any(p.startswith("repos/OWNER/REPO/actions/jobs/%s/logs" % JOB) for p in paths), "the failed job's log was not read: %r" % paths
    w = bench.window("Alpha")
    assert str(w.get("finding_standing")) == OLD_RUN, "the finding of run %s does not stand in the ledger: %r" % (OLD_RUN, w)
    assert w.get("last_run_read") == NEW_RUN_AT, "last_run_read is not the cancelled run's time: %r" % w
    assert_clean_file(bench, out)
    assert_get_only(bench)


def test_r097_a_standing_finding_does_not_hide_the_weeks_cancelled_run(bench):
    """A finding standing (run OLD) and a cancelled run in the window: the week's kind is a scanner failure with the rerun
    command, the standing line beside it, and last_run_read moves to the cancelled run.
    enforces: handoff/TASK-077-r2.md Ruling 2; handoff/TASK-077.md R6, R11."""
    one_project(bench, last_run_read=OLD_RUN_AT, finding=int(OLD_RUN))
    rc, out = bench.run(routes(runs="security-runs-cancelled.json"))
    sec = bench.section("Alpha", out)
    assert has(r"scanner failure", sec) and RERUN in sec, "the week's cancelled run is not reported as a scanner failure with `%s`:\n%s" % (RERUN, sec)
    assert standing_line(OLD_RUN, sec), "the standing finding (run %s) is not beside the week's kind:\n%s" % (OLD_RUN, sec)
    w = bench.window("Alpha")
    assert w.get("last_run_read") == NEW_RUN_AT, "last_run_read did not move to the window's completed run: %r" % w
    assert str(w.get("finding_standing")) == OLD_RUN, "the standing finding was dropped: %r" % w


def test_r097_a_standing_finding_does_not_skip_reading_a_new_failure(bench):
    """A finding standing (run OLD) and a new failure in the window whose log reads exit 1: the new run's jobs and its failed
    job's log are read (the stand-in's log), and the newer finding stands.
    enforces: handoff/TASK-077-r2.md Rulings 1 and 2; handoff/TASK-077.md R5 (c)."""
    one_project(bench, last_run_read=OLD_RUN_AT, finding=int(OLD_RUN))
    rc, out = bench.run(routes(runs="security-runs-failed.json", jobs="security-jobs-failed.json", log="security-log-finding.json"))
    paths = bench.paths()
    assert any(p.startswith("repos/OWNER/REPO/actions/runs/%s/jobs" % NEW_RUN) for p in paths), "the new failed run's jobs were not read: %r" % paths
    assert any(p.startswith("repos/OWNER/REPO/actions/jobs/%s/logs" % JOB) for p in paths), "the new failed job's log was not read: %r" % paths
    sec = bench.section("Alpha", out)
    assert has(r"\bfinding\b", sec) and "DEP-" in sec, "the new finding is not reported with a DEP- increment:\n%s" % sec
    w = bench.window("Alpha")
    assert str(w.get("finding_standing")) == NEW_RUN, "the newest exit-1 run does not stand: %r" % w
    assert w.get("last_run_read") == NEW_RUN_AT, "last_run_read did not move: %r" % w
    assert_clean_file(bench, out)


def test_r097_a_success_later_than_the_standing_run_clears_it_though_not_last(bench):
    """A finding standing (a run older than the window, its time unknown), the window [success, later cancelled]: the success
    is later than last_run_read, so the finding is cleared: no finding standing line, the ledger's finding_standing null.
    enforces: handoff/TASK-077-r2.md Ruling 3; handoff/TASK-077.md R6."""
    standing = "41000000001"
    one_project(bench, last_run_read=EARLY, finding=int(standing))
    rc, out = bench.run(routes(runs="security-runs-cancelled.json"))
    sec = bench.section("Alpha", out)
    assert not has(r"finding standing", sec) and standing not in sec, "the finding cleared by a later success still stands:\n%s" % sec
    assert has(r"scanner failure", sec), "the week's kind (the last run cancelled) is not a scanner failure:\n%s" % sec
    w = bench.window("Alpha")
    assert w.get("finding_standing") is None, "the cleared finding still stands in the ledger: %r" % w
    assert w.get("last_run_read") == NEW_RUN_AT, "last_run_read did not move: %r" % w


# ---------------------------------------------------------------- Ruling 4: the alerts read for every project with a remote


def test_r097_the_alerts_are_read_for_a_project_not_configured(bench):
    """No dependency-scan workflow and one open alert: not configured, and the alert named by its number (#41) and package.
    enforces: handoff/TASK-077-r2.md Ruling 4; handoff/TASK-077.md R5 (d) (e), R9."""
    one_project(bench)
    rc, out = bench.run(routes(workflows="security-workflows-absent.json", alerts="security-alerts-one.json"))
    sec = bench.section("Alpha", out)
    assert has(r"not configured", sec), "the section does not say not configured:\n%s" % sec
    assert re.search(r"(?<!\d)41(?!\d)", sec) and "requests" in sec, "the open alert (41, requests) is not named:\n%s" % sec
    paths = bench.paths()
    assert any(p.startswith("repos/OWNER/REPO/vulnerability-alerts") for p in paths), "the alerts check was not made: %r" % paths
    assert any(p.startswith("repos/OWNER/REPO/dependabot/alerts") for p in paths), "the open alerts were not listed: %r" % paths
    assert_get_only(bench)


def test_r097_the_alerts_are_read_for_a_disabled_workflow(bench):
    """A disabled workflow and the alerts off: no completed run, and alerts off written; the alerts check made.
    enforces: handoff/TASK-077-r2.md Ruling 4; handoff/TASK-077.md R5 (d), R9."""
    one_project(bench)
    rc, out = bench.run(routes(workflows="security-workflows-disabled.json", vuln="security-vulnerability-alerts-off.json"))
    sec = bench.section("Alpha", out)
    assert has(r"no completed run", sec), "the disabled workflow is not no completed run:\n%s" % sec
    paths = bench.paths()
    assert any(p.startswith("repos/OWNER/REPO/vulnerability-alerts") for p in paths), "the alerts check was not made: %r" % paths
    assert has(r"alerts off", sec), "the section does not say alerts off:\n%s" % sec
    assert not any("dependabot/alerts" in p for p in paths), "the open alerts were listed after a 404: %r" % paths


def test_r097_the_alerts_are_read_after_a_failed_workflows_read(bench):
    """The workflows list refused (403) and one open alert: the alerts are still read and the alert named.
    enforces: handoff/TASK-077-r2.md Ruling 4; handoff/TASK-077.md R5 (d) (e), R7."""
    one_project(bench)
    rc, out = bench.run(routes(workflows="security-forbidden.json", alerts="security-alerts-one.json"))
    paths = bench.paths()
    assert any(p.startswith("repos/OWNER/REPO/vulnerability-alerts") for p in paths), "the alerts check was not made: %r" % paths
    assert any(p.startswith("repos/OWNER/REPO/dependabot/alerts") for p in paths), "the open alerts were not listed: %r" % paths
    sec = bench.section("Alpha", out)
    assert re.search(r"(?<!\d)41(?!\d)", sec) and "requests" in sec, "the open alert (41, requests) is not named:\n%s" % sec
    assert not has(r"\bgreen\b", sec), "a failed read reported green:\n%s" % sec


# ---------------------------------------------------------------- Ruling 5: a failed read names the read and the failure


PHRASED_FAILURES = {
    "the workflows list, gh exited non-zero": dict(route=("repos/OWNER/REPO/actions/workflows", "!crash"),
                                                   read=r"workflows list", how=r"non-zero", alerts=False),
    "the runs list refused (403)": dict(route=("repos/OWNER/REPO/actions/workflows/dependency-scan.yml/runs", "security-forbidden.json"),
                                        read=r"runs list", how=r"\b403\b", alerts=False),
    "the runs list timed out": dict(inject=("dependency-scan.yml/runs", "timeout"), read=r"runs list", how=r"timed out", alerts=False),
    "the jobs list refused (403)": dict(kw=dict(runs="security-runs-failed.json"),
                                        route=("repos/OWNER/REPO/actions/runs/%s/jobs" % NEW_RUN, "security-forbidden.json"),
                                        read=r"jobs list", how=r"\b403\b", alerts=False),
    "the job log, gh exited non-zero": dict(kw=dict(runs="security-runs-failed.json", jobs="security-jobs-failed.json"),
                                            route=("repos/OWNER/REPO/actions/jobs/%s/logs" % JOB, "!crash"),
                                            read=r"job log", how=r"non-zero", alerts=False),
    "the alerts check, gh could not start": dict(inject=("vulnerability-alerts", "start"), read=r"alerts check",
                                                 how=r"could not start", alerts=True),
    "the open alerts list refused (403)": dict(route=("repos/OWNER/REPO/dependabot/alerts", "security-forbidden.json"),
                                               read=r"open alerts list", how=r"\b403\b", alerts=True),
}


@pytest.mark.parametrize("case", sorted(PHRASED_FAILURES))
def test_r097_a_failed_read_names_which_read_failed_and_how(bench, case):
    """A failed read is written on a line naming the read (workflows list, runs list, jobs list, job log, alerts check, open
    alerts list) and how it failed (refused (HTTP 403), timed out, gh could not start, gh exited non-zero); the remedy names
    the login's scope (and the Security tab for the alerts' reads); a failed (a)-(c) read's kind line says the scan could not
    be read, the word finding kept; never green. The wording around the read's name and the failure's word is not pinned.
    enforces: handoff/TASK-077-r2.md Ruling 5; handoff/TASK-077.md R7."""
    spec = PHRASED_FAILURES[case]
    one_project(bench)
    r = routes(**spec.get("kw", {}))
    if spec.get("route"):
        r[spec["route"][0]] = spec["route"][1]
    if spec.get("inject"):
        fail_gh_call(bench, *spec["inject"])
    rc, out = run_caught(bench, r)
    assert "Traceback" not in out, "%s ended in a traceback:\n%s" % (case, out)
    sec = bench.section("Alpha", out)
    assert failure_line(sec, spec["read"], spec["how"]), \
        "%s: no line names the read (%s) and how it failed (%s):\n%s" % (case, spec["read"], spec["how"], sec)
    assert has(r"\bfinding\b", sec), "%s: the word finding is not in the section:\n%s" % (case, sec)
    assert has(r"\bscope\b|gh auth refresh -s", sec), "%s: the remedy does not name the login's scope:\n%s" % (case, sec)
    if spec["alerts"]:
        assert has(r"security tab", sec), "%s: the remedy does not name the repository's Security tab:\n%s" % (case, sec)
    else:
        assert has(r"could not be read", sec), "%s: the kind line does not say the scan could not be read:\n%s" % (case, sec)
    assert not has(r"\bgreen\b", sec), "%s reported green:\n%s" % (case, sec)
    assert FAKE_TOKEN not in out, "a token was printed"
    assert_clean_file(bench, out)


def test_r097_a_failed_alerts_read_keeps_the_scans_own_result(bench):
    """A green scan and the open alerts list refused (403): the section holds the alerts' failure (the open alerts list, 403)
    with the Security tab remedy, and the scan's own result still stated, by the newest run read's time. Reading of Ruling 5
    with R6: a section whose alerts read failed is not a green section, so the word green is not in it; the scan's kind is
    shown by its last run read and by being neither a scanner failure nor no completed run.
    enforces: handoff/TASK-077-r2.md Ruling 5; handoff/TASK-077.md R6, R7."""
    one_project(bench)
    rc, out = bench.run(routes(alerts="security-forbidden.json"))
    sec = bench.section("Alpha", out)
    assert failure_line(sec, r"open alerts list", r"\b403\b"), "no line names the open alerts list's failure (403):\n%s" % sec
    assert has(r"security tab", sec), "the alerts failure's remedy does not name the Security tab:\n%s" % sec
    assert NEW_RUN_AT in sec, "the scan's own result (the run read at %s) is not stated beside the alerts failure:\n%s" % (NEW_RUN_AT, sec)
    assert not has(r"scanner failure", sec) and not has(r"no completed run", sec), "the scan's kind was replaced:\n%s" % sec
    assert not has(r"\bgreen\b", sec), "a section whose alerts read failed says green:\n%s" % sec


# ---------------------------------------------------------------- Ruling 6: printable ASCII only


def visible_escape(code, text):
    return re.search(r"\\(x%02x|u%04x)" % (code, code), text, re.I) is not None


def test_r097_control_bytes_and_non_ascii_are_written_as_visible_escapes(bench):
    """An open alert whose package name and advisory id hold ESC, TAB, BEL, DEL and a non-ASCII letter, and a project name
    holding a control byte: security.md holds no byte outside 0x20-0x7E but LF/CR, and each is written as a visible escape
    (\\xNN or \\uNNNN).
    enforces: handoff/TASK-077-r2.md Ruling 6; handoff/TASK-077.md R10."""
    name = "Al\x01pha"
    root = bench.project(name)
    bench.write_projects({name: root})
    bench.write_ledger({name: {"last_run_read": OLD_RUN_AT, "finding_standing": None}})
    rc, out = bench.run(routes(alerts="security-alerts-control.json"))
    assert_clean_file(bench, out)
    text = bench.report(out)
    assert visible_escape(0x01, text) and "pha" in text, "the project name's control byte is not a visible escape:\n%s" % text
    for code in (0x1B, 0x09, 0x07, 0x7F, 0xE9, 0xFC):
        assert visible_escape(code, text), "the character 0x%02X is not written as a visible escape:\n%s" % (code, text)
    assert re.search(r"(?<!\d)42(?!\d)", text), "the open alert (42) is not named:\n%s" % text


def test_r097_pace_report_prints_names_as_printable_ascii(bench):
    """pace-report's _ascii_name: ESC, TAB, DEL and a non-ASCII letter written as visible escapes, nothing outside 0x20-0x7E.
    enforces: handoff/TASK-077-r2.md Ruling 6."""
    bench.mp.syspath_prepend(BRIDGE)
    spec = importlib.util.spec_from_file_location("pace_report_t077", PACE)
    pace = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pace)
    got = pace._ascii_name("Al\x1bpha\tbe\x7ftaé")
    bad = sorted(set(hex(ord(c)) for c in got if not 0x20 <= ord(c) <= 0x7E))
    assert not bad, "_ascii_name left characters outside 0x20-0x7E: %r in %r" % (bad, got)
    for code in (0x1B, 0x09, 0x7F, 0xE9):
        assert visible_escape(code, got), "_ascii_name does not write 0x%02X as a visible escape: %r" % (code, got)


# ---------------------------------------------------------------- Ruling 7: reading the projects file


def test_r097_a_utf16_projects_file_is_refused_without_a_traceback(bench):
    """A UTF-16 projects file: refused with its reason (not UTF-8 text), the file named, exit 2, no traceback, nothing
    written, no read.
    enforces: handoff/TASK-077-r2.md Ruling 7; handoff/TASK-077.md R2."""
    root = bench.project("Alpha")
    bench.projects_file.parent.mkdir(parents=True, exist_ok=True)
    bench.projects_file.write_bytes(json.dumps({"Alpha": str(root)}).encode("utf-16"))
    before = bench.write_ledger({})
    rc, out = run_caught(bench, routes())
    assert "Traceback" not in out, "a UTF-16 projects file ended in a traceback:\n%s" % out
    assert rc == 2, "exit %r, not 2:\n%s" % (rc, out)
    assert "projects.json" in out and has(r"utf-?8", out), "the refusal does not name the file and say it is not UTF-8 text:\n%s" % out
    assert not bench.out_dir.exists(), "something was written under Reports/Evaluations/%s" % DATE
    assert bench.ledger_path.read_bytes() == before, "the ledger changed"
    assert bench.calls() == [], "a read was made: %r" % bench.calls()


def test_r097_a_projects_file_with_a_byte_order_mark_is_accepted(bench):
    """A UTF-8 projects file starting with a byte-order mark: accepted, exit 0, the project's section written.
    enforces: handoff/TASK-077-r2.md Ruling 7; handoff/TASK-077.md R2."""
    root = bench.project("Alpha")
    bench.projects_file.parent.mkdir(parents=True, exist_ok=True)
    bench.projects_file.write_bytes(b"\xef\xbb\xbf" + json.dumps({"Alpha": str(root)}).encode("utf-8"))
    bench.write_ledger({"Alpha": {"last_run_read": OLD_RUN_AT, "finding_standing": None}})
    rc, out = run_caught(bench, routes())
    assert rc == 0, "a projects file with a byte-order mark was refused (exit %r):\n%s" % (rc, out)
    sec = bench.section("Alpha", out)
    assert has(r"\bgreen\b", sec), "the project's section was not written from the file:\n%s" % sec


def other_home_with_zulu(bench):
    """A second folder holding its own .cursor-bridge/projects.json naming Zulu (a project), for --home."""
    zulu = bench.project("Zulu")
    other = bench.tmp / "sessions-home"
    (other / ".cursor-bridge").mkdir(parents=True)
    (other / ".cursor-bridge" / "projects.json").write_text(json.dumps({"Zulu": str(zulu)}), encoding="utf-8")
    return other


def test_r097_collect_home_never_chooses_the_projects_file(bench):
    """collect --home <folder>: the projects file is still the one under the user's home (~), never the --home folder's.
    enforces: handoff/TASK-077-r2.md Ruling 7; handoff/TASK-077.md R2."""
    root = bench.project("Alpha")
    docs = root / "Documents"
    docs.mkdir()
    (docs / "Alpha Issues During Development and Their Solutions.md").write_text(
        "# Alpha - Issues During Development and Their Solutions\n\n## ISS-001 - The first issue\nContext: the first.\n",
        encoding="utf-8")
    bench.write_projects({"Alpha": root})
    other = other_home_with_zulu(bench)
    bench.write_ledger({})
    rc, out = main_caught(bench, ["evaluate-reports.py", "collect", "--home", str(other)])
    assert "Alpha issues: 1 entries" in out, "collect --home did not read the projects of ~/.cursor-bridge/projects.json:\n%s" % out
    assert "Zulu" not in out, "collect --home read the projects file of the --home folder:\n%s" % out
    assert "Traceback" not in out, out


def test_r097_pace_report_home_never_chooses_the_projects_file(bench):
    """pace-report.py --home <folder> with no roots: the projects of ~/.cursor-bridge/projects.json, not the --home folder's.
    enforces: handoff/TASK-077-r2.md Ruling 7; handoff/TASK-077.md R15."""
    alpha = bench.project("Alpha")
    bench.write_projects({"Alpha": alpha})
    other = other_home_with_zulu(bench)
    rc, out, err = run_pace_split(bench, "--home", str(other))
    heads = [l for l in out.splitlines() if l.startswith("#")]
    assert any(re.search(r"Alpha|alpha-root", h) for h in heads), "pace-report --home did not read ~'s projects file:\n%s%s" % (out, err)
    assert not any(re.search(r"Zulu|zulu-root", h) for h in heads), "pace-report --home read the --home folder's projects file:\n%s" % out


# ---------------------------------------------------------------- Ruling 8: run and job ids


def test_r097_a_run_id_that_is_not_digits_is_a_failed_read_and_never_a_path(bench):
    """A failed run listed with the id ../../../user: no call holds that text; the runs list is a failed read (reply could
    not be parsed); never green; the ledger entry as it stood.
    enforces: handoff/TASK-077-r2.md Ruling 8; handoff/TASK-077.md R5, R7."""
    one_project(bench)
    rc, out = run_caught(bench, routes(runs="security-runs-bad-id.json", jobs="security-jobs-failed.json", log="security-log-finding.json"))
    assert not any("../../../user" in a or "/user/" in a for c in bench.calls() for a in c), \
        "a run id that is not digits entered a call: %r" % bench.calls()
    assert "Traceback" not in out, out
    sec = bench.section("Alpha", out)
    assert failure_line(sec, r"runs list", r"pars"), "the runs list is not a failed read (reply could not be parsed):\n%s" % sec
    assert not has(r"\bgreen\b", sec), "a failed read reported green:\n%s" % sec
    assert bench.window("Alpha") == {"last_run_read": OLD_RUN_AT, "finding_standing": None}, \
        "the ledger entry changed after a failed runs read: %r" % bench.window("Alpha")


def test_r097_finding_standing_is_stored_as_an_int(bench):
    """A finding of the window: the ledger's finding_standing is the run id as an int.
    enforces: handoff/TASK-077-r2.md Ruling 8; handoff/TASK-077.md R11."""
    one_project(bench)
    rc, out = bench.run(routes(runs="security-runs-failed.json", jobs="security-jobs-failed.json", log="security-log-finding.json"))
    w = bench.window("Alpha")
    fs = w.get("finding_standing")
    assert isinstance(fs, int) and not isinstance(fs, bool) and fs == int(NEW_RUN), "finding_standing is not the int %s: %r" % (NEW_RUN, w)


def test_r097_a_digits_string_standing_from_an_older_ledger_is_kept_as_an_int(bench):
    """An older ledger holding finding_standing as a digits string: accepted, reported by its run, stored back as an int.
    enforces: handoff/TASK-077-r2.md Ruling 8; handoff/TASK-077.md R6, R11."""
    one_project(bench, last_run_read=NEW_RUN_AT, finding=OLD_RUN)
    rc, out = bench.run(routes())
    sec = bench.section("Alpha", out)
    assert standing_line(OLD_RUN, sec), "the standing finding (run %s) is not reported:\n%s" % (OLD_RUN, sec)
    fs = bench.window("Alpha").get("finding_standing")
    assert isinstance(fs, int) and not isinstance(fs, bool) and fs == int(OLD_RUN), "finding_standing is not the int %s: %r" % (OLD_RUN, fs)


# ---------------------------------------------------------------- Ruling 9: unexpected reply shapes


BAD_ALERTS = {
    "an array of non-objects": "security-alerts-not-objects.json",
    "an object with exit 0": "security-alerts-object.json",
    "an empty body with exit 0": "security-alerts-empty.json",
}


@pytest.mark.parametrize("case", sorted(BAD_ALERTS))
def test_r097_an_open_alerts_reply_of_an_unexpected_shape_is_a_failed_read(bench, case):
    """The open alerts list answers [1, 2], {"message": "x"} or nothing (exit 0): a failed read of the open alerts list with
    the Security tab remedy, never the no-alert line, never a traceback.
    enforces: handoff/TASK-077-r2.md Ruling 9; handoff/TASK-077.md R7, R9."""
    one_project(bench)
    rc, out = run_caught(bench, routes(alerts=BAD_ALERTS[case]))
    assert "Traceback" not in out, "%s ended in a traceback:\n%s" % (case, out)
    sec = bench.section("Alpha", out)
    assert not says_no_alert_open(sec), "%s was read as no alert open:\n%s" % (case, sec)
    assert failure_line(sec, r"open alerts list", r"pars|read failed|fail"), "%s is not a failed read of the open alerts list:\n%s" % (case, sec)
    assert has(r"security tab", sec), "%s: the remedy does not name the Security tab:\n%s" % (case, sec)
    assert not has(r"\bgreen\b", sec), "%s reported green:\n%s" % (case, sec)


# ---------------------------------------------------------------- Rulings 10-11: malformed runs, order by time


MALFORMED_RUNS = {
    "a created_at that does not parse": "security-runs-bad-time.json",
    "a completed run with no conclusion": "security-runs-no-conclusion.json",
}


@pytest.mark.parametrize("case", sorted(MALFORMED_RUNS))
def test_r097_a_malformed_run_fails_the_runs_read(bench, case):
    """The newest listed run malformed (its created_at does not parse, or completed with no conclusion) behind an older
    success: not green, a failed read of the runs list, the ledger entry as it stood.
    enforces: handoff/TASK-077-r2.md Ruling 10; handoff/TASK-077.md R7, R11."""
    one_project(bench, last_run_read=EARLY)
    rc, out = run_caught(bench, routes(runs=MALFORMED_RUNS[case]))
    assert "Traceback" not in out, out
    sec = bench.section("Alpha", out)
    assert not has(r"\bgreen\b", sec), "%s was dropped and the older success read green:\n%s" % (case, sec)
    assert failure_line(sec, r"runs list", r"pars|read failed|fail"), "%s is not a failed read of the runs list:\n%s" % (case, sec)
    assert bench.window("Alpha") == {"last_run_read": EARLY, "finding_standing": None}, \
        "the ledger entry changed after a failed runs read: %r" % bench.window("Alpha")


def test_r097_the_newest_run_is_chosen_by_time_not_by_text(bench):
    """Two runs listed out of time order, created_at in the Z and +00:00 forms: the later by time (a success, earlier as
    text) decides: green, and last_run_read is that run's time.
    enforces: handoff/TASK-077-r2.md Ruling 11; handoff/TASK-077.md R6, R11."""
    one_project(bench)
    rc, out = bench.run(routes(runs="security-runs-out-of-order.json"))
    sec = bench.section("Alpha", out)
    assert has(r"\bgreen\b", sec) and not has(r"scanner failure", sec), "the newest run by time (a success) did not decide:\n%s" % sec
    lrr = bench.window("Alpha").get("last_run_read")
    assert lrr and utc(lrr) == utc("2026-11-15T13:54:53.900+00:00"), "last_run_read is not the newest run's time: %r" % lrr


# ---------------------------------------------------------------- Rulings 12-14: the workflow, the remote, the git call


def test_r097_a_lookalike_workflow_path_is_not_configured(bench):
    """A workflow whose path ends in my-dependency-scan.yml only: not configured, no run read.
    enforces: handoff/TASK-077-r2.md Ruling 12; handoff/TASK-077.md R5 (b)."""
    one_project(bench)
    rc, out = bench.run(routes(workflows="security-workflows-lookalike.json"))
    sec = bench.section("Alpha", out)
    assert has(r"not configured", sec), "a path ending in my-dependency-scan.yml was taken for the workflow:\n%s" % sec
    assert not any("/runs" in p for p in bench.paths()), "a run was read for a lookalike workflow: %r" % bench.paths()


@pytest.mark.parametrize("origin", ["https://github.com/../..", "git@github.com:./REPO.git"])
def test_r097_an_owner_or_repo_of_dots_only_is_no_remote(bench, origin):
    """An origin whose owner or repository segment is dots only: no remote, and no gh call.
    enforces: handoff/TASK-077-r2.md Ruling 13; handoff/TASK-077.md R4."""
    one_project(bench, origin=origin)
    rc, out = run_caught(bench, routes())
    assert bench.calls() == [], "a gh call was made for the origin %s: %r" % (origin, bench.calls())
    sec = bench.section("Alpha", out)
    assert has(r"no remote", sec), "the origin %s is not no remote:\n%s" % (origin, sec)


def test_r097_the_origin_read_runs_git_with_fsmonitor_off(bench):
    """The git call reading origin carries -c core.fsmonitor=false (recorded from subprocess.run in the program).
    enforces: handoff/TASK-077-r2.md Ruling 14; handoff/TASK-077.md R4."""
    one_project(bench)
    seen = record_git_calls(bench)
    rc, out = bench.run(routes())
    assert seen, "no git call was recorded (the origin read goes through subprocess.run):\n%s" % out
    for argv, _env in seen:
        pairs = list(zip(argv, argv[1:]))
        assert ("-c", "core.fsmonitor=false") in pairs or "-ccore.fsmonitor=false" in argv, \
            "a git call without -c core.fsmonitor=false: %r" % argv


def test_r097_git_dir_from_the_environment_does_not_choose_the_origin(bench):
    """GIT_DIR in the environment, pointing at another checkout whose origin is OWNER/DECOY: the project's own origin
    (OWNER/REPO) is still read, and no call names OWNER/DECOY.
    enforces: handoff/TASK-077-r2.md Ruling 14; handoff/TASK-077.md R4."""
    one_project(bench)
    decoy = bench.tmp / "decoy"
    decoy.mkdir()
    bench.git(decoy, "init", "-q")
    bench.git(decoy, "remote", "add", "origin", "https://github.com/OWNER/DECOY.git")
    bench.mp.setenv("GIT_DIR", str(decoy / ".git"))
    rc, out = bench.run(routes())
    assert not any("OWNER/DECOY" in a for c in bench.calls() for a in c), "GIT_DIR chose the origin read: %r" % bench.calls()
    sec = bench.section("Alpha", out)
    assert "OWNER/REPO" in sec and has(r"\bgreen\b", sec), "the project's own origin (OWNER/REPO) was not read:\n%s" % sec


# ---------------------------------------------------------------- Ruling 15: pace-report's default roots


def run_pace_split(bench, *args):
    env = dict(os.environ)
    p = subprocess.run([sys.executable, PACE, "--weeks", "1"] + list(args), cwd=str(bench.root / "Workspace"), env=env,
                       capture_output=True, text=True, timeout=600)
    return p.returncode, p.stdout, p.stderr


def test_r097_pace_report_names_roots_by_folder_in_the_files_order(bench):
    """pace-report.py with no roots: a project named Alpha at a folder alpha-root is headed alpha-root, and the roots keep
    the projects file's order (Zulu's zulu-root before alpha-root).
    enforces: handoff/TASK-077-r2.md Ruling 15; handoff/TASK-077.md R15."""
    zulu = bench.project("Zulu")
    alpha = bench.project("Alpha")
    bench.write_projects({"Zulu": zulu, "Alpha": alpha})
    rc, out, err = run_pace_split(bench)
    heads = [l for l in out.splitlines() if re.match(r"^#+ ", l)]
    za = [i for i, h in enumerate(heads) if "zulu-root" in h]
    aa = [i for i, h in enumerate(heads) if "alpha-root" in h]
    assert aa and za, "the roots are not headed by their folders' basenames (alpha-root, zulu-root): %r\n%s" % (heads, err)
    assert za[0] < aa[0], "the roots do not keep the projects file's order (zulu-root first): %r" % heads


def test_r097_pace_report_refuses_an_absent_projects_file_on_stderr(bench):
    """pace-report.py with no roots and no projects file: the refusal naming the file on stderr, exit 2.
    enforces: handoff/TASK-077-r2.md Ruling 15; handoff/TASK-077.md R15."""
    rc, out, err = run_pace_split(bench)
    assert "projects.json" in err, "the refusal is not on stderr:\nstdout:\n%s\nstderr:\n%s" % (out, err)
    assert "projects.json" not in out, "the refusal went to stdout:\n%s" % out
    assert rc == 2, "exit %r, not 2:\n%s%s" % (rc, out, err)
