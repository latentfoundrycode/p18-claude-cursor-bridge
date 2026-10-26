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
    ("a builder past its limit plus grace no longer counts", [task("command", "python ~/.claude/cursor-bridge/bridge-run.py --limit 7200 -- cursor-agent -p --force x", 7200 + 14400 + 120 + 60 + 601)], None, False),
    ("a server never counts", [task("command", "npm run dev", 60)], None, False),
    ("a completed task never counts", [task("command", "cursor-agent -p --force x", 60, status="completed")], None, False),
    ("a background agent under its ceiling with its timer running (KP-043)", [task("background_subagent", "Agent", 600), task("command", 'python ~/.claude/cursor-bridge/wake-timer.py 3000 "Agent"', 600, tid="t2")], [], True),
    ("a background agent with only a scheduled wake-up is not bounded (KP-043)", [task("background_subagent", "Agent", 600)], [{"id": "c1", "schedule": "7 * * * *", "description": "ceiling check", "command": "", "last_run_at": None, "next_run_at": ts(2900)}], False),
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
    timer = task("command", 'python ~/.claude/cursor-bridge/wake-timer.py 7200 "Agent"', 5000, tid="t2")   # ends at the raised ceiling (KP-043)
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO(json.dumps(hook_input(root, [task("background_subagent", "Agent", 5000), timer], []))))
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
    """reAngle, 2026-10-10 (KP-039) and 2026-10-11 (KP-043, ISS-021): a scheduled wake-up cannot bound a background
    agent, because it does not fire while one runs; the bound is a wake-timer command. The refusal prints the clock's
    reading, the ceiling's time and the timer command to copy, and says why the scheduled wake-up is not the bound."""
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
    assert "wake-timer.py 3000" in unscheduled[0] and ceiling.strftime("%Y-%m-%d %H:%M") in unscheduled[0], unscheduled[0]
    assert "(UTC+" in unscheduled[0] or "(UTC-" in unscheduled[0], unscheduled[0]
    assert "cannot fire while a background agent runs" in unscheduled[0] and late.strftime("%H:%M") in unscheduled[0], unscheduled[0]
    timer = {"id": "t1", "type": "shell", "status": "running", "description": "ceiling timer", "command": 'python ~/.claude/cursor-bridge/wake-timer.py 3000 "Review A"', "started_at": ts(-600)}
    pending, unscheduled = lg.pending_from_hook({"background_tasks": [agent, timer], "session_crons": []}, NOW, str(root))
    assert not unscheduled and "background agent a1" in pending and "wake-timer t1" in pending, "a running timer that ends at the ceiling is the bound (KP-043): " + str((pending, unscheduled))
    short = dict(timer, command='python ~/.claude/cursor-bridge/wake-timer.py 7200 "Review A"')
    pending, unscheduled = lg.pending_from_hook({"background_tasks": [agent, short], "session_crons": []}, NOW, str(root))
    assert len(unscheduled) == 1, "a timer that ends after the ceiling is no bound: " + str((pending, unscheduled))
    waiter = {"id": "w1", "type": "shell", "status": "running", "description": "poll", "command": "until grep -q ^exit out.txt; do sleep 15; done", "started_at": ts(-60)}
    pending, unscheduled = lg.pending_from_hook({"background_tasks": [waiter], "session_crons": []}, NOW, str(root))
    assert not pending and not unscheduled and lg.WAITERS == ["w1"], "a leftover polling loop never counts: " + str((pending, unscheduled, lg.WAITERS))
    near = dict(agent, started_at=ts(-3600 + 30))
    pending, unscheduled = lg.pending_from_hook({"background_tasks": [near], "session_crons": []}, NOW, str(root))
    assert len(unscheduled) == 1 and "TaskStop now" in unscheduled[0] and "CronCreate" not in unscheduled[0], "a ceiling at hand is stopped, not scheduled (review of 10c, finding 1): " + str(unscheduled)
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO(json.dumps({"cwd": str(root), "transcript_path": str(root / "none"), "hook_event_name": "Stop", "background_tasks": [agent], "session_crons": [cron]})))
    with pytest.raises(SystemExit) as e:
        lg.main()
    err = capsys.readouterr().err
    assert e.value.code == 2 and "The computer's clock reads" in err and "KP-043" in err and "wake-timer" in err, err


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
    timer = {"id": "t2", "type": "shell", "status": "running", "description": "ceiling timer", "command": 'python ~/.claude/cursor-bridge/wake-timer.py 3300 "Review A"', "started_at": int((NOW - 300) * 1000)}
    pending, unscheduled = lg.pending_from_hook({"background_tasks": [agent, timer], "session_crons": [cron]}, NOW, str(root))
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


