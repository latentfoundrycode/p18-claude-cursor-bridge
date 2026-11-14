"""TASK-061, the supervisor's acceptance tests: a review run's own launcher rows (R-079).

enforces: docs/REQUIREMENTS.md R-079; docs/BUILD_PLAN.md, TASK-061's Done when.

- `learned_limit` ignores every row whose start lies between the start and the end of a `review` row's run, read from
  the log's own times (a review row with no end ignoring nothing), so a suite a reviewer ran in its scratch folder
  teaches no limit.
- `review-guard.py verify` prints, after its verdict and never changing it or the exit code, one note naming the
  launcher rows written during the review's own run by id and kind, the review's own row apart, and no note where
  there is none.
- After the bridge's own launcher tests have run, the checkout's `run/launcher/runs.jsonl` holds no row of theirs.

At the checkpoint every case is red but the controls. The builder adds its cases to the launcher test files and
tests/test_review_guard.py and edits nothing in this file.
"""
import json
import os
import re
import subprocess
import sys
import time

import pytest

from test_review_guard import git, guard, repo  # noqa: F401  (repo is a fixture)

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.abspath(os.path.join(HERE, os.pardir))
CHECKOUT_LOG = os.path.join(WORKSPACE, "run", "launcher", "runs.jsonl")
LAUNCHER_TESTS = ["tests/test_bridge_run.py", "tests/test_bridge_run_slot.py", "tests/test_bridge_run_driver.py",
                  "tests/test_release_s_launcher.py"]


