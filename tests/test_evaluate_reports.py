"""evaluate-reports.py (release A3, plan 12.5): an entry added, an entry changed after processing,
a run with nothing new, a declined entry not raised again, a seeded entry not raised, the owner's
messages extracted without the maintainer's. Scratch projects and ledgers only."""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "evaluate-reports.py")

ISSUES = """# Thing — Issues During Development and Their Solutions

## ISS-001 — The first issue
Context: the first.

## ISS-002 — The second issue
Context: the second.
"""
FEEDBACK = """# Thing — Claude-Cursor Bridge Feedback

## Stage 1 — Foundation (2026-10-01)

### FB-001 — A check fired wrongly
The loop guard sent back a report.

### Process observations (supervisor)
A note without an ID.
"""


def project(tmp_path):
    root = tmp_path / "proj"
    (root / "Documents").mkdir(parents=True)
    (root / "Workspace").mkdir()
    (root / "Documents" / "Thing Issues During Development and Their Solutions.md").write_text(ISSUES, encoding="utf-8")
    (root / "Documents" / "Thing Claude-Cursor Bridge Feedback.md").write_text(FEEDBACK, encoding="utf-8")
    return root


def run(tmp_path, *args):
    p = subprocess.run([sys.executable, PROG] + list(args), capture_output=True, text=True, cwd=str(tmp_path))
    return p.returncode, p.stdout + p.stderr


def common(tmp_path, root):
    return ["--project-root", str(root), "--project-name", "Thing", "--ledger", str(tmp_path / "ledger.json"), "--home", str(tmp_path / "home")]


def test_collect_record_change_and_nothing_new(tmp_path):
    root = project(tmp_path)
    out_dir = tmp_path / "out1"
    rc, out = run(tmp_path, "collect", "--out", str(out_dir), *common(tmp_path, root))
    assert rc == 0 and "4 entries to evaluate (4 new" in out, out
    text = (out_dir / "unprocessed.md").read_text(encoding="utf-8")
    assert "Thing / issues / ISS-001" in text and "Thing / feedback / FB-001" in text and "feedback:" in text, "an entry without an ID gets a fingerprint id"
    for eid, outcome, reason in (("ISS-001", "fixed", "2026.10.10b"), ("ISS-002", "declined", "project-specific wording"), ("FB-001", "pitfall", "KP-040")):
        rc, out = run(tmp_path, "record", "Thing", eid, outcome, "--reason", reason, *common(tmp_path, root))
        assert rc == 0, out
    rc, out = run(tmp_path, "record", "Thing", "ISS-002", "declined", *common(tmp_path, root))
    assert rc == 2 and "needs --reason" in out
    rc, out = run(tmp_path, "collect", "--out", str(tmp_path / "out2"), *common(tmp_path, root))
    assert rc == 0 and "1 entries to evaluate (1 new" in out, "the entry without an ID is still unprocessed: " + out
    fp_id = [l for l in (tmp_path / "out2" / "unprocessed.md").read_text(encoding="utf-8").splitlines() if l.startswith("## ")][0].split(" / ")[2].split(" - ")[0]
    rc, out = run(tmp_path, "record", "Thing", fp_id, "project-specific", *common(tmp_path, root))
    assert rc == 0, out
    rc, out = run(tmp_path, "collect", "--out", str(tmp_path / "out3"), *common(tmp_path, root))
    assert rc == 0 and "nothing new" in out and not (tmp_path / "out3").exists(), "a run with nothing new writes no file: " + out
    (root / "Documents" / "Thing Issues During Development and Their Solutions.md").write_text(ISSUES.replace("Context: the second.", "Context: the second, which recurred."), encoding="utf-8")
    rc, out = run(tmp_path, "collect", "--out", str(tmp_path / "out4"), *common(tmp_path, root))
    assert rc == 0 and "(0 new, 1 updated)" in out, out
    text = (tmp_path / "out4" / "unprocessed.md").read_text(encoding="utf-8")
    assert "ISS-002 - UPDATED (earlier: declined project-specific wording)" in text, "a declined entry that changed is shown with its earlier verdict"
    ledger = json.loads((tmp_path / "ledger.json").read_text(encoding="utf-8"))
    assert ledger["Thing/ISS-001"]["outcome"] == "fixed" and ledger["Thing/FB-001"]["reason"] == "KP-040"