def test_bug020_a_one_shot_in_the_repeated_hour_is_found(lg):
    """BUG-020 (docs/debug/BUG-020.md, ISS-014): `cron_next` walks instants, not wall-clock minutes, so a
    one-shot schedule in the hour the clock repeats when summer time ends is found at its second
    occurrence, the first occurrence still before the fold is found as itself, a time after the fold
    is right, and after clocks go forward a wall time past the gap is right. The zone is named through
    `tz` (the computer's local zone when it is None), so the case runs at any hour on any computer
    that has the zone data. Europe/Berlin: 2026-10-25 01:00 UTC clocks go from 03:00 back to 02:00;
    2027-03-28 01:00 UTC from 02:00 forward to 03:00."""
    zoneinfo = pytest.importorskip("zoneinfo")
    try:
        berlin = zoneinfo.ZoneInfo("Europe/Berlin")
    except zoneinfo.ZoneInfoNotFoundError:
        pytest.skip("no zone data on this computer")

    def utc(text):
        return datetime.fromisoformat(text).replace(tzinfo=timezone.utc).timestamp()

    autumn = utc("2026-10-25T00:35:00")  # 02:35 local summer time, before the fold
    assert lg.cron_next("9 2 25 10 *", autumn, tz=berlin) == utc("2026-10-25T01:09:00")   # 02:09 the second time
    assert lg.cron_next("49 2 25 10 *", autumn, tz=berlin) == utc("2026-10-25T00:49:00")  # 02:49 the first time
    assert lg.cron_next("9 3 25 10 *", autumn, tz=berlin) == utc("2026-10-25T02:09:00")   # 03:09 standard time
    spring = utc("2027-03-28T00:30:00")  # 01:30 local standard time, before the gap
    assert lg.cron_next("30 3 28 3 *", spring, tz=berlin) == utc("2027-03-28T01:30:00")   # 03:30 summer time
    assert lg.cron_next("45 1 28 3 *", spring, tz=berlin) == utc("2027-03-28T00:45:00")   # 01:45 before the gap


def test_r040_driver_auto_ceiling_is_not_the_test_fallback(lg, tmp_path):
    """R-040: --limit auto --kind driver uses the driver's ceiling, not the test fallback."""
    root = tmp_path / "proj" / "Workspace"
    (root / "docs").mkdir(parents=True)
    cmd = "python ~/.claude/cursor-bridge/bridge-run.py --limit auto --kind driver -- python x.py"
    assert lg.command_ceiling(cmd, str(root)) == 14400


def test_r040_heavy_launch_count_includes_slot_wait(lg, tmp_path):
    """R-040: a launched heavy bridge-run command counts through slot wait, grace, report and launcher grace."""
    root = tmp_path / "proj" / "Workspace"
    (root / "docs").mkdir(parents=True)
    driver = "python ~/.claude/cursor-bridge/bridge-run.py --limit auto --kind driver -- python x.py"
    builder = "python ~/.claude/cursor-bridge/bridge-run.py --limit 7200 -- cursor-agent -p --force x"
    testcmd = "python ~/.claude/cursor-bridge/bridge-run.py --limit auto --kind test -- pytest -q"
    review = "python ~/.claude/cursor-bridge/bridge-run.py --limit auto --kind review -- cursor-agent -p x"
    wake = "python scratch/pgtest.py . # wake"
    assert lg.command_ceiling(driver, str(root)) + lg.heavy_launch_extra(driver) + lg.GRACE_SECONDS == 29580
    assert lg.command_ceiling(builder, str(root)) + lg.heavy_launch_extra(builder) + lg.GRACE_SECONDS == 22380
    assert lg.command_ceiling(testcmd, str(root)) + lg.heavy_launch_extra(testcmd) + lg.GRACE_SECONDS == 18780
    assert lg.heavy_launch_extra(review) == 0
    assert lg.heavy_launch_extra(wake) == 0
    tasks = [task("command", driver, 29579)]
    pending, _ = lg.pending_from_hook({"background_tasks": tasks, "session_crons": []}, NOW, str(root))
    assert pending
    tasks[0]["started_at"] = ts(-29581)
    pending, _ = lg.pending_from_hook({"background_tasks": tasks, "session_crons": []}, NOW, str(root))
    assert not pending


def test_bug021_the_clock_change_edges_of_cron_next(lg):
    """Stage B4's review, round 1 (Review A's briefs and programs parts, converging; docs/HARDENING.md, Stage B4):
    from inside the repeated hour, a one-shot later in it is found at its second occurrence, not an hour early
    (docs/debug/BUG-020.md, Evidence); a one-shot in the hour clocks skip is found at no time and a daily schedule
    in it fires the next day, the model of Claude Code's own scheduler the walk assumes (recorded with its check);
    a cron with no time found still counts as a pending wake-up; and the eight-day bound is exact."""
    zoneinfo = pytest.importorskip("zoneinfo")
    try:
        berlin = zoneinfo.ZoneInfo("Europe/Berlin")
    except zoneinfo.ZoneInfoNotFoundError:
        pytest.skip("no zone data on this computer")

    def utc(text):
        return datetime.fromisoformat(text).replace(tzinfo=timezone.utc).timestamp()

    inside = utc("2026-10-25T01:20:00")  # 02:20 local standard time, the second time
    assert lg.cron_next("50 2 25 10 *", inside, tz=berlin) == utc("2026-10-25T01:50:00")  # not 00:50, an hour early
    assert lg.cron_next("10 2 25 10 *", inside, tz=berlin) is None                       # both 02:10s have passed
    spring = utc("2027-03-28T00:30:00")  # 01:30 local standard time, before the gap
    assert lg.cron_next("30 2 28 3 *", spring, tz=berlin) is None                         # 02:30 does not exist that day
    assert lg.cron_next("30 2 * * *", spring, tz=berlin) == utc("2027-03-29T00:30:00")    # the next day's 02:30
    start = utc("2026-11-02T10:00:30")
    assert lg.cron_next("0 10 10 11 *", start, tz=timezone.utc) == utc("2026-11-10T10:00:00")  # the last minute searched
    assert lg.cron_next("1 10 10 11 *", start, tz=timezone.utc) is None                          # one minute past it
    assert lg.cron_next("30 2 30 2 *", NOW) is None, "the precondition: no time is found for 30 February"
    pending, unscheduled = lg.pending_from_hook({"background_tasks": [], "session_crons": [{"id": "c9", "schedule": "30 2 30 2 *"}]}, NOW, ".")
    assert pending == ["scheduled wake-up c9"] and not unscheduled, (pending, unscheduled)