def write_rows(folder, rows):
    log = folder / "run" / "launcher"
    log.mkdir(parents=True, exist_ok=True)
    (log / "runs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def stamp(t):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))


# ---------------------------------------------------------------- learned_limit


REVIEW = {"id": "2026-10-07T10:00:00Z", "kind": "review", "seconds": 1200, "exit": 0, "healthy": True}
INSIDE = {"id": "2026-10-07T10:05:00Z", "kind": "test", "seconds": 2300, "exit": 0, "healthy": True}
OUTSIDE = {"id": "2026-10-07T12:00:00Z", "kind": "test", "seconds": 1300, "exit": 0, "healthy": True}


def test_r079_control_without_a_review_every_healthy_row_teaches(program, tmp_path):
    br = program("bridge-run")
    write_rows(tmp_path, [INSIDE, OUTSIDE])
    limit, why = br.learned_limit("test", str(tmp_path))
    assert limit == 3450 and INSIDE["id"] in why, (limit, why)


def test_r079_a_row_inside_a_review_s_run_teaches_no_limit(program, tmp_path):
    br = program("bridge-run")
    write_rows(tmp_path, [INSIDE, OUTSIDE, REVIEW])            # the review's row is written last, at its end
    limit, why = br.learned_limit("test", str(tmp_path))
    assert limit == 1950 and OUTSIDE["id"] in why, (limit, why)


def test_r079_a_suffixed_id_inside_a_review_is_ignored_too(program, tmp_path):
    """Two runs started in one second: the second's id carries a suffix; its start is still read from the id."""
    br = program("bridge-run")
    write_rows(tmp_path, [dict(INSIDE, id="2026-10-07T10:05:00Z-2"), OUTSIDE, REVIEW])
    limit, why = br.learned_limit("test", str(tmp_path))
    assert limit == 1950 and OUTSIDE["id"] in why, (limit, why)


def test_r079_every_kind_inside_a_review_is_ignored(program, tmp_path):
    br = program("bridge-run")
    driver_in = {"id": "2026-10-07T10:10:00Z", "kind": "driver", "seconds": 4000, "exit": 0, "healthy": True}
    driver_out = {"id": "2026-10-07T13:00:00Z", "kind": "driver", "seconds": 3500, "exit": 0, "healthy": True}
    write_rows(tmp_path, [driver_in, driver_out, REVIEW])
    limit, why = br.learned_limit("driver", str(tmp_path))
    assert driver_out["id"] in why and driver_in["id"] not in why, (limit, why)


def test_r079_a_review_row_with_no_end_ignores_nothing(program, tmp_path):
    br = program("bridge-run")
    write_rows(tmp_path, [INSIDE, OUTSIDE, dict(REVIEW, seconds=None)])
    limit, why = br.learned_limit("test", str(tmp_path))
    assert limit == 3450 and INSIDE["id"] in why, (limit, why)


def test_r079_a_row_after_the_review_s_end_still_teaches(program, tmp_path):
    br = program("bridge-run")
    after = dict(INSIDE, id="2026-10-07T10:25:00Z")             # the review ended at 10:20:00
    write_rows(tmp_path, [after, OUTSIDE, REVIEW])
    limit, why = br.learned_limit("test", str(tmp_path))
    assert limit == 3450 and after["id"] in why, (limit, why)


# ---------------------------------------------------------------- review-guard verify's note


def reviewed_with_rows(repo, rows_of):
    """snapshot; a Review B launch line at T; the log's rows as rows_of(T) gives them; verify. (rc, out, T)"""
    rc, out = guard(repo, "snapshot", "TASK-001")
    assert rc == 0, out
    t = time.time() + 2
    (repo / "run" / "review" / "REVIEW-TASK-001.err").write_text(
        "bridge-run: started %s\nsome output of the reviewer\nbridge-run: exit 0\n" % stamp(t), encoding="utf-8")
    rows = rows_of(t)
    log = repo / "run" / "launcher"
    log.mkdir(parents=True, exist_ok=True)
    (log / "runs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    rc, out = guard(repo, "verify", "TASK-001")
    return rc, out, t


def after_verdict(out):
    lines = out.splitlines()
    ok = [i for i, l in enumerate(lines) if l.startswith("review-guard: OK")]
    assert len(ok) == 1, out
    return "\n".join(lines[ok[0] + 1:])


def test_r079_verify_names_the_rows_written_during_the_review(repo):
    def rows(t):
        return [{"id": stamp(t - 300), "kind": "test", "seconds": 40, "exit": 0, "healthy": True},
                {"id": stamp(t + 60), "kind": "test", "seconds": 5, "exit": 0, "healthy": True},
                {"id": stamp(t + 120) + "-2", "kind": "driver", "seconds": 9, "exit": 1, "healthy": None},
                {"id": stamp(t + 900), "kind": "watch", "seconds": 30, "exit": 0, "healthy": None},
                {"id": stamp(t), "kind": "review", "seconds": 600, "exit": 0, "healthy": None}]
    rc, out, t = reviewed_with_rows(repo, rows)
    assert rc == 0 and "verified mark written" in out, out
    note = after_verdict(out)
    lines = [l for l in note.splitlines() if l.strip()]
    assert len(lines) == 1, "one note, after the verdict: " + out
    assert stamp(t + 60) in note and stamp(t + 120) + "-2" in note, note
    assert re.search(r"\btest\b", note) and re.search(r"\bdriver\b", note), "each row named with its kind: " + note
    assert stamp(t - 300) not in note and stamp(t + 900) not in note, "rows outside the review's run are not named: " + note


def test_r079_verify_prints_no_note_where_no_row_was_written_during_the_review(repo):
    def rows(t):
        return [{"id": stamp(t - 300), "kind": "test", "seconds": 40, "exit": 0, "healthy": True},
                {"id": stamp(t), "kind": "review", "seconds": 600, "exit": 0, "healthy": None}]
    rc, out, t = reviewed_with_rows(repo, rows)
    assert rc == 0 and "verified mark written" in out, out
    assert after_verdict(out).strip() == "", "nothing after the verdict where no row was written during the review: " + out


# ---------------------------------------------------------------- the launcher tests write no row into the checkout


@pytest.mark.skipif(not os.path.isdir(os.path.join(WORKSPACE, "run")),
                    reason="the launcher writes its log only where the checkout has a run/ folder (absent in CI)")
def test_r079_the_launcher_tests_write_no_row_into_the_checkout(tmp_path):
    """The bridge's own launcher tests each start the launcher in a temporary Workspace of their own, by their own
    arrangement: run in a subprocess, they leave the checkout's run log as it was."""
    before = open(CHECKOUT_LOG, "rb").read() if os.path.isfile(CHECKOUT_LOG) else None
    env = {k: v for k, v in os.environ.items() if k.upper() not in ("BRIDGE_RUN_ALLOW_ANY", "BRIDGE_RUN_SLOT_SCALE")}
    p = subprocess.run([sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-q"] + LAUNCHER_TESTS,
                       capture_output=True, text=True, cwd=WORKSPACE, env=env, timeout=3000)
    assert " passed" in p.stdout, p.stdout[-3000:] + p.stderr[-2000:]
    after = open(CHECKOUT_LOG, "rb").read() if os.path.isfile(CHECKOUT_LOG) else None
    if before != after:
        new = (after or b"")[len(before or b""):].decode("utf-8", "replace")
        pytest.fail("the launcher tests wrote rows into the checkout's run log:\n" + new[:3000])
