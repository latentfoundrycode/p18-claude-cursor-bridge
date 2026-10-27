"""Stage B3's least-confident items 1 and 2, settled by tests before stage B4's first delegation (FIX-004).

enforces: docs/HARDENING.md, Stage B3, "Least confident (stage close, 2026-10-24)", items 1 and 2.

Item 1: the phase-module tests read a heading as trace-check.py reads one (tests/phase_modules.py's trace_headings,
which headings(), section() and section_span() use), so an indented heading of an excused title, which trace-check.py
excuses text under, is seen by every test that reads a module's headings or sections.
Item 2: every section an entry of trace-exceptions.md excuses in a phase module (the interface variant files apart,
which test_phase_modules_close.py pins) has one heading of its title and is pinned by its length and sha256, the set of
pins derived from the entries, so an edit of an excused passage fails until its pin is re-taken with the edit's own
`reword` entry, and a new entry fails until its section is pinned here.

Supervisor-written; no builder run."""
import hashlib
import importlib.util
import os
import re

import pytest

from phase_modules import BRIDGE, PHASES, read, module, headings, section, section_span, trace_headings

TRACE_CHECK = os.path.join(BRIDGE, "cursor-bridge", "trace-check.py")
EXCEPTIONS = os.path.join(BRIDGE, "cursor-bridge", "workflow", "trace-exceptions.md")
PREFIX = "bridge/cursor-bridge/workflow/phases/"
WORKFLOW_PREFIX = "bridge/cursor-bridge/workflow/"
WORKFLOW = os.path.join(BRIDGE, "cursor-bridge", "workflow")
CONDITIONAL = ("traits/", "types/")