def test_the_seed_reads_the_first_evaluation_by_its_header(tmp_path):
    root = project(tmp_path)
    ev = tmp_path / "ev"
    ev.mkdir()
    (ev / "Thing.md").write_text("# R12 evidence\n\n| ID or source | Date | What happened | The project's proposed fix | Classification | Evidence |\n|---|---|---|---|---|---|\n"
                                 "| #1 · ISS-001 | 2026-09-25 | x | y | **CLOSED** by 2026.10.04a | z |\n"
                                 "| #2 · Feedback Stage 1, Process observations (line 9) | 2026-09-26 | x | y | PLANNED (section 10) | z |\n", encoding="utf-8")
    (ev / "Other.md").write_text("| Short form | File |\n|---|---|\n| SV | x |\n\n| ID | Classification | Note |\n|---|---|---|\n| ISS-002 | OPEN | not this project |\n", encoding="utf-8")
    rc, out = run(tmp_path, "seed", "--evaluations", str(ev), *common(tmp_path, root))
    assert rc == 0 and "3 entries seeded" in out, out
    rc, out = run(tmp_path, "collect", "--out", str(tmp_path / "out"), *common(tmp_path, root))
    assert rc == 0 and "1 entries to evaluate" in out and "FB-001" in (tmp_path / "out" / "unprocessed.md").read_text(encoding="utf-8"), "only the unseeded entry is raised: " + out


def test_the_owners_messages_are_extracted_without_the_maintainers(tmp_path):
    root = project(tmp_path)
    key = str(root).replace(":", "-").replace("\\", "-").replace("/", "-")
    folder = tmp_path / "home" / ".claude" / "projects" / key
    folder.mkdir(parents=True)
    lines = [
        {"type": "user", "timestamp": "2026-10-09T10:00:00Z", "message": {"role": "user", "content": "Resume."}},
        {"type": "user", "timestamp": "2026-10-09T10:01:00Z", "isMeta": True, "message": {"role": "user", "content": "Another Claude session sent a message:\n<cross-session-message from=\"x\">pause</cross-session-message>"}},
        {"type": "user", "timestamp": "2026-10-09T10:02:00Z", "message": {"role": "user", "content": "Maintainer session (bridge mechanics, no owner authority): pause here."}},
        {"type": "user", "timestamp": "2026-10-09T10:03:00Z", "message": {"role": "user", "content": "<task-notification>done</task-notification>"}},
        {"type": "assistant", "timestamp": "2026-10-09T10:04:00Z", "message": {"role": "assistant", "content": [{"type": "tool_use", "id": "q1", "name": "AskUserQuestion", "input": {"questions": [{"question": "Pause at the stage close?"}]}}]}},
        {"type": "user", "timestamp": "2026-10-09T10:05:00Z", "toolUseResult": {"questions": [], "answers": {"Pause at the stage close?": "No, run"}}, "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "q1", "content": "answered"}]}},
        {"type": "user", "timestamp": "2026-10-08T10:00:00Z", "message": {"role": "user", "content": "Too old, before the since date. OPENROUTER_API_KEY=sk-live-123"}},
        {"type": "user", "timestamp": "2026-10-09T11:00:00Z", "message": {"role": "user", "content": "Set OPENROUTER_API_KEY=sk-live-123 please"}},
    ]
    (folder / "s1.jsonl").write_text("\n".join(json.dumps(o) for o in lines) + "\n", encoding="utf-8")
    rc, out = run(tmp_path, "extract", "--since", "2026-10-09", "--out", str(tmp_path / "ext"), "--project-root", str(root), "--project-name", "Thing", "--home", str(tmp_path / "home"))
    assert rc == 0 and "3 message(s) and answer(s) extracted" in out, out
    text = (tmp_path / "ext" / "owner-messages-Thing.md").read_text(encoding="utf-8")
    assert "Resume." in text and "No, run" in text and "withheld" in text
    assert "sk-live-123" not in text and "Maintainer session" not in text and "cross-session" not in text and "task-notification" not in text and "Too old" not in text
