"""The program release, TASK-056: tests for the clauses of release S's register rows that the reality check found held by no
test (R-066, R-067, R-069); supervisor-authored.

Each test characterises behaviour release S built (bridge 2026.11.12a), so the red-on-checkpoint proof does not apply; its strength
is shown by run/supervisor/TASK-056-mutants.json, one mutant of the clause's program line each. The rows' other clauses are held by
the tests their Evidence cells name, which carry the rows' IDs."""
import os

from test_release_s_evidence import git as evidence_git, make, no_evidence, run as run_completion
from test_release_s_records_gate import change, git, premerge_record, repo, state  # noqa: F401 (repo is a fixture)
from test_session_start_module import HOOK, home, pointers, project  # noqa: F401 (home is a fixture)


# ---------------------------------------------------------------- R-066: a record folder is never a test, by any spelling


def test_r066_a_path_under_handoff_or_run_is_no_test_by_any_spelling(program):
    """R-066: a file under `handoff/` or `run/`, like one under `docs/`, counts neither as an Evidence cell's test, by a path or by
    an address, nor as done mode's trace (the record folders all three, not `docs/` alone)."""
    cc = program("completion-check")
    for token in ("handoff/test_plan.md", "./handoff/tests/test_a.py", "run/agent/test_a.py", "Run//supervisor/test_a.py",
                  "https://example.invalid/o/r/blob/main/handoff/test_a.py", "https://example.invalid/o/r/blob/main/run/test_a.py"):
        assert not cc.is_test_path(token), token
    assert cc.is_test_path("tests/test_a.py") and cc.is_test_path("https://example.invalid/o/r/blob/main/tests/test_a.py")


def test_r066_a_test_named_file_under_run_is_no_trace_in_done_mode(tmp_path):
    """R-066, done mode's trace: a test-named file under `run/` that names the row is no tracked test naming it."""
    r = make(tmp_path, "| R-001 | the user imports a CSV file | owner | built | tests/test_import.py |\n", texts=None)
    (r / "tests").mkdir()
    (r / "tests" / "test_import.py").write_text("def test_import():\n    assert True\n", encoding="utf-8")
    (r / "run" / "agent").mkdir(parents=True)
    (r / "run" / "agent" / "test_import_notes.py").write_text("# R-001 imported by hand\n", encoding="utf-8")
    evidence_git(r, "add", "-A", "-f")
    evidence_git(r, "commit", "-q", "-m", "a test and a note under run (#8)")
    rc, out = run_completion(r, "done")
    lines = no_evidence(out)
    assert rc == 1 and len(lines) == 1 and "R-001" in lines[0] and "no tracked test names it" in lines[0], out


# ---------------------------------------------------------------- R-067: the short gate opens no round


def test_r067_the_short_gate_writes_its_record_and_no_snapshot_round_or_mark(repo, program, monkeypatch, capsys):
    """R-067: `premerge-records <pr>` writes the pre-merge record for the head and nothing else under the guard's folder: no
    snapshot, no rounds record, no verified mark, so no Review B is asked for and no round is counted."""
    for k in ("GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM"):
        monkeypatch.setenv(k, os.devnull)
    mod = program("review-guard")
    change(repo, "docs/PROJECT_STATUS.md", "Phase: done\n")
    head = git(repo, "rev-parse", "HEAD")
    monkeypatch.setattr(mod, "pr_state", lambda pr, root: (state(repo, ["docs/PROJECT_STATUS.md"]), None))
    assert mod.cmd_premerge_records(str(repo), "12") == 0, capsys.readouterr().out
    folder = repo / ".git" / "bridge"
    written = sorted(os.path.relpath(os.path.join(d, f), str(folder)).replace("\\", "/") for d, _, files in os.walk(str(folder)) for f in files)
    assert written == ["premerge/" + head] and premerge_record(repo) == [head], written


# ---------------------------------------------------------------- R-069: after a compaction the hook asks for less


def test_r069_the_hook_reads_one_file_with_its_conditional_files_and_names_the_inventory_on_demand(tmp_path, home):
    """R-069: the list asks for the ONE phase file of the step in hand with every conditional workflow file it lists, and ends
    with the line that begins "On demand, by the section, heading or entry the step in hand names, never whole as a block:
    docs/INVENTORY.md", an `on demand:` line per conventions file of the phase under it."""
    out = pointers(project(tmp_path, "Phase: building",
                           "Workflows: Host Extension Development → Claude Code Extension; traits: Installable"), home)
    lines = out.split("\n")
    assert "with it every conditional workflow file listed after the phase files" in HOOK.READ_ONE and HOOK.READ_ONE in lines, out
    on_demand = [i for i, l in enumerate(lines) if l.startswith("On demand, by the section, heading or entry the step in hand names, "
                                                                 "never whole as a block: docs/INVENTORY.md")]
    assert len(on_demand) == 1, out
    listed = lines[lines.index(HOOK.READ_ONE) + 1:on_demand[0]]
    assert listed and all(l.startswith("  - ~/.claude/cursor-bridge/workflow/") for l in listed), listed
    assert any("/types/host-extension.md" in l for l in listed) and any("/traits/installable.md" in l for l in listed), listed
    below = lines[on_demand[0] + 1:on_demand[0] + 3]
    assert below == ["  - on demand: ~/.claude/cursor-bridge/Merge-Verification-Policy.md",
                     "  - on demand: ~/.claude/cursor-bridge/Known-Pitfalls.md"], below