def trace_check():
    spec = importlib.util.spec_from_file_location("trace_check_b3_least_confident", TRACE_CHECK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def phase_files():
    out = []
    for root, _dirs, files in os.walk(PHASES):
        for f in files:
            if f.endswith(".md"):
                out.append(os.path.relpath(os.path.join(root, f), PHASES).replace(os.sep, "/"))
    return sorted(out)


def excused_module_sections():
    """(file, title) of every `new` or `reword` entry on a phase module, the interface variant files apart, the file
    given under phases/, and of every entry on a conditional workflow, which trace-check.py reads as a module too (its
    is_module_path), the file given under workflow/ (`traits/<key>.md`, `types/...`; FIX-004's lead, taken by
    TASK-017); each once, the entry's heading stripped as trace-check.py's parse_exceptions strips it."""
    out = []
    for line in read(EXCEPTIONS).split("\n"):
        m = re.match(r"^- (?:new|reword) \S+ (\S+\.md) (.+)$", line)
        key = None
        if m and m.group(1).startswith(PREFIX) and not m.group(1).startswith(PREFIX + "interface/"):
            key = (m.group(1)[len(PREFIX):], m.group(2).strip())
        elif m and m.group(1).startswith(tuple(WORKFLOW_PREFIX + c for c in CONDITIONAL)):
            key = (m.group(1)[len(WORKFLOW_PREFIX):], m.group(2).strip())
        if key and key not in out:
            out.append(key)
    return out


def excused_file(rel):
    """A pinned file's text: a conditional workflow read under workflow/, a phase module under phases/."""
    return read(os.path.join(WORKFLOW, rel)) if rel.startswith(CONDITIONAL) else module(rel)


@pytest.mark.parametrize("rel", phase_files())
def test_item1_the_helpers_read_each_module_s_headings_as_trace_check_does(rel):
    """Item 1: for every file under workflow/phases/, the headings the phase-module tests read are the headings
    trace-check.py's parse_units reads, in order, so no heading it excuses text under escapes the tests."""
    text = module(rel)
    _units, theirs = trace_check().parse_units(text)
    assert [t for _level, t in headings(text)] == theirs, rel


def test_item1_the_round4_probe_is_seen():
    """Item 1's own proof, stage B3's review round 4 (Review A, tests): an indented ` ### Keeping the position`, a new
    entry's title, added to a copy of configuration.md is a heading trace-check.py excuses text under; the column-0
    reading the tests used before missed it, and every phase-module test passed. Now headings() lists it, so the
    STRUCTURE tests' comparison fails, and section() refuses the title, which now has two headings."""
    text = module("configuration")
    probe = text.rstrip("\n") + "\n\n ### Keeping the position\n\nA paragraph a new entry would excuse unseen.\n"
    assert [l for l in probe.split("\n") if l == "### Keeping the position"] == ["### Keeping the position"]
    _units, theirs = trace_check().parse_units(probe)
    assert theirs.count("Keeping the position") == 2
    assert headings(probe) == headings(text) + [(3, "Keeping the position")]
    with pytest.raises(AssertionError):
        section(probe, "Keeping the position", 3)


def test_item1_fences_open_and_close_as_trace_check_reads_them():
    """Item 1: a fence opened by an indented run (four spaces, which the old reading did not take for a fence) hides
    the headings inside it, and a fence closes only on a run of its character at least as long, whatever follows the
    run, as trace-check.py's parse_units reads a fence, and a fence never closed hides the rest of the file; the
    helpers and trace-check.py agree on each case."""
    cases = {
        "## A\n    ```\n### B\n    ```\n### C\n": [(2, "A"), (3, "C")],
        "## A\n````\n### B\n```\n### C\n````text\n### D\n": [(2, "A"), (3, "D")],
        "## A\n~~~\n### B\n```\n~~~\n### C\n": [(2, "A"), (3, "C")],
        "## A\n    ### B\n   ### C\n": [(2, "A"), (3, "C")],
        "## A\n```\n### B\n## C\n": [(2, "A")],
    }
    tc = trace_check()
    for text, expected in cases.items():
        assert headings(text) == expected, text
        assert tc.parse_units(text)[1] == [t for _l, t in expected], text


# Each section an entry of trace-exceptions.md excuses in a phase module, the interface variant files apart (pinned in
# test_phase_modules_close.py), and since TASK-017 in a conditional workflow (keyed `traits/<key>.md`), as FIX-004 found it: from its heading line to the next heading of its level or higher
# as trace-check.py reads them, LF, the whitespace at its end stripped; (length, sha256). trace-check.py excuses new
# text anywhere in such a section, so CI holds each section's text here. An increment that edits an excused section
# re-takes its pin in the same diff as its `reword` entry, and a reviewer reads the change to a pin as a new trace
# exception; an increment that adds an entry adds its section's pin.
EXCUSED_MODULE_SECTIONS = {
    ("change-cycle.md", "The procedure"): (6378, "02c6c662783f67e65f38c3394b4f4091c742ccb06bf1541db2568b077583a4ac"),
    ("change-cycle.md", "What must survive a compaction"): (1809, "789075c8285efd5644e0ae921872172221cf4441c7ee86730fea47d61ae7c6aa"),
    ("configuration.md", "Extension points"): (760, "036bd6b825c833494bbddbe5557f3cf70dfaa3b1cbc5c65c7bba1fa3ef31bae2"),
    ("configuration.md", "Keeping the position"): (613, "17547dab86d8b5b275f703e7380a6999d2aa31e414b8a85bfe9595d818135f10"),
    ("configuration.md", "The windowless test suite"): (1222, "54205dac21fc59bc8e203678d4cfc1a78a13f73765767a78fef8dea1fba2d315"),
    ("configuration.md", "What must survive a compaction"): (963, "338b5c4e338a41c95c7b9b2e1a110ed4e1473a8ad4ed04298359f8b21fd0984a"),
    ("delegation-loop.md", "2. Package the brief"): (964, "5394e345e8d43f10f2f9d98db2d5b092b96d0deea6e2dd75a4d3bb47b45e7e2e"),
    ("delegation-loop.md", "7. Decide — in a sub-file"): (241, "9146216638749b537ebdd42d28bdad75eb7ecfdafea1f8236bf90c7bb07c55ee"),
    ("delegation-loop.md", "Extension points"): (1696, "71ab68db2d7893030aa65e8136e44bba2d06a321490d2127803a47a4e9ad680d"),
    ("delegation-loop.md", "The model, the timeout and the limit"): (1976, "75dd79f1bb1b958f3aaece7bcbf8c38d53d4c24871d79448f02600e1dc1a1ccd"),
    ("delegation-loop.md", "The procedure"): (359, "43426ab85b1373afd99983578086509a127d152b6db6ef4c398de9d2aaf480f1"),
    ("delegation-loop.md", "The tests before the first reviewer"): (5981, "683cdccc08d3f310335c5ed96371f2eb451ded32930185971c24d1f41b1ab30c"),
    ("delegation-loop.md", "Waiting for the slot, and a mutation run cut short"): (2297, "54a9419f0b590d08b6c7b428ef80e12f0e3dfc2338c9694e5a436c24205d93b9"),
    ("delegation-loop.md", "What must survive a compaction"): (2971, "7b0aa4473dd3d8c041aa8c7efee5756d9ba73cb71446cc224058a3cdb239b705"),
    ("delegation-loop/decide.md", "The mutation run"): (5628, "44f27ca570e65d6e8f0d662b2eef25cc93c9fb4aaf2a6d3587ee47d35e9a0f18"),
    ("delegation-loop/decide.md", "Where this sub-file belongs"): (436, "9e38cf68a4da72d205ec742fe0d1cbf6f5c6e6bd75a04469b52333775ad19e01"),
    ("delegation-loop/refactoring-pass.md", "Keeping the pass's position"): (474, "16c05ddcf26b7cfb893f990cc227172f04ef2417dcce816df779b25abd84024b"),
    ("delegation-loop/refactoring-pass.md", "Where this sub-file belongs"): (451, "d5cc03c8c0b31688c8182cc8c13bd6ef7288eb85dcc32c95a7157929cfcb696c"),
    ("design.md", "A part without screens"): (268, "2a16dc74e42feea8823e7d580109fbed8dd2783aae9e58b8ea9fc36058211446"),
    ("design.md", "Extension points"): (761, "0084dfd13bf170a046f673a2312ed9580521c8be2a0a428b167b06aca65ffeb1"),
    ("design.md", "The delivery kind"): (494, "6b32868830fa9a36639468c4485c247450ad5d9337993b315eaed2480bf51dd5"),
    ("design.md", "The gate"): (3276, "811efda0ecdbcc72898697ee0027efe24d7e9a09c5263ab4919bb976cd5c8768"),
    ("design.md", "Traits at the design gate"): (3403, "653036f6b84c11afd94a9900be1477d23e9b839bc1c9e2eb933a0d03860a617b"),
    ("design.md", "What must survive a compaction"): (1824, "d9abbafd86416f3858cb865ca649ecfda5b4f47c167fd0691387079cc0234ea1"),
    ("intake.md", "Classifying each part"): (3492, "9b052cc643dd9fbb953f62dc8e62fa4a5750d37318b9b9d6da196e389632181e"),
    ("intake.md", "Extension points"): (1254, "4a0f40bda97f5ba7ea20d260c0262f88783a2018a5fb15d709625fe991c1bada"),
    ("intake.md", "The intake notes"): (495, "6a874f5d940b89189e58ee2ee281f3467a7571cf3b9d83d09076a3e02a6a3d25"),
    ("intake.md", "What must survive a compaction"): (1000, "7ea9c66e9a79abfbc187608754d2454ab2bf4a043998034b3778eeeaec15a533"),
    ("interface.md", "Extension points"): (694, "daf47b7c33ff4b4e4205551e1bf2a41e169e632c977c0412ec0a8e98820a2ca7"),
    ("interface.md", "The gate"): (687, "556436a8cbfa4707a771bc709bb8a33102b43c6643f60c90362503c0d748708a"),
    ("interface.md", "The interface notes"): (498, "e986453d03113ef18dc16f461414ef22045943fdd677f544a3df9e00886273a2"),
    ("interface.md", "The variants"): (1458, "926ec90a63bd7a60e8334e4c9046d870f1bddd016dd90f3169bd6104baf0fd8a"),
    ("interface.md", "What must survive a compaction"): (1489, "5b372267c3bf6f318492b4eae6f277d3619d0fd42039ceddc7f903c9c3f170b7"),
    ("interface.md", "Which variants a part runs"): (1922, "82a465d2e23ba652f9704bedd8abeb28d031fadb17385366063f4766a1593068"),
    ("planning.md", "Extension points"): (1220, "7c60fc3db2dd655458f81bae44119268990eb368b946e71acfb98eacd3750dfe"),
    ("planning.md", "Step 0 — Prior-project lessons (ask before drafting)"): (2264, "48550c1f28154614dad3e93db34babdca1eb5906c75c3288198be40d0f4af65a"),
    ("planning.md", "What must survive a compaction"): (1824, "8b60325b75200bd99b0800fd6f99b9e9fe9a44da4f9963bb75615d8942b33020"),
    ("planning.md", "What the interface phase hands to the plan"): (1239, "c0159380131640dd4e5c5d86d5cc6904a9cedc9d3eb4276dac36ecdeb9264e09"),
    ("project-end.md", "Extension points"): (1215, "b43b5ed92b4810f1da52e175f743c08db42a712311f25476bfa586af47ee56c6"),
    ("project-end.md", "Flagged traits in the promotion pass"): (1352, "882dd588f2b4e00b538bb37dc9ff64d590ada558b6bbc6094eb2fab17153eee5"),
    ("project-end.md", "Keeping the position"): (310, "e817d5b0593b8c3a9162d3463969c7034ee539ed8ca874e240bb2a82d56a29be"),
    ("project-end.md", "What must survive a compaction"): (1405, "8cf8d80f0852e598b6084dbd884f9a159de9eecce64ad1718553549e5f76277f"),
    ("project-end.md", "Where this module begins"): (321, "bbeaa6dac861483bec0e2e320a116a0d483739f69bb50facc302542288aaf75e"),
    ("reflection.md", "Extension points"): (738, "bd09934998929fba6d2139393c37232ec3e9c13622b402ce9ac264fb7b7b8228"),
    ("reflection.md", "Keeping the position"): (536, "197743ebea82a65f13ab634c7a4d70966457f1d3bc711817bed81386dcf22277"),
    ("reflection.md", "Project end"): (200, "9a6b3ec9d97b138b9e9f711b9fab7d9f2846fdc6a8a8a93b567da2ef05b96429"),
    ("reflection.md", "What must survive a compaction"): (1744, "c9ba058e4ac4fa6298c97d6ded26081b0368a5ea5e3518825a32839e3c987092"),
    ("reflection.md", "Whether a compaction preceded it"): (897, "ebc5c943f5efaf88ed526fe33cf0e9ffa9364891949c853d27f525a674969be4"),
    ("run-parameters.md", "Extension points"): (683, "5ef8d017187dfd16f8fa971a8e7ef3551136b497387f14e9477562f84331976c"),
    ("run-parameters.md", "What must survive a compaction"): (821, "d67698de27c0e6d55d3d347079911111df122fb0b3cb667fcb937b4ff1f55979"),
    ("run-parameters.md", "Writing the answers down"): (779, "ed3fe29e9fe1c96fa0348e57540a525572f2a646250b2adae046fc231b17b731"),
    ("traits/ai-models.md", "Add at configuration.items"): (1640, "4fd6accd73dbe9210a071eac20aff8753b354f0e990ce4d5398eee7c5674ee69"),
    ("traits/ai-models.md", "Add at delegation-loop.test-checks"): (1439, "84c9995cb323093cb1abe39966bd0052788f7fd99abff905a520abe75e5f9f38"),
    ("traits/ai-models.md", "Add at design.sections"): (325, "2f905de7f6e5d8b7f7c01c9f93afaeec794d9c20482ed2177211ac032b4f73da"),
    ("traits/ai-models.md", "Add at intake.questions"): (529, "20e891d7b9c1e96dd4f1c2951030ed089834e66ee50ab9548bac19c69092020a"),
    ("traits/external-services.md", "Add at delegation-loop.brief-constraints"): (273, "e19a9657e8871232fd956bf6e14673e86457026f88a1fbd564dcd926b32c5a32"),
    ("traits/external-services.md", "Add at delegation-loop.inspect-checks"): (439, "ff3dde12e5e044f461431458e96384a7f0f08a0e78a12b7daf74b63c38a7f3e1"),
    ("traits/external-services.md", "Add at delegation-loop.test-checks"): (419, "6e3340c6127ca19cfb60997566f496159c87685169f40cb94139e3e06b3884e7"),
    ("traits/external-services.md", "Add at planning.critic-lenses"): (533, "c850ed185641c6f69f3925e376c34d91be2c08df3de3b63d526e250b1d52113b"),
    ("traits/has-screens.md", "Add at interface.variants"): (623, "a427497d241df466c9c2d9140a6efb00392d90de8d23ef31b8e2df7a8af241f2"),
    ("traits/has-screens.md", "Add at planning.critic-lenses"): (843, "e33f771242637cec0ff3b0e641c304dbd93619ab35e5c5f510aef3a8243805fd"),
    ("traits/has-screens.md", "The Observability & Verifiability section"): (947, "11fa2639607592b1459f987f5001d0995649c703b0d1883b36952ee46d567b7a"),
    ("traits/has-screens.md", "The approved mockup and the frozen rule"): (243, "7053139bfab3ea1b0a7cbf4b5438523980a566c20ef1722fbd2ffeaa343f32de"),
    ("traits/installable.md", "Add at planning.critic-lenses"): (1170, "da8c4ceb8668b134252b51479f875f286f892a49cb695566978a9f90a88a2cc0"),
    ("traits/installable.md", "Add at project-end.delivery for install-script"): (274, "d362a1f64616d675f5352593568531e22e5fc3c918ed83a33a3962c02a1f3b8a"),
    ("traits/installable.md", "Code signing"): (308, "ed449346ff68fd449d3f7a1af719ba4547e34d1d74efdfde46f305a81e10ffb8"),
    ("traits/installable.md", "Which delivery kinds the Delivery section is for"): (236, "db56fef951c7aba1a67b796d4d85e19d2c58bcc218d0246737d0468591a82cac"),
    ("traits/installable.md", "Which delivery kinds the intake passage is for"): (273, "ac97680fd2fe85b751ea032c449418d2178ed307e0bbee73dade1c86f6379ea3"),
    ("traits/installable.md", "Which delivery kinds the packaging stage is for"): (295, "51a6686b489336f334218346d1514999765a3ee2f7a6dfad70d7595d22bd1df4"),
    ("traits/long-running-process.md", "Add at configuration.items"): (1126, "8c519174065a3fb315e7f683241cb1ab586f94d652d9830359089529b5a471b9"),
    ("traits/long-running-process.md", "Add at delegation-loop.brief-constraints"): (479, "dc52685ab9d4112a16acbe97a1731c5215ced74f88737ca6448822bb28d6fdc2"),
    ("traits/long-running-process.md", "Add at delegation-loop.test-checks"): (661, "812d870334a6574c22154268eec05a5dd3b0dc760bceafcf4318e748d1964c0e"),
    ("traits/performance-budgets.md", "Add at planning.critic-lenses"): (321, "464ee6c2b87edda66ee707a2081737826b3afa823d54c036df9afa2949d43b84"),
    ("traits/performance-budgets.md", "The mechanism and the hot path"): (488, "96fb8f084311c8ec4c9b853d3b6a71e50eb159055a22f03888f4d9a69a23b97d"),
    ("traits/spends-money.md", "Add at configuration.items"): (2322, "dbcc7b8d5fb3e4eda42bb6d3396512629a6669414e22b8b6e665344b70b0d441"),
    ("traits/spends-money.md", "Add at delegation-loop.brief-constraints"): (2913, "37d80c252e4339812e15640e300cd9f78c9a8a256ddff563f84fd3523b676d45"),
    ("traits/spends-money.md", "Add at delegation-loop.inspect-checks"): (1800, "0bdc70cf3839c1a26788f35b051f817c69a647383d643418b10930e14a51f73b"),
    ("traits/spends-money.md", "Add at delegation-loop.test-checks"): (1497, "133a4216403e747e802ca2e2e3fb340aefbe5ca44afa8cc3275bbe4dc3b99dba"),
    ("traits/spends-money.md", "Add at intake.questions"): (2438, "019900649a7ce0990e72dea2d6a5269278e81b39af37e24d732d1f4fb17040e9"),
    ("types/host-extension.md", "Add at delegation-loop.test-checks"): (1011, "a842e08d33314a8b6f2fb56aaf755f9752b653f7720241b370606c7c8a5749cb"),
    ("types/host-extension.md", "Add at design.sections"): (1211, "0829a69c1cd80b674258510f8a7b914e6c51ebfaea98e8780ff8443c466e4a72"),
    ("types/host-extension.md", "Add at project-end.delivery for host-installation"): (1034, "38cd3f1ebfb09f20b6b428b1501405254269304fef163d46715e81e8ab61ae70"),
    ("types/host-extension.md", "Set at intake.delivery-kind"): (49, "ffd70a04d0bbb9b542b511b490e14b414c23529b24996384687c10ebf29fcdb2"),
    ("types/host-extension/claude-code-extension.md", "Add at design.sections"): (666, "bd7b18f7ecb1499a0b526c079604b95e8c8080f2664166e71bd50b3f6491cdce"),
    ("types/own-computer.md", "Add at intake.questions"): (728, "caf1748cd3bdb56fe9109723467158c5a2dc4f319dd0fab07fb9b20180feb0b0"),
    ("types/own-computer/local-service.md", "Add at interface.variants"): (611, "7ddcb47b124539696c5a26a884ee52b3107282dbbc6e8be76ddc092002d50015"),
    ("types/web-app.md", "Add at project-end.delivery for web-deployment"): (6724, "689aa1ef2457273aeb2403eb876e29f788199d0760c7d8a228dd1490a159287d"),
    ("types/web-app.md", "Set at intake.delivery-kind"): (46, "2f7f51bb4c7b463f115afedb11af271b6040aba9852194f8fc6f3b522241f7f5"),
    ("types/web-app/local-web-app.md", "Set at intake.delivery-kind"): (46, "a1a429fb4f8905db0310a69eb9ed62f22f457d76e0e20044530163c83d2b32ee"),
}


def test_item2_the_pins_are_derived_from_the_entries():
    """Item 2: the pinned sections are exactly the sections the entries excuse in the phase modules (the interface
    variant files apart) and in the conditional workflows (TASK-017), so a new entry fails here until its section is pinned, and an entry withdrawn takes its pin
    with it; the thirteen sections stage B3's review counted are among them, with every other excused module section."""
    assert sorted(excused_module_sections()) == sorted(EXCUSED_MODULE_SECTIONS)


@pytest.mark.parametrize("rel,title", sorted(EXCUSED_MODULE_SECTIONS))
def test_item2_each_excused_module_section_has_one_heading_and_is_pinned(rel, title):
    """Item 2: the module has one heading of the excused title, as trace-check.py reads headings (a second would be
    excused unpinned), and the section under it, to where trace-check.py's reading ends it, is the pinned text."""
    lines = excused_file(rel).split("\n")
    same = [(i, level) for i, level, t in trace_headings(lines) if t == title]
    assert len(same) == 1, (rel, title, same)
    start, end = section_span(lines, title, same[0][1])
    body = "\n".join(lines[start:end]).rstrip()
    assert (len(body), hashlib.sha256(body.encode("utf-8")).hexdigest()) == EXCUSED_MODULE_SECTIONS[(rel, title)], len(body)
