"""loop-guard.py: which background work counts as a wake source (KP-031), where the status
file is found, and how its fields are read. Synthetic transcripts only."""
import json
import os
import time
from datetime import datetime, timezone

import pytest


@pytest.fixture
def lg(program):
    return program("loop-guard")


NOW = time.time()


def ts(offset=0):
    return datetime.fromtimestamp(NOW + offset, tz=timezone.utc).isoformat()


def write_transcript(tmp_path, cmd, tool="Bash", done=False, done_as="message"):
    lines = [
        {"timestamp": ts(-60), "message": {"role": "assistant", "content": [
            {"type": "tool_use", "id": "u1", "name": tool, "input": {"command": cmd, "run_in_background": True}}]}},
        {"timestamp": ts(-59), "toolUseResult": {"backgroundTaskId": "b1"},
         "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "u1", "content": "started"}]}},
    ]
    note = "<task-notification><task-id>b1</task-id><status>completed</status></task-notification>"
    if done and done_as == "message":
        lines.append({"timestamp": ts(-10), "message": {"role": "user", "content": [{"type": "text", "text": note}]}})
    elif done and done_as == "queue":
        lines.append({"timestamp": ts(-10), "type": "queue-operation", "operation": "enqueue", "content": note})
    elif done and done_as == "attachment":
        lines.append({"timestamp": ts(-10), "type": "attachment", "attachment": {"type": "queued_command", "prompt": note}})
    f = tmp_path / "t.jsonl"
    f.write_text("\n".join(json.dumps(o) for o in lines) + "\n", encoding="utf-8")
    return str(f)


@pytest.mark.parametrize("name,cmd,expect", [
    ("a dev server is not a wake source", "uv run --project backend reangle dev start > log 2>&1", False),
    ("docker compose up is not a wake source", "docker compose up -d", False),
    ("a builder run is a wake source", "cursor-agent -p --force --model grok-4.7-high \"Read handoff/TASK-001.md\" 2> run/agent/TASK-001.err", True),
    ("a builder run through bridge-run is a wake source", "python ~/.claude/cursor-bridge/bridge-run.py --limit 7200 -- cursor-agent -p --force --model x \"Read handoff/TASK-001.md\"", True),
    ("the CI watch is a wake source", "gh pr checks 62 --repo x/y --watch --required --fail-fast 2>&1 | tail -6", True),
    ("a marked command is a wake source", "python scratch/pgtest.py . # wake", True),
    ("the marker is case-insensitive", "python bench.py  #WAKE", True),
    ("an unmarked script is not a wake source", "python scratch/pgtest.py .", False),
])
def test_wake_sources(lg, tmp_path, name, cmd, expect):
    assert bool(lg.pending_wakeups(write_transcript(tmp_path, cmd), NOW)) == expect, name


def test_a_server_started_with_the_powershell_tool_is_not_a_wake_source(lg, tmp_path):
    assert not lg.pending_wakeups(write_transcript(tmp_path, "npm run dev", tool="PowerShell"), NOW)


@pytest.mark.parametrize("how", ["message", "queue", "attachment"])
def test_a_finished_task_is_not_pending_however_its_notice_arrived(lg, tmp_path, how):
    assert not lg.pending_wakeups(write_transcript(tmp_path, "cursor-agent -p --force x", done=True, done_as=how), NOW)


def test_a_background_agent_is_a_wake_source(lg, tmp_path):
    lines = [{"timestamp": ts(-60), "message": {"role": "assistant", "content": [
        {"type": "tool_use", "id": "u2", "name": "Agent", "input": {"prompt": "review", "run_in_background": True}}]}},
        {"timestamp": ts(-59), "toolUseResult": {"agentId": "a1", "isAsync": True},
         "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "u2", "content": "launched"}]}}]
    f = tmp_path / "t.jsonl"
    f.write_text("\n".join(json.dumps(o) for o in lines) + "\n", encoding="utf-8")
    assert lg.pending_wakeups(str(f), NOW)


def test_status_file_is_found_from_every_start_folder(lg, tmp_path):
    root = tmp_path
    (root / "Workspace" / "docs").mkdir(parents=True)
    (root / "Workspace" / "src").mkdir()
    (root / "Worktrees" / "TASK-012" / "docs").mkdir(parents=True)
    (root / "Workspace" / "docs" / "PROJECT_STATUS.md").write_text("**Phase:** building\n- Awaiting user on: none (nothing pending)\n", encoding="utf-8")
    (root / "Worktrees" / "TASK-012" / "docs" / "PROJECT_STATUS.md").write_text("Phase: planning\n", encoding="utf-8")
    for cwd in (root / "Workspace", root, root / "Worktrees" / "TASK-012", root / "Workspace" / "src"):
        status = lg.read_status(str(cwd))
        assert status is not None, cwd
        assert lg.field(status, "Phase") == "building", cwd
        assert lg.field(status, "Awaiting user on").startswith("none"), cwd


@pytest.mark.parametrize("text,value", [
    ("Phase: building (stage 2)", "building (stage 2)"),
    ("**Phase:** building", "building"),
    ("- Phase: `changing`", "changing"),
    ("* **Phase**: done", "done"),
])
def test_field_variants(lg, text, value):
    assert lg.field(text, "Phase") == value


def hook_input(root, tasks=None, crons=None, **more):
    data = {"cwd": str(root), "transcript_path": str(root / "none.jsonl"), "hook_event_name": "Stop"}
    if tasks is not None:
        data["background_tasks"] = tasks
    if crons is not None:
        data["session_crons"] = crons
    data.update(more)
    return data


def task(kind, command, age, status="running", tid="t1"):
    return {"id": tid, "type": kind, "status": status, "description": command[:30], "command": command, "started_at": ts(-age)}


@pytest.mark.parametrize("name,tasks,crons,allowed", [
    ("a running builder read from the hook's list", [task("command", "python ~/.claude/cursor-bridge/bridge-run.py --limit 7200 -- cursor-agent -p --force x", 600)], None, True),
    ("a builder past its limit plus grace no longer counts", [task("command", "python ~/.claude/cursor-bridge/bridge-run.py --limit 7200 -- cursor-agent -p --force x", 7200 + 601)], None, False),
    ("a server never counts", [task("command", "npm run dev", 60)], None, False),
    ("a completed task never counts", [task("command", "cursor-agent -p --force x", 60, status="completed")], None, False),
    ("a background agent under its ceiling with its wake-up scheduled", [task("background_subagent", "Agent", 600)], [{"id": "c1", "schedule": "7 * * * *", "description": "ceiling check", "command": "", "last_run_at": None, "next_run_at": ts(2900)}], True),
    ("a background agent with no wake-up scheduled is not a wake source (case 5)", [task("background_subagent", "Agent", 600)], [], False),
    ("a wake-up scheduled after the ceiling does not bound the agent: sent back (second pass, S1)", [task("background_subagent", "Agent", 600)], [{"id": "c1", "schedule": "x", "description": "", "command": "", "last_run_at": None, "next_run_at": ts(7200)}], False),
    ("a wake-up past due still fires when the session is idle", [], [{"id": "c1", "schedule": "x", "description": "", "command": "", "last_run_at": None, "next_run_at": ts(-300)}], True),
    ("a test suite through the launcher counts without # wake", [task("command", "python ~/.claude/cursor-bridge/bridge-run.py --limit auto --kind test -- pytest -q", 60)], None, True),
    ("a background agent past its ceiling (case 5)", [task("background_subagent", "Agent", 3601)], None, False),
    ("a scheduled wake-up still due", [], [{"id": "c1", "schedule": "7 * * * *", "description": "ceiling check", "command": "", "last_run_at": None, "next_run_at": ts(1800)}], True),
    ("an empty list means nothing is pending", [], [], False),
])
def test_the_guard_reads_what_is_in_flight_from_the_hook(lg, tmp_path, monkeypatch, capsys, name, tasks, crons, allowed):
    """Release A2 (plan 10.3): Claude Code's own list replaces the transcript reconstruction."""
    root = tmp_path / "proj" / "Workspace"
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "PROJECT_STATUS.md").write_text("Phase: building\nAwaiting user on: nothing\n", encoding="utf-8")
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO(json.dumps(hook_input(root, tasks, crons))))
    with pytest.raises(SystemExit) as e:
        lg.main()
    assert (e.value.code == 0) is allowed, (name, capsys.readouterr().err)


def test_the_agent_ceiling_can_be_raised_in_the_run_parameters(lg, tmp_path, monkeypatch):
    root = tmp_path / "proj" / "Workspace"
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "PROJECT_STATUS.md").write_text("Phase: building\nAwaiting user on: nothing\n", encoding="utf-8")
    (root / "docs" / "RUN_PARAMETERS.md").write_text("Merge authority: supervisor\nAgent ceiling: 7200\nCeiling above twice: builder 21600 (the owner: six hours, 2026-10-10)\n", encoding="utf-8")
    assert lg.agent_ceiling(str(root)) == 7200
    crons = [{"id": "c1", "schedule": "x", "description": "", "command": "", "last_run_at": None, "next_run_at": ts(2000)}]
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO(json.dumps(hook_input(root, [task("background_subagent", "Agent", 5000)], crons))))
    with pytest.raises(SystemExit) as e:
        lg.main()
    assert e.value.code == 0
    assert lg.command_ceiling("python ~/.claude/cursor-bridge/bridge-run.py --limit auto --kind builder -- cursor-agent -p x", str(root)) == 21600, "the owner's raised ceiling (finding 7)"
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO(json.dumps(hook_input(root, [task("command", "python ~/.claude/cursor-bridge/bridge-run.py --limit auto --kind builder -- cursor-agent -p x", 5 * 3600)]))))
    with pytest.raises(SystemExit) as e:
        lg.main()
    assert e.value.code == 0, "a builder five hours into a six-hour owner ceiling is still a wake source"


