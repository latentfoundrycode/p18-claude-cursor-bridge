"""Hotfix 2026.10.25a: the loop guard classes a background task by its tool (C2, TDP FB-006) and reads a
`Paused:` line in run/supervisor/in-flight.md as a wait (C12, FB-027); evaluate-reports.py shows an entry
written after a forced verdict, lists the bridge's own project with its Workspace's note key only, reads a
recurrence heading as an update (C1), and reads the status file's incidents still to write and states
UTC in the extract (C8 of 2026-10-18); compaction-baseline.py and the maintainer's token-usage.py read the
`-Workspace` transcript folders (C9 of 2026-10-18). Scratch projects, homes and ledgers only."""
import io
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
EVAL = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "evaluate-reports.py")
BASELINE = os.path.join(HERE, os.pardir, "tools", "compaction-baseline.py")
TOKEN_USAGE = os.environ.get("TOKEN_USAGE_PY") or r"E:\p18-claude-cursor-bridge\Reports\Maintainer\token-usage.py"   # the maintainer's own script, outside the repository
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
NOW = time.time()


def ts(offset=0):
    return datetime.fromtimestamp(NOW + offset, tz=timezone.utc).isoformat()


# ---------------------------------------------------------------- loop-guard.py
@pytest.fixture
def lg(program):
    return program("loop-guard")


def workspace(tmp_path, in_flight=None):
    root = tmp_path / "proj" / "Workspace"
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "PROJECT_STATUS.md").write_text("Phase: building\nAwaiting user on: nothing\n", encoding="utf-8")
    if in_flight is not None:
        (root / "run" / "supervisor").mkdir(parents=True)
        (root / "run" / "supervisor" / "in-flight.md").write_text(in_flight, encoding="utf-8")
    return root


def stop(lg, monkeypatch, root, tasks, transcript=None):
    data = {"cwd": str(root), "transcript_path": transcript or str(root / "none.jsonl"), "hook_event_name": "Stop"}
    if tasks is not None:
        data["background_tasks"] = tasks
        data["session_crons"] = []
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(data)))
    with pytest.raises(SystemExit) as e:
        lg.main()
    return e.value.code


# Claude Code's own form of the hook's list (2.1.308): a type name, no start time, a command for a shell task only.
MONITOR_WS = {"id": "sp3zauj11", "type": "monitor", "status": "running", "description": "artifact live update"}
MCP_TASK = {"id": "k1", "type": "MCP task", "status": "running", "description": "an MCP task", "server": "s", "tool": "t"}
SUBAGENT = {"id": "a1", "type": "subagent", "status": "running", "description": "Review A", "agent_type": "diff-reviewer"}
BUILDER = {"id": "b1", "type": "shell", "status": "running", "description": "builder",
           "command": "python ~/.claude/cursor-bridge/bridge-run.py --limit 7200 -- cursor-agent -p --force x"}


def test_c2_a_monitor_task_never_demands_a_wake_timer(lg, tmp_path, monkeypatch, capsys):
    """TDP FB-006 (2): an artifact live-update monitor (`monitor_ws`) was read as a background agent
    and a wake-timer demanded for it, three times on 2026-10-11."""
    root = workspace(tmp_path)
    pending, unscheduled = lg.pending_from_hook({"background_tasks": [MONITOR_WS], "session_crons": []}, NOW, str(root))
    assert not pending and not unscheduled, "a monitor is neither an agent nor a wake source: " + str((pending, unscheduled))
    pending, unscheduled = lg.pending_from_hook({"background_tasks": [MCP_TASK], "session_crons": []}, NOW, str(root))
    assert unscheduled, "a task with no command that is not a monitor (an MCP task, a workflow) finishes and notifies: it stays an agent, as before"
    assert stop(lg, monkeypatch, root, [MONITOR_WS]) == 2
    err = capsys.readouterr().err
    assert "KP-043" not in err and "wake-timer.py" not in err, "no wake-timer is demanded for a monitor: " + err
    assert stop(lg, monkeypatch, root, [MONITOR_WS, BUILDER]) == 0, "a running builder beside a monitor still allows the stop"


