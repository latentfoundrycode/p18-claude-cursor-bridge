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