def test_an_agent_without_its_wake_up_is_sent_back_with_the_reason(lg, tmp_path, monkeypatch, capsys):
    root = tmp_path / "proj" / "Workspace"
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "PROJECT_STATUS.md").write_text("Phase: building\nAwaiting user on: nothing\n", encoding="utf-8")
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO(json.dumps(hook_input(root, [task("background_subagent", "Agent", 300)], []))))
    with pytest.raises(SystemExit) as e:
        lg.main()
    assert e.value.code == 2 and "CronCreate" in capsys.readouterr().err


def test_without_the_hook_list_the_transcript_is_read_as_before(lg, tmp_path, monkeypatch):
    root = tmp_path / "proj" / "Workspace"
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "PROJECT_STATUS.md").write_text("Phase: building\nAwaiting user on: nothing\n", encoding="utf-8")
    tp = write_transcript(tmp_path, "cursor-agent -p --force x")
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO(json.dumps({"cwd": str(root), "transcript_path": tp, "hook_event_name": "Stop"})))
    with pytest.raises(SystemExit) as e:
        lg.main()
    assert e.value.code == 0


def test_stop_hook_active_allows(lg, monkeypatch, capsys):
    import io, sys
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"stop_hook_active": True})))
    with pytest.raises(SystemExit) as e:
        lg.main()
    assert e.value.code == 0


