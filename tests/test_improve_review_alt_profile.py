"""TASK-087d (R-107; docs/DESIGN.md, "Change: the improvements release", C39): `roster-check.py --review-alt
<reason>` acts on the profile the resolve picks. The supervisor's acceptance tests, written before the brief and
committed before the checkpoint.

The defect (docs/HARDENING.md, TASK-087c, Review A, round 2): the request took the first profile whose builder is
usable and did not apply the resolve's exclusion of a profile whose Review B its pool or a mark excludes with no
independent usable alternate, so with the other pool exhausted, on this repository's roster, it refused with `no
review_b_alt named in profile 'full'` while the resolve used the native profile, which names composer-2.5. The first
test is the reviewer's wanted probe: a two-profile roster, the pool exhausted, the native profile's alternate
resolving with its DEVIATION line.

The scratch repositories, the roster's state file and the run record are built as tests/test_improve_roster_alt.py
builds them, with its helpers; `roster-check.py` runs with `--no-probe` from the scratch repository, but for the
in-process tests that replace `probe`.

enforces: docs/BUILD_PLAN.md, TASK-087d, Done when; docs/REQUIREMENTS.md R-107; docs/DESIGN.md C39
"""
import json
import os

from roster_rows import BRANCH, COMPOSER, FULL, GPT, GROK_B, GROK_R, NATIVE, REVIEW_A, row
from test_improve_roster_alt import (_main_in_process, assert_deviation, commit, deviation_printed, fail_text,
                                     plant_resolved, resolve, resolved, resolved_path, scratch_repo, write,
                                     write_record, write_roster)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, os.pardir))

NATIVE_ALT = dict(NATIVE, review_b_alt=COMPOSER)
ON_REQUEST = "DEVIATION  review_b is %s on request (safety-refusal)" % COMPOSER


def _deviation_lines(out):
    return [line.strip() for line in out.splitlines() if line.strip().startswith("DEVIATION")]


def test_task087d_an_exhausted_pool_the_request_acts_on_the_native_profile(tmp_path):
    """The reviewer's wanted probe: the other pool exhausted, the full profile naming no alternate (its Review B in
    the exhausted pool), the native profile naming composer-2.5, an empty built set: the resolve picks the native
    profile, so the request does too, printing its DEVIATION line and writing the native profile with the entry
    (red on the checkpoint: `FAIL  --review-alt refused: no review_b_alt named in profile 'full'`)."""
    ws = scratch_repo(tmp_path)
    commit(ws, "checkpoint")
    write_roster(ws, [FULL, NATIVE_ALT], other_pool="exhausted")
    rc, out = resolve(ws, "--review-alt", "safety-refusal")
    assert "no review_b_alt" not in out, out
    assert_deviation(ws, rc, out, COMPOSER, "safety-refusal", set())
    assert _deviation_lines(out) == [ON_REQUEST], out
    data = resolved(ws)
    assert data["profile"] == "native" and data["builder"] == COMPOSER and data["review_a"] == REVIEW_A, data


def test_task087d_the_plain_resolve_and_the_request_name_the_same_profile(tmp_path):
    """The profile in use is one reading: the resolve without the request and the request name the same profile on
    the same roster (red on the checkpoint, where the request names `full`)."""
    ws = scratch_repo(tmp_path)
    commit(ws, "checkpoint")
    write_roster(ws, [FULL, NATIVE_ALT], other_pool="exhausted")
    rc, out = resolve(ws)
    assert rc == 0 and resolved(ws)["profile"] == "native", out
    rc, out = resolve(ws, "--review-alt", "safety-refusal")
    assert rc == 0 and resolved(ws)["profile"] == "native", out


def test_task087d_a_marked_review_b_skips_the_profile_for_the_request_too(tmp_path):
    """The mark, the other exclusion the resolve applies to a profile's Review B: with the pool available and the
    full profile's Review B marked unavailable, no alternate there, the request acts on the native profile (red on
    the checkpoint)."""
    ws = scratch_repo(tmp_path)
    commit(ws, "checkpoint")
    write_roster(ws, [FULL, NATIVE_ALT], unavailable=[GPT])
    rc, out = resolve(ws, "--review-alt", "safety-refusal")
    assert_deviation(ws, rc, out, COMPOSER, "safety-refusal", set())
    assert resolved(ws)["profile"] == "native", out