def test_c2_an_agent_task_is_still_timer_bound_and_a_shell_command_counts_by_its_pattern(lg, tmp_path):
    root = workspace(tmp_path)
    pending, unscheduled = lg.pending_from_hook({"background_tasks": [SUBAGENT], "session_crons": []}, NOW, str(root))
    assert len(unscheduled) == 1 and "wake-timer.py" in unscheduled[0], "an Agent task needs its timer, as before: " + str(unscheduled)
    pending, unscheduled = lg.pending_from_hook({"background_tasks": [SUBAGENT, MONITOR_WS], "session_crons": []}, NOW, str(root))
    assert len(unscheduled) == 1 and unscheduled[0].startswith("a1 "), "only the agent asks for a timer, never the monitor beside it: " + str(unscheduled)
    server = dict(BUILDER, id="s1", command="npm run dev")
    pending, unscheduled = lg.pending_from_hook({"background_tasks": [server, BUILDER], "session_crons": []}, NOW, str(root))
    assert pending == ["background command b1"] and not unscheduled, (pending, unscheduled)
    assert lg.task_class(MONITOR_WS) == "other" and lg.task_class(SUBAGENT) == "agent" and lg.task_class(BUILDER) == "shell"


def test_c2_a_monitor_tool_task_in_the_transcript_is_no_wake_source(lg, tmp_path):
    """The transcript fallback classes by the tool too: a Monitor tool's task never counts, even with a
    command that would count for the shell; an async Agent task still does."""
    def transcript(name, inp, result):
        lines = [{"timestamp": ts(-60), "message": {"role": "assistant", "content": [{"type": "tool_use", "id": "u1", "name": name, "input": inp}]}},
                 {"timestamp": ts(-59), "toolUseResult": result,
                  "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "u1", "content": "started"}]}}]
        p = tmp_path / ("%s.jsonl" % name)
        p.write_text("\n".join(json.dumps(o) for o in lines) + "\n", encoding="utf-8")
        return str(p)
    for result in ({"taskId": "m1"}, {"backgroundTaskId": "m1"}):
        tp = transcript("Monitor", {"command": "gh pr checks 5 --watch", "description": "checks", "timeout_ms": 1800000}, result)
        assert lg.pending_wakeups(tp, NOW) == [], "a Monitor task is no wake source: " + str(result)
    tp = transcript("Monitor", {"ws": {"url": "wss://example.invalid/s"}, "description": "frames", "timeout_ms": 1800000}, {"taskId": "m2"})
    assert lg.pending_wakeups(tp, NOW) == []
    tp = transcript("Agent", {"prompt": "review", "run_in_background": True}, {"agentId": "a9", "isAsync": True})
    assert lg.pending_wakeups(tp, NOW) == ["background task a9"]
    tp = transcript("Bash", {"command": "cursor-agent -p --force x", "run_in_background": True}, {"backgroundTaskId": "b9"})
    assert lg.pending_wakeups(tp, NOW) == ["background task b9"]


def test_c12_a_paused_line_in_the_in_flight_file_is_a_wait(lg, tmp_path, monkeypatch):
    """FB-027: a pause is written in the untracked run/supervisor/in-flight.md, so the tracked status file is not edited."""
    root = workspace(tmp_path, "In flight: TASK-031 r2\nPaused: on the owner's word (2026-10-25 09:00), resume on their message\n")
    assert stop(lg, monkeypatch, root, []) == 0, "a Paused: line names a wait"
    assert stop(lg, monkeypatch, root, [SUBAGENT]) == 0, "a pause allows the stop before any timer is asked for"
    for value in ("none", "nothing", "-", ""):
        (root / "run" / "supervisor" / "in-flight.md").write_text("In flight: TASK-031 r2\nPaused: %s\n" % value, encoding="utf-8")
        assert stop(lg, monkeypatch, root, []) == 2, "Paused: %r is no wait" % value
    (root / "run" / "supervisor" / "in-flight.md").write_text("**Paused:** the owner's pause\n", encoding="utf-8")
    assert stop(lg, monkeypatch, root, []) == 0, "the field is read in the status file's tolerant form"


# ---------------------------------------------------------------- evaluate-reports.py
ISSUES = """# Thing - Issues During Development and Their Solutions

## ISS-001 - The first issue
Context: the first.
"""
FEEDBACK = """# Thing - Claude-Cursor Bridge Feedback

## Stage 1 - Foundation (2026-10-01)

### FB-001 - A check fired wrongly
The loop guard sent back a report.

### FB-002 - Another
Something else.
"""
RECURRED = FEEDBACK + """
## Stage 2 - Later (2026-10-18)

### FB-001 (recurred 2026-10-18) - the check fired wrongly again
The same report, a week later.
"""


def project(tmp_path, issues=ISSUES, feedback=FEEDBACK, status=None):
    root = tmp_path / "proj"
    (root / "Documents").mkdir(parents=True, exist_ok=True)
    (root / "Workspace" / "docs").mkdir(parents=True, exist_ok=True)
    (root / "Documents" / "Thing Issues During Development and Their Solutions.md").write_text(issues, encoding="utf-8")
    (root / "Documents" / "Thing Claude-Cursor Bridge Feedback.md").write_text(feedback, encoding="utf-8")
    if status is not None:
        (root / "Workspace" / "docs" / "PROJECT_STATUS.md").write_text(status, encoding="utf-8")
    return root


def run(tmp_path, *args):
    p = subprocess.run([sys.executable, EVAL] + list(args), capture_output=True, text=True, cwd=str(tmp_path))
    return p.returncode, p.stdout + p.stderr


def common(tmp_path, root, name="Thing"):
    return ["--project-root", str(root), "--project-name", name, "--ledger", str(tmp_path / "ledger.json"), "--home", str(tmp_path / "home")]


def record_all(tmp_path, root, ids):
    for eid in ids:
        rc, out = run(tmp_path, "record", "Thing", eid, "project-specific", *common(tmp_path, root))
        assert rc == 0, out


def test_c1_an_entry_written_after_a_forced_verdict_is_shown_once_as_written(tmp_path):
    """2026-10-25 C1 (rows 12 to 15): the TDP wrote ISS-010 to ISS-013 after their verdicts were forced;
    the collector showed a changed entry only when the ledger held a fingerprint, so they never surfaced."""
    root = project(tmp_path)
    record_all(tmp_path, root, ("ISS-001", "FB-001", "FB-002"))
    rc, out = run(tmp_path, "record", "Thing", "ISS-002", "planned", "--reason", "C4 of 2026-10-18", "--force", *common(tmp_path, root))
    assert rc == 0, out
    rc, out = run(tmp_path, "collect", "--out", str(tmp_path / "out0"), *common(tmp_path, root))
    assert "nothing new" in out, "a forced entry not yet written is not raised: " + out
    (root / "Documents" / "Thing Issues During Development and Their Solutions.md").write_text(ISSUES + "\n## ISS-002 - The outage marked as a model's failure\nContext: written at the gate.\n", encoding="utf-8")
    rc, out = run(tmp_path, "collect", "--out", str(tmp_path / "out1"), *common(tmp_path, root))
    assert rc == 0 and "1 entries to evaluate (0 new, 0 updated, 1 written after a forced verdict)" in out, out
    text = (tmp_path / "out1" / "unprocessed.md").read_text(encoding="utf-8")
    assert "ISS-002 - WRITTEN (forced verdict: planned C4 of 2026-10-18)" in text and "written at the gate" in text, text
    rec = json.loads((tmp_path / "ledger.json").read_text(encoding="utf-8"))["Thing/ISS-002"]
    assert rec["fingerprint"] and rec["outcome"] == "planned", "its fingerprint is taken on its first appearance: " + str(rec)
    rc, out = run(tmp_path, "collect", "--out", str(tmp_path / "out2"), *common(tmp_path, root))
    assert "nothing new" in out, "shown once: " + out
    (root / "Documents" / "Thing Issues During Development and Their Solutions.md").write_text(ISSUES + "\n## ISS-002 - The outage marked as a model's failure\nContext: written at the gate, then amended.\n", encoding="utf-8")
    rc, out = run(tmp_path, "collect", "--out", str(tmp_path / "out3"), *common(tmp_path, root))
    assert "(0 new, 1 updated)" in out and "ISS-002 - UPDATED (earlier: planned" in (tmp_path / "out3" / "unprocessed.md").read_text(encoding="utf-8"), out


def test_c1_the_bridge_project_is_listed_and_read_from_its_workspace_key_only(program, tmp_path):
    """2026-10-25 C1 (row 76): the bridge's own project is a report source; the root's key
    (`E--p18-claude-cursor-bridge`) is the maintainer's own and never one."""
    er = program("evaluate-reports")
    assert os.path.normcase(er.PROJECTS["Bridge"]) == os.path.normcase(r"E:\p18-claude-cursor-bridge")
    assert er.project_keys("Bridge", er.PROJECTS["Bridge"]) == ["E--p18-claude-cursor-bridge-Workspace"]
    assert er.project_keys("TDP", er.PROJECTS["TDP"]) == ["E--p19-technical-documentation-provider", "E--p19-technical-documentation-provider-Workspace"]
    for name in ("Claude-Cursor Bridge Issues During Development and Their Solutions.md", "Claude-Cursor Bridge Claude-Cursor Bridge Feedback.md"):
        assert name.endswith(er.ISSUES_SUFFIX) or name.endswith(er.FEEDBACK_SUFFIX), name
    home = tmp_path / "home"
    for key, note in (("E--p18-claude-cursor-bridge", "maintainer-rule.md"), ("E--p18-claude-cursor-bridge-Workspace", "pause-for-fable.md")):
        (home / ".claude" / "projects" / key / "memory").mkdir(parents=True)
        (home / ".claude" / "projects" / key / "memory" / note).write_text("a note\n", encoding="utf-8")
        (home / ".claude" / "projects" / key / "s.jsonl").write_text("", encoding="utf-8")
    assert [e[0] for e in er.notes_entries(er.PROJECTS["Bridge"], str(home), "Bridge")] == ["note:pause-for-fable.md"]
    assert [os.path.basename(os.path.dirname(p)) for p in er.session_files(er.PROJECTS["Bridge"], str(home), "Bridge")] == ["E--p18-claude-cursor-bridge-Workspace"]
    root = project(tmp_path)                                       # the hand collect's form: any root, named Bridge
    key = er.project_key(str(root))
    for k, note in ((key, "root-note.md"), (key + "-Workspace", "workspace-note.md")):
        (home / ".claude" / "projects" / k / "memory").mkdir(parents=True)
        (home / ".claude" / "projects" / k / "memory" / note).write_text("a note\n", encoding="utf-8")
    rc, out = run(tmp_path, "collect", "--out", str(tmp_path / "out"), *common(tmp_path, root, "Bridge"))
    text = (tmp_path / "out" / "unprocessed.md").read_text(encoding="utf-8")
    assert "note:workspace-note.md" in text and "note:root-note.md" not in text, text


def test_c1_a_recurrence_heading_is_an_update_of_its_entry(program, tmp_path):
    """2026-10-25 C1: `### FB-001 (recurred 2026-10-18)` was a second entry under the key FB-001."""
    er = program("evaluate-reports")
    entries = er.feedback_entries(RECURRED)
    ids = [e[0] for e in entries]
    assert ids.count("FB-001") == 1 and "FB-002" in ids, ids
    body = [e for e in entries if e[0] == "FB-001"][0][2]
    assert "The loop guard sent back a report." in body and "recurred 2026-10-18" in body and "a week later" in body, body
    assert er.outside(RECURRED, entries) == er.outside(FEEDBACK, er.feedback_entries(FEEDBACK)) + 1, "nothing lost (the stage heading is outside)"
    root = project(tmp_path)
    record_all(tmp_path, root, ("ISS-001", "FB-001", "FB-002"))
    (root / "Documents" / "Thing Claude-Cursor Bridge Feedback.md").write_text(RECURRED, encoding="utf-8")
    rc, out = run(tmp_path, "collect", "--out", str(tmp_path / "out"), *common(tmp_path, root))
    assert rc == 0 and "1 entries to evaluate (0 new, 1 updated)" in out, out
    rc, out = run(tmp_path, "record", "Thing", "FB-001", "planned", "--reason", "C2", *common(tmp_path, root))
    rc, out = run(tmp_path, "collect", "--out", str(tmp_path / "out2"), *common(tmp_path, root))
    assert "nothing new" in out, "one fingerprint for the entry and its recurrence: " + out


STATUS = ("Phase: paused\n"
          "Open issues: ISS-001 fixed; ISS-015 to write at the next reflection (PR #203 round 1: Review B left a diff excerpt; "
          "the round void); ISS-011 repeated 2026-10-19 (#203's subject ended \"(R-103, TASK-168; R-104 recorded)\"); "
          "an ISS to write at the next reflection for the 2026-10-19 crash (the killed driver left mutant M6, KP-056)\n"
          "Awaiting user on: the owner's pause\n")


def test_c8_the_status_files_incidents_to_write_are_shown_and_the_extract_says_utc(tmp_path):
    """2026-10-18 C8 (entries 22 to 25, 31): five of that run's costliest entries were on a status file's
    `Open issues:` line, named as still to write."""
    root = project(tmp_path, status=STATUS)
    record_all(tmp_path, root, ("ISS-001", "FB-001", "FB-002"))
    rc, out = run(tmp_path, "collect", "--out", str(tmp_path / "out"), *common(tmp_path, root))
    assert rc == 0 and "Thing status: 2 incident(s)" in out and "2 entries to evaluate (0 new, 0 updated, 2 to write)" in out, out
    text = (tmp_path / "out" / "unprocessed.md").read_text(encoding="utf-8")
    assert "status / status:ISS-015 - TO WRITE" in text and "Review B left a diff excerpt" in text, text
    assert text.count("TO WRITE") == 2 and "2026-10-19 crash" in text and "R-104 recorded" not in text, "only the parts named as to write: " + text
    crash = [l.split(" / ")[2].split(" - ")[0] for l in text.splitlines() if l.startswith("## ") and "ISS-015" not in l][0]
    rc, out = run(tmp_path, "record", "Thing", crash, "planned", "--reason", "release B stage B5", *common(tmp_path, root))
    assert rc == 0, "a status-line incident is recorded like an entry, without --force: " + out
    (root / "Documents" / "Thing Issues During Development and Their Solutions.md").write_text(ISSUES + "\n## ISS-015 - The reviewer wrote under run/review/\nContext: the round void.\n", encoding="utf-8")
    rc, out = run(tmp_path, "collect", "--out", str(tmp_path / "out2"), *common(tmp_path, root))
    assert "1 entries to evaluate (1 new, 0 updated)" in out and "status:ISS-015" not in (tmp_path / "out2" / "unprocessed.md").read_text(encoding="utf-8"), \
        "once written, the Issues entry is the source: " + out
    key = str(root).replace(":", "-").replace("\\", "-").replace("/", "-")
    folder = tmp_path / "home" / ".claude" / "projects" / key
    folder.mkdir(parents=True)
    (folder / "s.jsonl").write_text(json.dumps({"type": "user", "uuid": "u1", "timestamp": "2026-10-20T14:31:00Z", "origin": {"kind": "human"},
                                                "message": {"role": "user", "content": "Resume."}}) + "\n", encoding="utf-8")
    rc, out = run(tmp_path, "extract", "--since", "2026-10-18", "--out", str(tmp_path / "ext"), *common(tmp_path, root))
    head = (tmp_path / "ext" / "owner-messages-Thing.md").read_text(encoding="utf-8").split("\n- ")[0]
    assert rc == 0 and "Times are UTC" in head, head


# ---------------------------------------------------------------- the -Workspace transcript folders (C9 of 2026-10-18)
def fake_home(tmp_path):
    home = tmp_path / "fakehome"
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home))
    return home, env


