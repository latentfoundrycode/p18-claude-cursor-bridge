"""evaluate-reports.py (release A3, plan 12.5): the three real document shapes; an entry added, an
entry changed after processing, a run with nothing new, a declined entry not raised again, a seeded
entry not raised and never another project's; the owner's messages extracted in the record's own
forms. Scratch projects, homes and ledgers only."""
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

## Issue 3 — A numbered one, the video factory's way
Context: the third.
"""
FEEDBACK_REANGLE = """# Thing — Claude-Cursor Bridge Feedback

## Stage 1 — Foundation (2026-10-01)

### FB-001 — A check fired wrongly
The loop guard sent back a report.

### Process observations (supervisor)
A note without an ID, identified by these first lines.
"""
FEEDBACK_TDP = """# Thing — Claude-Cursor Bridge Feedback

## Milestone 5 close (2026-09-20)

The whole entry sits under the stage heading, with no subsection at all.
It has two paragraphs.

## Milestone 6 close (2026-09-21)

Another one.
"""
FEEDBACK_VF = """# Thing — Claude-Cursor Bridge Feedback

## 1. The gate proves code runs, not that it matches a contract (Stage P — supervisor). Highest value.

The main text of the first entry.

### Why this is worth encoding
Its trailing part belongs to it.

## 2. The refactor pass has no clean path for fixture duplication (Stage P — supervisor).