def assistant_transcript(tmp_path, text):
    lines = [{"timestamp": ts(-30), "message": {"role": "assistant", "content": [{"type": "text", "text": "an earlier message with ```bash\nls\n```"}]}},
             {"timestamp": ts(-20), "message": {"role": "user", "content": [{"type": "text", "text": "ok"}]}},
             {"timestamp": ts(-10), "message": {"role": "assistant", "content": [{"type": "text", "text": text}]}}]
    f = tmp_path / "t.jsonl"
    f.write_text("\n".join(json.dumps(o) for o in lines) + "\n", encoding="utf-8")
    return str(f)


@pytest.mark.parametrize("text, sent_back", [
    ("Run this:\n\n```bash\npython tools/x.py\n```\n\nThen tell me.", True),
    ("Terminal: Git Bash (Start menu, type Git Bash)\n\n```bash\npython tools/x.py\n```\n\nReport back the last line.", False),
    ("**Terminal:** PowerShell (Start menu, type PowerShell)\n\n```powershell\nGet-Content x\n```", False),
    ("- **Terminal**: this chat\n\n```bash\n/supervisor\n```", False),
    ("1. Terminal: Git Bash (Start menu)\n2. Run:\n\n```bash\npython tools/x.py\n```", False),
    ("**2. Terminal:** PowerShell\n\n```powershell\nGet-Content x\n```", False),
    ("Terminal (Git Bash): open it from the Start menu\n\n```bash\nls\n```", False),
    ("10. Run:\n\n    ```bash\n    python tools/x.py\n    ```\n", True),
    ("Terminal output: all clean.\n\n```bash\npython tools/x.py\n```", True),
    ("Open PowerShell and run:\n\n```powershell\nGet-Content x\n```", True),
    ("1. Run:\n\n   ```bash\n   python tools/x.py\n   ```\n", True),
    ("Run:\n\n~~~ps1\nGet-Content x\n~~~\n", True),
    ("Run:\n\n```batch\ndir\n```\n", True),
    ("FYI: I ran this myself:\n\n```\npytest -q\n```\n\n2 passed.", False),
    ("FYI, in this chat I ran `pytest -q`: 2 passed.", False),
    ("Nothing needed — proceeding. Tests: 12 passed.", False),
    ("Here is the file:\n\n```python\nprint(1)\n```", False),
])
def test_a_run_sheet_without_its_terminal_is_sent_back(lg, tmp_path, text, sent_back):
    """Release A1b, rule 27: the last message holds a shell block and names no terminal."""
    assert lg.run_sheet_without_terminal(lg.last_assistant_text(assistant_transcript(tmp_path, text))) is sent_back