def test_c9_compaction_baseline_reads_the_workspace_folder(tmp_path):
    home, env = fake_home(tmp_path)
    marker = {"type": "system", "subtype": "compact_boundary", "uuid": "c1", "timestamp": "2026-10-20T10:00:00Z", "sessionId": "s1", "compactMetadata": {"trigger": "auto"}}
    for key in ("E--p19-technical-documentation-provider-Workspace", "E--p19-technical-documentation-provider"):
        (home / ".claude" / "projects" / key).mkdir(parents=True)
    (home / ".claude" / "projects" / "E--p19-technical-documentation-provider-Workspace" / "a.jsonl").write_text(json.dumps(marker) + "\n", encoding="utf-8")
    second = dict(marker, uuid="c2", timestamp="2026-10-21T10:00:00Z")          # copied into both folders by a resume
    (home / ".claude" / "projects" / "E--p19-technical-documentation-provider-Workspace" / "c.jsonl").write_text(json.dumps(second) + "\n", encoding="utf-8")
    (home / ".claude" / "projects" / "E--p19-technical-documentation-provider" / "b.jsonl").write_text(json.dumps(second) + "\n", encoding="utf-8")
    p = subprocess.run([sys.executable, BASELINE, "--since", "2026-10-12", "--projects", "E--p19-technical-documentation-provider:TDP"],
                       capture_output=True, text=True, env=env)
    assert p.returncode == 0 and "2026-10-20  1" in p.stdout and "2026-10-21  1" in p.stdout and "all projects: before 0, after 2" in p.stdout, \
        "the -Workspace folder counts with the project's other, a marker in both once: " + p.stdout + p.stderr


def test_c9_token_usage_reads_the_workspace_folder(tmp_path):
    """The maintainer's own script, outside the repository: loaded by its absolute path, skipped where it is absent (CI)."""
    if not os.path.isfile(TOKEN_USAGE):
        pytest.skip("the maintainer's token-usage.py is not on this computer")
    home, env = fake_home(tmp_path)
    folder = home / ".claude" / "projects" / "E--p19-technical-documentation-provider-Workspace"
    folder.mkdir(parents=True)
    rec = {"type": "assistant", "timestamp": "2026-10-20T10:00:00Z", "sessionId": "abcdef12", "requestId": "r1",
           "message": {"id": "m1", "model": "claude-x", "usage": {"input_tokens": 1000, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 2000000, "output_tokens": 500}}}
    (folder / "a.jsonl").write_text(json.dumps(rec) + "\n", encoding="utf-8")
    p = subprocess.run([sys.executable, TOKEN_USAGE, "--since", "2026-10-12"], capture_output=True, text=True, env=env)
    assert p.returncode == 0 and "TDP" in p.stdout and "requests 1" in p.stdout, p.stdout + p.stderr