def test_task087d_after_a_grok_build_the_request_records_the_built_family(tmp_path):
    """After a grok builder row on the branch the native profile's alternate is independent of what was built; the
    request resolves it with the known set in its entry (red on the checkpoint)."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [FULL, NATIVE_ALT], other_pool="exhausted")
    write_record(ws, row(GROK_R, start=c1, clean=True))
    commit(ws, "the builder's work")
    rc, out = resolve(ws, "--review-alt", "safety-refusal")
    assert_deviation(ws, rc, out, COMPOSER, "safety-refusal", {"xai"})
    assert resolved(ws)["profile"] == "native", out


def test_task087d_after_a_composer_build_the_request_is_refused_by_the_family_cause(tmp_path):
    """After a composer builder row the native profile's alternate is of the family that built the branch: the
    request ends with exit 1 and that cause, the resolved file unchanged (red on the checkpoint, whose cause is the
    full profile's missing alternate)."""
    ws = scratch_repo(tmp_path)
    c1 = commit(ws, "checkpoint")
    write_roster(ws, [FULL, NATIVE_ALT], other_pool="exhausted")
    write_record(ws, row(COMPOSER, start=c1, clean=True))
    commit(ws, "the builder's work")
    before = plant_resolved(ws)
    rc, out = resolve(ws, "--review-alt", "safety-refusal")
    assert rc == 1 and "RESOLVED" not in out and not deviation_printed(out), out
    text = fail_text(out)
    assert COMPOSER in text and "cursor" in text and "built the branch" in text, out
    assert "no review_b_alt" not in text, out
    assert resolved_path(ws).read_bytes() == before, "the resolved file is left unchanged"


def test_task087d_with_the_pool_available_the_request_stays_on_the_full_profile(tmp_path):
    """The rule that stands (TASK-086a, round 2): where the resolve picks the full profile, the request acts on it
    and never passes to a later profile; the full profile naming no alternate, it ends with exit 1 and that cause."""
    ws = scratch_repo(tmp_path)
    commit(ws, "checkpoint")
    write_roster(ws, [FULL, NATIVE_ALT])
    before = plant_resolved(ws)
    rc, out = resolve(ws, "--review-alt", "safety-refusal")
    assert rc == 1 and "RESOLVED" not in out and not deviation_printed(out), out
    assert "no review_b_alt" in fail_text(out) and "'full'" in fail_text(out), out
    assert resolved_path(ws).read_bytes() == before


def test_task087d_a_full_profile_that_names_an_alternate_keeps_it_on_request(tmp_path):
    """Where the full profile names an alternate and its Review B is excluded by the exhausted pool, the resolve uses
    the full profile with its alternate; the request acts on that profile, the reason the one given."""
    ws = scratch_repo(tmp_path)
    commit(ws, "checkpoint")
    write_roster(ws, [dict(FULL, review_b_alt=COMPOSER), NATIVE_ALT], other_pool="exhausted")
    rc, out = resolve(ws, "--review-alt", "safety-refusal")
    assert_deviation(ws, rc, out, COMPOSER, "safety-refusal", set())
    data = resolved(ws)
    assert data["profile"] == "full" and data["builder"] == GROK_B, data


def _fake_probe(probed, failing, sign_in=()):
    def fake_probe(model_id, *args, **kwargs):
        probed.append(model_id)
        if model_id in sign_in:
            return None, "sign-in"
        if model_id in failing:
            return False, "exit 1; stdout=''; stderr='refused'"
        return True, "answered"
    return fake_probe


def test_task087d_a_review_b_that_did_not_answer_skips_the_profile_for_the_request_too(program, tmp_path,
                                                                                         monkeypatch, capsys):
    """With probes, the request reads each answer as the resolve reads it: the full profile's Review B not answering
    skips that profile, so the request acts on the native profile, every model probed at most once (red on the
    checkpoint, which probed the full profile's builder alone and refused for the missing alternate). The skipped
    profile's builder and Review B are probed once each; the native profile's builder is also its alternate, so its
    count is not held."""
    ws = scratch_repo(tmp_path)
    commit(ws, "checkpoint")
    write_roster(ws, [FULL, NATIVE_ALT])
    mod = program("roster-check")
    probed = []
    monkeypatch.setattr(mod, "probe", _fake_probe(probed, failing={GPT}))
    rc, out = _main_in_process(mod, ws, monkeypatch, capsys, "--review-alt", "safety-refusal")
    assert rc == 0, out
    data = resolved(ws)
    assert data["profile"] == "native" and data["review_b"] == COMPOSER, (data, out)
    assert data["deviation"]["reason"] == "safety-refusal", data
    assert GPT in probed and COMPOSER in probed, (probed, out)
    assert probed.count(GROK_B) == 1 and probed.count(GPT) == 1, "the skipped profile's models once each: %r" % probed


def test_task087d_a_sign_in_ends_the_request_with_exit_5(program, tmp_path, monkeypatch, capsys):
    """The Cursor tool signed out: the request ends with SIGN-IN, exit 5, as the resolve does, the resolved file
    unchanged (as on the checkpoint)."""
    ws = scratch_repo(tmp_path)
    commit(ws, "checkpoint")
    write_roster(ws, [FULL, NATIVE_ALT], other_pool="exhausted")
    before = plant_resolved(ws)
    mod = program("roster-check")
    probed = []
    sign_in = getattr(mod, "PROBE_SIGN_IN")
    monkeypatch.setattr(mod, "probe", lambda model_id, *a, **k: (probed.append(model_id) or sign_in, "sign-in"))
    rc, out = _main_in_process(mod, ws, monkeypatch, capsys, "--review-alt", "safety-refusal")
    assert rc == 5, out
    assert resolved_path(ws).read_bytes() == before


def test_task087d_this_repositorys_roster_resolves_the_native_alternate_on_request(tmp_path):
    """This repository's docs/ROSTER.json, copied into a scratch repository with no builder row and the other pool
    exhausted as the roster records it: the request resolves composer-2.5 on the native profile; the real resolved
    file is not touched (red on the checkpoint)."""
    real = os.path.join(ROOT, "docs", "ROSTER.json")
    real_resolved = os.path.join(ROOT, "docs", "ROSTER.resolved.json")
    before = open(real_resolved, "rb").read() if os.path.exists(real_resolved) else None
    roster = json.loads(open(real, encoding="utf-8").read())
    ws = scratch_repo(tmp_path)
    commit(ws, "checkpoint")
    write(ws, "docs/ROSTER.json", json.dumps(roster, indent=2) + "\n")
    write(ws, ".git/bridge/roster-state.json",
          json.dumps({"other_pool": "exhausted", "exhausted_at": "2026-11-21T19:54 UTC",
                      "exhausted_reason": "owner said usage exhausted"}, indent=2) + "\n")
    rc, out = resolve(ws, "--review-alt", "safety-refusal")
    assert rc == 0, out
    data = resolved(ws)
    assert data["profile"] == "native" and data["review_b"] == COMPOSER, (data, out)
    assert data["deviation"]["reason"] == "safety-refusal" and data["deviation"]["branch"] == BRANCH, data
    after = open(real_resolved, "rb").read() if os.path.exists(real_resolved) else None
    assert after == before, "the real resolved file is untouched"


def test_task087d_the_docstrings_roster_example_names_no_alternate_in_the_full_profile():
    """Stage I1's review, should fix 1: the module docstring's roster example shows the full profile as the policy's
    template and docs/ROSTER.json hold it, with no `review_b_alt` (red on the checkpoint, lines 15 to 19)."""
    path = os.path.join(ROOT, "bridge", "cursor-bridge", "roster-check.py")
    src = open(path, encoding="utf-8").read()
    doc = src.split('"""', 2)[1]
    start = doc.index('"profiles": [')
    example = doc[start:doc.index("]", start)]
    full_part = example[example.index('"name": "full"'):example.index('"name": "native"')]
    native_part = example[example.index('"name": "native"'):]
    assert "review_b_alt" not in full_part, full_part
    assert "review_b_alt" in native_part and COMPOSER in native_part, native_part