def test_the_run_sheet_check_reads_the_last_assistant_message_only(lg, tmp_path):
    tp = assistant_transcript(tmp_path, "Done. Nothing to run.")
    assert lg.last_assistant_text(tp) == "Done. Nothing to run."
    assert not lg.run_sheet_without_terminal(lg.last_assistant_text(tp)), "the earlier message's block does not count"


def test_the_run_sheet_check_applies_in_every_phase_and_blocks_the_stop(lg, tmp_path, monkeypatch, capsys):
    root = tmp_path / "proj" / "Workspace"
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "PROJECT_STATUS.md").write_text("Phase: configuration\nAwaiting user on: the owner's key\n", encoding="utf-8")
    tp = assistant_transcript(tmp_path, "Please run:\n\n```bash\npython setup.py\n```")
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO(json.dumps({"cwd": str(root), "transcript_path": tp, "hook_event_name": "Stop"})))
    with pytest.raises(SystemExit) as e:
        lg.main()
    assert e.value.code == 2 and "names no terminal" in capsys.readouterr().err
    tp = assistant_transcript(tmp_path, "Terminal: PowerShell.\n\n```powershell\npython setup.py\n```")
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO(json.dumps({"cwd": str(root), "transcript_path": tp, "hook_event_name": "Stop"})))
    with pytest.raises(SystemExit) as e:
        lg.main()
    assert e.value.code == 0, "configuration is not an active phase for the loop guard, and the run sheet is complete"
    # the hook's own copy of the final message is read first; the transcript (which may lag) is the fallback
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO(json.dumps({"cwd": str(root), "transcript_path": tp, "hook_event_name": "Stop",
                                                                           "last_assistant_message": "Please run:\n\n```bash\npython setup.py\n```"})))
    with pytest.raises(SystemExit) as e:
        lg.main()
    assert e.value.code == 2, "the hook's own copy of the final message wins over the transcript"


