"""Release A4, the first review's findings that the other files do not cover: the scope check's base at
the brief's first commit and the supervisor's own records commits (F7), a `path`: note bullet read
(F17), a start-less timer and the rejected timers named (F8, F15), a Cargo version bump (F11), the
nearest tsconfig with a $schema URL (F12), `key DECIMAL (10,2)` (F20d), frame_drops (F16), the run
log's branch (F20b), a provider named only in a string noted (F20c)."""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_scope_check import brief, drift_list, git, repo, run as run_scope  # noqa: E402,F401
from test_diagram_check_a4 import make as make_diagram_repo, run as run_diagram  # noqa: E402
from test_lock_check import run as run_lock  # noqa: E402
from test_conformance_check import make_workspace, run as run_conf, verdict  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")


def test_the_base_stays_at_the_briefs_first_commit_and_records_commits_are_not_drift(repo):
    b = brief(repo, ["- src/core/a.py"])
    (repo / "src" / "other.py").write_text("O = 2\n", encoding="utf-8")
    env = dict(ENV, GIT_AUTHOR_NAME="builder", GIT_AUTHOR_EMAIL="builder@example.invalid", GIT_COMMITTER_NAME="builder", GIT_COMMITTER_EMAIL="builder@example.invalid")
    subprocess.run(["git", "add", "-A"], cwd=str(repo), check=True, env=env)
    subprocess.run(["git", "commit", "-q", "-m", "builder committed"], cwd=str(repo), check=True, env=env)
    (repo / "handoff" / "TASK-001.md").write_text((repo / "handoff" / "TASK-001.md").read_text(encoding="utf-8") + "\n(a note added later)\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "the brief fixed after the fact")
    rc, out = run_scope(repo, b)
    assert rc == 1 and "src/other.py" in drift_list(out) and "later commit" in out, "a brief committed again moved the base past the builder's commit (first pass, F7): " + out
    git(repo, "config", "user.email", "t@example.invalid")
    (repo / "docs" / "INVENTORY.md").write_text("| x |\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "records: the inventory")
    rc, out = run_scope(repo, b)
    assert "RECORDS (" in out and "docs/INVENTORY.md" not in drift_list(out) and "docs/INVENTORY.md" in out.split("RECORDS (")[1].split("\n")[0], "the supervisor's own records commit is not the builder's drift (first pass, F7): " + out
    (repo / "docs" / "REQUIREMENTS.md").write_text("| r |\n", encoding="utf-8")
    rc, out = run_scope(repo, b)
    assert "docs/REQUIREMENTS.md" in drift_list(out), "an uncommitted records change is still drift: " + out
    (repo / "src" / "core" / "b.py").write_text("B = 2\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "a builder's round: code and a record together")
    rc, out = run_scope(repo, b)
    assert "docs/REQUIREMENTS.md" in drift_list(out), "a commit mixing code with a record is the builder's, whatever its author (second pass, N1): " + out


def test_a_bold_note_and_sub_bullets_end_the_scope(repo):
    b = brief(repo, ["- src/core/a.py", "- src/core/b.py", "", "**Limits inside Scope:**", "- advance.py stays as it is", "- the registry is read only"])
    (repo / "src" / "core" / "a.py").write_text("A = 2\n", encoding="utf-8")
    rc, out = run_scope(repo, b)
    assert rc == 0 and "NOT READ AS A PATH" not in out and "advance.py" not in out.split("SCOPE:")[1].split("\n")[0], "the path list ends at the bold note (second pass, N8): " + out


def test_a_wrapped_bullet_continues_and_later_paths_stay(repo):
    b = brief(repo, ["- src/core/a.py, which holds the parser and", "  the tokenizer that goes with it", "- src/core/b.py"])
    (repo / "src" / "core" / "b.py").write_text("B = 2\n", encoding="utf-8")
    rc, out = run_scope(repo, b)
    assert rc == 0 and "src/core/b.py" in out.split("SCOPE:")[1].split("\n")[0], "an indented continuation line does not end the Scope (third pass, T2): " + out


def test_an_emphasised_note_after_a_plan_folder_is_not_a_path(program):
    pc = program("plan-check")
    assert pc.scope_paths("tests/service/ *(amended 2026-10-10: the service tests; see docs/CHANGES.md)*, src/x.py") == ["tests/service", "src/x.py"], "third pass, T4"


def test_the_plan_check_reads_a_brief_as_the_scope_check_does(program):
    pc = program("plan-check")
    text = "# TASK-023\n\n## Scope\n- src/a.py\n- A **cassette directory** (recommend\n  tests/cassettes/) for the replays\n- `src/b.py`: the writer\n\n**Limits:**\n- advance.py stays\n\n## Constraints\n- none\n"
    assert pc.brief_scope(text) == ["src/a.py", "src/b.py"], "a wrapped prose bullet yields no entry and the limits list is not scope (third pass, T7): " + str(pc.brief_scope(text))


def test_a_plan_scope_with_a_parenthesised_list_names_the_files(program):
    pc = program("plan-check")
    assert pc.scope_paths("tdp/ingest/normalize/ (located_build.py, azure_reader.py: the dropped strings), tdp/service/ (admin.py), tests/service/\u00a0, see docs/CHANGES.md") == \
        ["tdp/ingest/normalize/located_build.py", "tdp/ingest/normalize/azure_reader.py", "tdp/service/admin.py", "tests/service", "see docs/CHANGES.md"], "the TDP's form (second pass, N4)"


def test_a_built_row_needs_evidence_not_a_plan_increment(tmp_path):
    from test_completion_check import make, run as run_completion
    r = make(tmp_path)
    plan = (r / "docs" / "BUILD_PLAN.md").read_text(encoding="utf-8").replace("Satisfies: R-001, R-004", "Satisfies: R-001")
    (r / "docs" / "BUILD_PLAN.md").write_text(plan, encoding="utf-8")
    rc, out = run_completion(r, "--mode", "plan")
    assert "UNPLANNED: R-004" not in out, "a built row of a plan since removed is not UNPLANNED (second pass, N3): " + out


def test_a_quoted_path_with_a_note_is_read_and_an_unreadable_bullet_is_said(repo):
    b = brief(repo, ["- `src/core/a.py`: the handler", "- Only touch what is listed"])
    (repo / "src" / "core" / "a.py").write_text("A = 2\n", encoding="utf-8")
    rc, out = run_scope(repo, b)
    assert rc == 0 and "NOT READ AS A PATH: Only touch what is listed" in out, "first pass, F17: " + out


def test_a_startless_timer_bounds_and_rejected_timers_are_named(program):
    import time
    lg = program("loop-guard")
    now = time.time()
    agent = {"id": "a1", "type": "background_subagent", "status": "running", "description": 'Review "B" ($5)', "command": "Agent", "started_at": int((now - 600) * 1000)}
    timer = {"id": "t1", "type": "shell", "status": "running", "description": "timer", "command": 'python ~/.claude/cursor-bridge/wake-timer.py 3000 "a1"'}
    pending, unscheduled = lg.pending_from_hook({"background_tasks": [agent, timer], "session_crons": []}, now, ".")
    assert not unscheduled and "background agent a1" in pending, "a timer with no start counts when its seconds fit the ceiling (first pass, F8): " + str((pending, unscheduled))
    late = dict(timer, command='python ~/.claude/cursor-bridge/wake-timer.py 7200 "a1"', started_at=int((now - 100) * 1000))
    pending, unscheduled = lg.pending_from_hook({"background_tasks": [agent, late], "session_crons": []}, now, ".")
    assert len(unscheduled) == 1 and "t1 (ends at" in unscheduled[0] and 'wake-timer.py 3000 "a1"' in unscheduled[0], "the rejected timer is named and the printed command uses the id (first pass, F8, F15): " + unscheduled[0]


def test_a_cargo_version_bump_still_needs_its_lockfile(tmp_path):
    r = tmp_path / "ws"
    r.mkdir()
    (r / "Cargo.toml").write_text('[package]\nname = "thing"\nversion = "0.1.0"\n\n[dependencies]\nserde = "1"\n', encoding="utf-8")
    (r / "Cargo.lock").write_text("# lock\n", encoding="utf-8")
    for args in (["init", "-q", "-b", "main"], ["add", "-A"], ["commit", "-q", "-m", "base"]):
        subprocess.run(["git"] + args, cwd=str(r), check=True, env=ENV)
    (r / "Cargo.toml").write_text('[package]\nname = "thing"\nversion = "0.2.0"\n\n[dependencies]\nserde = "1"\n', encoding="utf-8")
    rc, out = run_lock(r)
    assert rc == 1 and "LOCKFILE MISSING" in out, "Cargo.lock records the root version, so a bump needs it (first pass, F11): " + out


def test_the_nearest_tsconfig_is_read_with_a_schema_url(tmp_path):
    r = make_diagram_repo(tmp_path, "frontend/ui/**", "frontend/store/**", {
        "frontend/tsconfig.json": json.dumps({"$schema": "https://json.schemastore.org/tsconfig", "extends": "./tsconfig.base.json", "compilerOptions": {"paths": {"@/*": ["./*"]}}}),
        "frontend/tsconfig.base.json": json.dumps({"compilerOptions": {"baseUrl": ".", "strict": True}}),
        "frontend/ui/view.ts": "import { keys } from '@/store/keys';\n",
        "frontend/store/keys.ts": "export const keys = {};\n",
        "app/service.ts": "export const s = 1;\n"})
    rc, out = run_diagram(r)
    assert rc == 1 and "IMPORT: frontend/ui/view.ts" in out, "reAngle's layout: frontend/tsconfig.json with @/* -> ./* (first pass, F12): " + out


def test_a_column_of_a_known_type_with_a_space_before_its_size_is_a_column(program):
    dc = program("diagram-check")
    assert dc.sql_schema("CREATE TABLE t (id INT, key DECIMAL (10,2), KEY idx (id));")["t"] == {"id", "key"}


def test_frame_drops_is_not_higher_is_better(program):
    bc = program("bench-check")
    assert bc.direction(None, "frame_drops") is None and bc.direction(None, "requests_per_s") == "higher" and bc.direction(None, "ops") == "higher"


def test_the_run_log_matches_the_builder_run_to_the_branch(tmp_path):
    prog = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "roster-check.py")
    roster = {"other_pool": "exhausted", "reset_day": 16, "review_a": "claude-opus-4-8",
              "profiles": [{"name": "full", "builder": "grok-4.7-high", "review_b": "gpt-5.6-sol-high"}, {"name": "native", "builder": "composer-2.5", "review_b": "grok-4.7-high"}]}
    (tmp_path / "ROSTER.json").write_text(json.dumps(roster), encoding="utf-8")
    for args in (["init", "-q", "-b", "task-002"], ["commit", "-q", "--allow-empty", "-m", "x"]):
        subprocess.run(["git"] + args, cwd=str(tmp_path), check=True, env=ENV)
    (tmp_path / "run" / "launcher").mkdir(parents=True)
    (tmp_path / "run" / "launcher" / "runs.jsonl").write_text(
        json.dumps({"id": "b1", "kind": "builder", "head": "cursor-agent", "model": "composer-2.5", "branch": "task-002", "limit": 7200, "seconds": 1, "exit": 0, "healthy": True}) + "\n"
        + json.dumps({"id": "b2", "kind": "builder", "head": "cursor-agent", "model": "grok-4.7-high", "branch": "task-003", "limit": 7200, "seconds": 1, "exit": 0, "healthy": True}) + "\n", encoding="utf-8")
    p = subprocess.run([sys.executable, prog, str(tmp_path / "ROSTER.json"), "--no-probe"], capture_output=True, text=True, cwd=str(tmp_path), env=ENV)
    assert p.returncode == 0 and "composer-2.5" in p.stdout.split("last builder run")[1].split("\n")[0], "the branch under review was built by composer, the later grok run is another branch's (first pass, F20b): " + p.stdout


def test_a_provider_named_only_in_a_string_is_noted(tmp_path):
    make_workspace(tmp_path)
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "judge.py").write_text('import httpx2\n\nPROVIDER = "openrouter"\n\ndef ask(q):\n    return httpx2.get("http://127.0.0.1:1")\n', encoding="utf-8")
    rc, out = run_conf(tmp_path)
    kind, detail = verdict(out, "Adapters named in a string only")
    assert kind == "NOTE" and "judge.py" in detail, "first pass, F20c: " + out