The second entry.
"""


def project(tmp_path, feedback=FEEDBACK_REANGLE):
    root = tmp_path / "proj"
    (root / "Documents").mkdir(parents=True)
    (root / "Workspace").mkdir()
    (root / "Documents" / "Thing Issues During Development and Their Solutions.md").write_text(ISSUES, encoding="utf-8")
    (root / "Documents" / "Thing Claude-Cursor Bridge Feedback.md").write_text(feedback, encoding="utf-8")
    return root


def run(tmp_path, *args):
    p = subprocess.run([sys.executable, PROG] + list(args), capture_output=True, text=True, cwd=str(tmp_path))
    return p.returncode, p.stdout + p.stderr


def common(tmp_path, root):
    return ["--project-root", str(root), "--project-name", "Thing", "--ledger", str(tmp_path / "ledger.json"), "--home", str(tmp_path / "home")]


def ids_in(path):
    return [l.split(" / ")[2].split(" - ")[0] for l in path.read_text(encoding="utf-8").splitlines() if l.startswith("## ")]


def test_the_three_document_shapes_are_read_whole(tmp_path):
    """Finding 1 of the 2026.10.10b review: the TDP's `##`-only feedback and the video factory's
    numbered entries were invisible; every shape now yields its entries and reports what is outside."""
    for i, (feedback, expected) in enumerate(((FEEDBACK_REANGLE, {"FB-001"}), (FEEDBACK_TDP, set()), (FEEDBACK_VF, {"FEEDBACK-1", "FEEDBACK-2"}))):
        sub = tmp_path / ("shape%d" % i)
        sub.mkdir()
        root = project(sub, feedback)
        rc, out = run(sub, "collect", "--out", str(sub / "out"), *common(sub, root))
        assert rc == 0 and "Thing feedback:" in out, out
        found = set(ids_in(sub / "out" / "unprocessed.md"))
        assert expected <= found and {"ISS-001", "ISS-002", "ISSUE-3"} <= found, (feedback[:30], found)
        fb = [i for i in found if i.startswith("FB-") or i.startswith("FEEDBACK-") or i.startswith("feedback:")]
        assert len(fb) == 2, (feedback[:30], fb)
        if feedback is FEEDBACK_VF:
            text = (sub / "out" / "unprocessed.md").read_text(encoding="utf-8")
            assert "Its trailing part belongs to it." in text.split("FEEDBACK-1")[1].split("\n## ")[0], "a numbered entry keeps its trailing subsection"


def test_collect_record_change_and_nothing_new(tmp_path):
    root = project(tmp_path)
    rc, out = run(tmp_path, "collect", "--out", str(tmp_path / "out1"), *common(tmp_path, root))
    assert rc == 0 and "5 entries to evaluate (5 new" in out, out
    for eid, outcome, reason in (("ISS-001", "fixed", "2026.10.10b"), ("ISS-002", "declined", "project-specific wording"), ("ISSUE-3", "project-specific", ""), ("FB-001", "pitfall", "KP-040")):
        rc, out = run(tmp_path, "record", "Thing", eid, outcome, *(["--reason", reason] if reason else []), *common(tmp_path, root))
        assert rc == 0, out
    rc, out = run(tmp_path, "record", "Thing", "ISS-002", "declined", *common(tmp_path, root))
    assert rc == 2 and "needs --reason" in out
    rc, out = run(tmp_path, "collect", "--out", str(tmp_path / "out2"), *common(tmp_path, root))
    assert rc == 0 and "1 entries to evaluate (1 new" in out, "the entry without an ID is still unprocessed: " + out
    fp_id = ids_in(tmp_path / "out2" / "unprocessed.md")[0]
    assert fp_id.startswith("feedback:")
    rc, out = run(tmp_path, "record", "Thing", fp_id, "project-specific", *common(tmp_path, root))
    assert rc == 0, out
    rc, out = run(tmp_path, "collect", "--out", str(tmp_path / "out3"), *common(tmp_path, root))
    assert rc == 0 and "nothing new" in out and not (tmp_path / "out3").exists(), "a run with nothing new writes no file: " + out
    fb = (root / "Documents" / "Thing Claude-Cursor Bridge Feedback.md")
    fb.write_text(fb.read_text(encoding="utf-8").replace("### Process observations (supervisor)", "### Observations on the process (supervisor)"), encoding="utf-8")
    rc, out = run(tmp_path, "collect", "--out", str(tmp_path / "out3b"), *common(tmp_path, root))
    assert rc == 0 and "nothing new" in out, "a renamed heading does not make an entry new (finding 11): " + out
    (root / "Documents" / "Thing Issues During Development and Their Solutions.md").write_text(ISSUES.replace("Context: the second.", "Context: the second, which recurred."), encoding="utf-8")
    rc, out = run(tmp_path, "collect", "--out", str(tmp_path / "out4"), *common(tmp_path, root))
    assert rc == 0 and "(0 new, 1 updated)" in out, out
    text = (tmp_path / "out4" / "unprocessed.md").read_text(encoding="utf-8")
    assert "ISS-002 - UPDATED (earlier: declined project-specific wording)" in text, "a declined entry that changed is shown with its earlier verdict"
    ledger = json.loads((tmp_path / "ledger.json").read_text(encoding="utf-8"))
    assert ledger["Thing/ISS-001"]["outcome"] == "fixed" and ledger["Thing/FB-001"]["reason"] == "KP-040" and ledger["_meta"]["last_collect"]
    rc, out = run(tmp_path, "record", "Thing", "ISS-099", "fixed", "--reason", "x", "--force", *common(tmp_path, root))
    assert rc == 0
    rc, out = run(tmp_path, "collect", "--out", str(tmp_path / "out5"), *common(tmp_path, root))
    assert "ISS-099" not in out, "a forced entry is never raised as updated (finding 13)"


def test_the_seed_reads_each_project_file_by_its_header_and_never_another_project(tmp_path):
    """Findings 2 and 3: one evaluation file per project, matched to that project only; the source
    column found by its header; Issue n, Feedback n, ranges and notes matched."""
    root = project(tmp_path, FEEDBACK_VF)
    (tmp_path / "home" / ".claude" / "projects" / str(root).replace(":", "-").replace("\\", "-").replace("/", "-") / "memory").mkdir(parents=True)
    (tmp_path / "home" / ".claude" / "projects" / str(root).replace(":", "-").replace("\\", "-").replace("/", "-") / "memory" / "proceed-autonomously.md").write_text("a note\n", encoding="utf-8")
    ev = tmp_path / "ev"
    ev.mkdir()
    (ev / "Thing.md").write_text("# R12 evidence\\n\\n| Short form | File |\\n|---|---|\\n| SV | x |\\n\\n"
                                 "| # | Source | Date | What | Fix | Class | Evidence |\\n|---|---|---|---|---|---|---|\\n"
                                 "| 1 | ISS-001; Feedback 1 | 2026-09-25 | x | y | **CLOSED** by 2026.10.04a | z |\\n"
                                 "| 2 | Issues 2-3 | 2026-09-26 | x | y | PLANNED (section 10) | z |\\n"
                                 "| 3 | Memory `proceed-autonomously.md` | 2026-09-26 | x | y | PARTLY | z |\\n".replace("\\n", "\n"), encoding="utf-8")
    (ev / "Other.md").write_text("| ID or source | Date | What | Fix | Classification | Evidence |\\n|---|---|---|---|---|---|\\n| ISS-002 | 2026-09-25 | x | y | OPEN | not this project |\\n".replace("\\n", "\n"), encoding="utf-8")
    rc, out = run(tmp_path, "seed", "--evaluations", str(ev), *common(tmp_path, root))
    assert rc == 0 and "5 entries seeded" in out and "Other.md" in out, out
    ledger = json.loads((tmp_path / "ledger.json").read_text(encoding="utf-8"))
    assert ledger["Thing/ISS-001"]["outcome"] == "fixed" and ledger["Thing/ISSUE-3"]["outcome"] == "planned" and ledger["Thing/ISS-002"]["outcome"] == "planned"
    assert ledger["Thing/FEEDBACK-1"]["outcome"] == "fixed" and ledger["Thing/note:proceed-autonomously.md"]["outcome"] == "planned"
    rc, out = run(tmp_path, "collect", "--out", str(tmp_path / "out"), *common(tmp_path, root))
    assert rc == 0 and "1 entries to evaluate" in out and "FEEDBACK-2" in (tmp_path / "out" / "unprocessed.md").read_text(encoding="utf-8"), "only the unseeded entry is raised: " + out


def test_the_owners_messages_are_extracted_in_the_records_own_forms(tmp_path):
    """Finding 4: only the owner's own typing (origin.kind human), no compaction summary, each record
    once across files, a screenshot's text kept, every key-shaped token withheld, other sessions' messages out."""
    root = project(tmp_path)
    key = str(root).replace(":", "-").replace("\\", "-").replace("/", "-")
    folder = tmp_path / "home" / ".claude" / "projects" / key
    folder.mkdir(parents=True)
    human = {"kind": "human"}
    lines = [
        {"type": "user", "uuid": "u1", "timestamp": "2026-10-09T10:00:00Z", "origin": human, "message": {"role": "user", "content": "Resume."}},
        {"type": "user", "uuid": "u2", "timestamp": "2026-10-09T10:01:00Z", "isMeta": True, "message": {"role": "user", "content": "Another Claude session sent a message:\n<cross-session-message from=\"x\">pause</cross-session-message>"}},
        {"type": "user", "uuid": "u3", "timestamp": "2026-10-09T10:02:00Z", "origin": {"kind": "session"}, "message": {"role": "user", "content": "From Supervisor Agent: Maintainer session (bridge mechanics, no owner authority): pause here."}},
        {"type": "user", "uuid": "u4", "timestamp": "2026-10-09T10:03:00Z", "origin": {"kind": "task-notification"}, "message": {"role": "user", "content": "<task-notification>done</task-notification>"}},
        {"type": "user", "uuid": "u5", "timestamp": "2026-10-09T10:03:30Z", "origin": human, "isCompactSummary": True, "message": {"role": "user", "content": "This session is being continued from a previous conversation."}},
        {"type": "assistant", "uuid": "a1", "timestamp": "2026-10-09T10:04:00Z", "message": {"role": "assistant", "content": [{"type": "tool_use", "id": "q1", "name": "AskUserQuestion", "input": {"questions": [{"question": "Pause at the stage close?"}]}}]}},
        {"type": "user", "uuid": "u6", "timestamp": "2026-10-09T10:05:00Z", "toolUseResult": {"questions": [], "answers": {"Pause at the stage close?": "No, run"}}, "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "q1", "content": "answered"}]}},
        {"type": "user", "uuid": "u7", "timestamp": "2026-10-08T10:00:00Z", "origin": human, "message": {"role": "user", "content": "Too old, before the since date."}},
        {"type": "user", "uuid": "u8", "timestamp": "2026-10-09T11:00:00Z", "origin": human, "message": {"role": "user", "content": "Set OPENROUTER_API_KEY=sk-live-123 please, and here is the bare one: hf_abcdefghijklmnop1234"}},
        {"type": "user", "uuid": "u9", "timestamp": "2026-10-09T12:41:00Z", "origin": human, "message": {"role": "user", "content": [{"type": "image", "source": {}}, {"type": "text", "text": "You are opening a large amount of terminals. Are you failing to close them?"}]}},
    ]
    (folder / "s1.jsonl").write_text("\n".join(json.dumps(o) for o in lines) + "\n", encoding="utf-8")
    (folder / "s2.jsonl").write_text("\n".join(json.dumps(o) for o in lines[:1]) + "\n", encoding="utf-8")   # the same record in a second file
    rc, out = run(tmp_path, "extract", "--since", "2026-10-09", "--out", str(tmp_path / "ext"), *common(tmp_path, root))
    assert rc == 0 and "4 message(s) and answer(s) extracted" in out, out
    text = (tmp_path / "ext" / "owner-messages-Thing.md").read_text(encoding="utf-8")
    assert text.count("Resume.") == 1 and "No, run" in text and "[with 1 image(s)]" in text and "opening a large amount of terminals" in text
    assert "sk-live-123" not in text and "hf_abcdefghijklmnop1234" not in text and text.count("withheld") >= 2
    assert "continued from a previous" not in text and "Maintainer session" not in text and "cross-session" not in text and "task-notification" not in text and "Too old" not in text
    rc, out = run(tmp_path, "extract", "--out", str(tmp_path / "ext2"), *common(tmp_path, root))
    assert rc == 0 and "since %s" % json.loads((tmp_path / "ledger.json").read_text(encoding="utf-8"))["_meta"]["last_extract"] in out, "without --since the ledger's last extract is the date (finding 13): " + out