def test_the_refusal_prints_the_ceiling_on_the_computers_clock(lg, tmp_path, monkeypatch, capsys):
    """reAngle, 2026-10-10 (KP-039): wake-ups computed from a UTC stamp with an assumed offset landed an hour
    past the ceiling. The refusal prints the clock's reading, the ceiling's time and the schedule to copy, and
    names a wake-up that is due after the ceiling."""
    from datetime import datetime as dt
    root = tmp_path / "proj" / "Workspace"
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "PROJECT_STATUS.md").write_text("Phase: building\nAwaiting user on: nothing\n", encoding="utf-8")
    agent = {"id": "a1", "type": "background_subagent", "status": "running", "description": "Review A", "command": "Agent", "started_at": ts(-600)}
    late = dt.fromtimestamp(NOW - 600 + 3600 + 3600)
    cron = {"id": "c1", "schedule": "%d %d %d %d *" % (late.minute, late.hour, late.day, late.month), "description": "an hour late", "command": "", "last_run_at": None}
    pending, unscheduled = lg.pending_from_hook({"background_tasks": [agent], "session_crons": [cron]}, NOW, str(root))
    assert len(unscheduled) == 1 and "background agent a1" not in pending, (pending, unscheduled)   # the late wake-up is listed, the agent is not covered
    ceiling = dt.fromtimestamp(NOW - 600 + 3600)
    assert "`%d %d %d %d *`" % (ceiling.minute, ceiling.hour, ceiling.day, ceiling.month) in unscheduled[0] and ceiling.strftime("%Y-%m-%d %H:%M") in unscheduled[0], unscheduled[0]
    assert "after it" in unscheduled[0] and late.strftime("%H:%M") in unscheduled[0], unscheduled[0]
    assert "(UTC+" in unscheduled[0] or "(UTC-" in unscheduled[0], unscheduled[0]
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO(json.dumps({"cwd": str(root), "transcript_path": str(root / "none"), "hook_event_name": "Stop", "background_tasks": [agent], "session_crons": [cron]})))
    with pytest.raises(SystemExit) as e:
        lg.main()
    err = capsys.readouterr().err
    assert e.value.code == 2 and "The computer's clock reads" in err and "KP-039" in err and "never convert a UTC stamp" in err, err


def test_the_hook_input_is_read_in_its_live_forms(lg, tmp_path, monkeypatch):
    """reAngle, 2026-10-10 (field observation on 2026.10.10a): a start as epoch milliseconds, a one-shot
    cron with its schedule only, a command task under another type name."""
    assert abs(lg.parse_ts(int(NOW * 1000)) - NOW) < 1 and abs(lg.parse_ts(str(int(NOW))) - NOW) < 1 and lg.parse_ts("not a time") is None
    assert lg.parse_ts(ts(0)) is not None
    import datetime as dt
    local = dt.datetime.fromtimestamp(NOW + 1800)
    due = lg.cron_next("%d %d %d %d *" % (local.minute, local.hour, local.day, local.month), NOW)
    assert due is not None and abs(due - (NOW + 1800)) < 90, "a one-shot cron pinned to a local time"
    assert lg.cron_next("*/5 * * * *", NOW) is not None and lg.cron_next("nonsense", NOW) is None
    root = tmp_path / "proj" / "Workspace"
    (root / "docs").mkdir(parents=True)
    (root / "run").mkdir()
    (root / "docs" / "PROJECT_STATUS.md").write_text("Phase: building\nAwaiting user on: nothing\n", encoding="utf-8")
    agent = {"id": "a1", "type": "background_subagent", "status": "running", "description": "Review A", "command": "Agent", "started_at": int((NOW - 300) * 1000)}
    cron = {"id": "c1", "schedule": "%d %d %d %d *" % (local.minute, local.hour, local.day, local.month), "description": "ceiling", "command": "", "last_run_at": None}
    pending, unscheduled = lg.pending_from_hook({"background_tasks": [agent], "session_crons": [cron]}, NOW, str(root))
    assert pending and not unscheduled, (pending, unscheduled)
    old = dict(agent, started_at=int((NOW - 7200) * 1000))
    pending, unscheduled = lg.pending_from_hook({"background_tasks": [old], "session_crons": []}, NOW, str(root))
    assert not pending and not unscheduled, "past its ceiling: neither pending nor waiting for a wake-up"
    launched = {"id": "b1", "type": "shell", "status": "running", "description": "review", "command": "python ~/.claude/cursor-bridge/bridge-run.py --limit auto --kind review -- cursor-agent -p x", "started_at": ts(-60)}
    pending, unscheduled = lg.pending_from_hook({"background_tasks": [launched], "session_crons": []}, NOW, str(root))
    assert pending and not unscheduled, "a launched command is never an agent needing a wake-up"
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO(json.dumps({"cwd": str(root), "transcript_path": str(root / "none"), "hook_event_name": "Stop", "background_tasks": [launched], "session_crons": []})))
    with pytest.raises(SystemExit) as e:
        lg.main()
    assert e.value.code == 0
    recorded = json.loads((root / "run" / "supervisor" / "loop-guard-input.json").read_text(encoding="utf-8"))
    assert recorded["background_tasks"][0]["id"] == "b1" and "transcript_path" not in recorded, "the guard records what it decided from"
