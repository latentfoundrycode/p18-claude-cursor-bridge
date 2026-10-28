"""R-044 pace-report.py: read-only weekly pace tables from git and launcher/guard records."""
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.abspath(os.path.join(HERE, os.pardir))
PACE = os.path.join(WORKSPACE, "bridge", "cursor-bridge", "pace-report.py")
ISS013_FORM = "docs: fixes (pointers, TASK-031's Scope, survival lists, records) (#61)"
UTC = datetime.timezone.utc
NOW = datetime.datetime.now(UTC)
MONDAY0 = datetime.datetime.combine(
    NOW.date() - datetime.timedelta(days=NOW.weekday()), datetime.time(0, 0), tzinfo=UTC
)


def at(k, day=2, hour=12):
    return MONDAY0 - datetime.timedelta(weeks=k) + datetime.timedelta(days=day, hours=hour)


def week(k):
    y, w, _ = (MONDAY0 - datetime.timedelta(weeks=k)).date().isocalendar()
    return (y, w)


def gitdate(dt):
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S+0000")


def run_id(dt):
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def git_env():
    return dict(
        os.environ,
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_SYSTEM=os.devnull,
        GIT_AUTHOR_NAME="t",
        GIT_AUTHOR_EMAIL="t@example.invalid",
        GIT_COMMITTER_NAME="t",
        GIT_COMMITTER_EMAIL="t@example.invalid",
    )


def pace(args, cwd):
    p = subprocess.run(  # windowless: visible-ok pace-report under test
        [sys.executable, PACE] + [str(a) for a in args],
        cwd=str(cwd),
        env=git_env(),
        capture_output=True,
        timeout=120,
    )
    return p.returncode, p.stdout.decode("ascii", "replace"), p.stderr.decode("ascii", "replace")


class MiniProject(object):
    def __init__(self, tmp_path, name="proj"):
        self.root = tmp_path / name
        self.ws = self.root / "Workspace"
        self.ws.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=str(self.ws), env=git_env(), check=True)  # windowless: visible-ok temp-repo git for tests
        (self.ws / ".gitignore").write_text("run/\n", encoding="utf-8")

    def brief(self, ident):
        p = self.ws / "handoff" / ("%s.md" % ident)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# %s\n" % ident, encoding="utf-8")

    def commit(self, subject, when):
        subprocess.run(["git", "-C", str(self.ws), "add", "-A"], env=git_env(), check=True)  # windowless: visible-ok temp-repo git for tests
        subprocess.run(  # windowless: visible-ok temp-repo git for tests
            ["git", "-C", str(self.ws), "commit", "-q", "--allow-empty", "--no-verify", "-m", subject],
            env={**git_env(), "GIT_AUTHOR_DATE": gitdate(when), "GIT_COMMITTER_DATE": gitdate(when)},
            check=True,
        )

    def launch(self, ident, when):
        row = {
            "id": run_id(when),
            "kind": "builder",
            "branch": ident.lower(),
            "exit": 0,
            "brief": ident,
            "round": 1,
            "brief_name": ident,
            "merge_ids": [ident],
        }
        p = self.ws / "run" / "launcher" / "runs.jsonl"
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")


def test_r044_ascii_output_and_build_parser(program):
    """R-044. pace-report is ASCII and exposes build_parser()."""
    mod = program("pace-report")
    assert mod.build_parser() is not None
    with open(PACE, "rb") as f:
        assert all(b < 128 for b in f.read())


def test_r044_non_project_root_exits_2(tmp_path):
    """R-044. A root without Workspace/.git exits 2 before table output."""
    bad = tmp_path / "bad"
    bad.mkdir()
    rc, out, err = pace([bad], tmp_path)
    assert rc == 2
    assert "bad" in err or "bad" in out
    assert "|" not in out


def test_r044_merge_and_start_weeks(tmp_path):
    """R-044. Launcher start and subject merge appear in their ISO weeks."""
    p = MiniProject(tmp_path)
    p.brief("TASK-501")
    p.commit("records: brief", at(10))
    p.launch("TASK-501", at(5))
    p.commit("TASK-501: shipped (#1)", at(2))
    rc, out, _ = pace([p.root], tmp_path)
    assert rc == 0
    wk = week(2)
    assert "%d-W%02d" % (wk[0], wk[1]) in out
    assert "1" in out


def test_r044_iss013_form_merges_nothing_with_plan_check(tmp_path, program):
    """R-044. ISS-013-shaped subject counts no merge; plan-check agrees on TASK-031."""
    p = MiniProject(tmp_path)
    p.brief("TASK-031")
    p.commit("records: brief", at(10))
    p.commit(ISS013_FORM, at(2))
    rc, out, _ = pace([p.root], tmp_path)
    assert rc == 0
    wk = week(2)
    row = [line for line in out.splitlines() if "%d-W%02d" % (wk[0], wk[1]) in line][0]
    parts = [c.strip() for c in row.strip("|").split("|")]
    assert parts[2] == "0"
    pc = program("plan-check")
    os.chdir(str(p.ws))
    assert "TASK-031" not in (pc.merged_ids("main") or set())


def test_r044_blank_mean_when_no_merge(tmp_path):
    """R-044. A week with no merges leaves mean days empty, not zero."""
    p = MiniProject(tmp_path)
    p.brief("TASK-601")
    p.commit("records: brief", at(10))
    p.commit("TASK-601: once (#1)", at(1))
    rc, out, _ = pace([p.root], tmp_path)
    assert rc == 0
    wk = week(3)
    rows = [ln for ln in out.splitlines() if "%d-W%02d" % (wk[0], wk[1]) in ln]
    assert rows and re.search(r"\|\s*\|\s*\|", rows[0])


def test_r044_usage_error_on_bad_weeks(tmp_path):
    """R-044. --weeks 0 is usage error exit 2."""
    p = MiniProject(tmp_path)
    p.commit("x (#1)", at(2))
    rc, out, _ = pace([p.root, "--weeks", "0"], tmp_path)
    assert rc == 2
    assert "|" not in out
