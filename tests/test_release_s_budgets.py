"""Release S (S1, S6): two word budgets in place of the per-file size caps and the size and hash pins.

1. The rulebook's total: every instruction text the bridge installs, counted in words. A change that needs more raises the number
   here, in its own pull request, where a reviewer sees it: a new rule is paid for by retiring one (the rule budget).
2. What a resumed supervisor must re-read: the hook names the phase's files and asks for the ONE that holds the step in hand, so the
   cost of a compaction is bounded by the largest file the hook can name for any phase.

Both are counted the plain way, `len(text.split())`, so anyone can check a number with one line. The digest's own cap (9,500
characters, under Claude Code's 10,000 for a hook's output) stays where it is, in tests/test_session_start.py.

Register: R-066's two budgets are test_the_rulebook_stays_within_its_word_budget and
test_the_file_of_any_step_stays_within_what_one_re_read_may_cost; R-069's one file of the step in hand is
test_the_hook_asks_for_one_file_of_the_step_and_not_the_phase_s_whole_list."""
import importlib.util
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
BRIDGE = os.path.abspath(os.path.join(HERE, os.pardir, "bridge"))
PHASES = os.path.join(BRIDGE, "cursor-bridge", "workflow", "phases")

RULEBOOK_WORDS = 150000        # the rulebook stood at 149,668 words when release S began (2026-11-11)
STEP_FILE_WORDS = 8000         # the largest file of a step: the delegation loop's module, 7,550 words then


def words(path):
    with open(path, encoding="utf-8") as f:
        return len(f.read().split())


def rulebook():
    """Every Markdown text under bridge/ that instructs: the release notes (a history, which only grows) and the design seeds
    (reference designs, read one at a time when a mockup is drawn) are not rules."""
    found = {}
    for folder, _dirs, names in os.walk(BRIDGE):
        for name in names:
            path = os.path.join(folder, name)
            rel = os.path.relpath(path, BRIDGE).replace(os.sep, "/")
            if name.endswith(".md") and rel != "cursor-bridge/CHANGELOG.md" and "/design-seeds/" not in "/" + rel:
                found[rel] = words(path)
    return found


def test_the_rulebook_stays_within_its_word_budget():
    counted = rulebook()
    total = sum(counted.values())
    largest = ", ".join("%s %d" % (rel, n) for rel, n in sorted(counted.items(), key=lambda kv: -kv[1])[:5])
    assert total <= RULEBOOK_WORDS, ("the rulebook holds %d words, over its budget of %d: retire text for what was added, or raise RULEBOOK_WORDS "
                                     "in this pull request and say why (largest: %s)" % (total, RULEBOOK_WORDS, largest))
    assert len(counted) > 40 and counted["commands/supervisor.md"] > 5000, "the count reads the installed texts, the core among them"


def hook():
    spec = importlib.util.spec_from_file_location("session_start_budget", os.path.join(BRIDGE, "cursor-bridge", "session-start.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def step_files():
    """{phase: the phase files the hook can name for it}: the hook's own table of modules, and each module's `Sub-files:` and
    `Variants:` lines as the hook's pattern reads them."""
    h = hook()
    out = {}
    for phase, modules in h.PHASE_MODULES.items():
        files = []
        for key in modules:
            files.append(key + ".md")
            with open(os.path.join(PHASES, key + ".md"), encoding="utf-8") as f:
                for line in f.read().splitlines():
                    for prefix in ("Sub-files: ", "Variants: "):
                        if line.startswith(prefix):
                            files += [p for p in line[len(prefix):].rstrip().split("; ") if h.POINTER_PATH.fullmatch(p)]
        out[phase] = files
    return out


def test_the_file_of_any_step_stays_within_what_one_re_read_may_cost():
    named = step_files()
    assert named["building"][:4] == ["delegation-loop.md", "delegation-loop/decide.md", "delegation-loop/refactoring-pass.md", "delegation-loop/merge.md"], named["building"]
    over = sorted((words(os.path.join(PHASES, *rel.split("/"))), phase, rel) for phase, files in named.items() for rel in files
                  if words(os.path.join(PHASES, *rel.split("/"))) > STEP_FILE_WORDS)
    assert not over, "a file the hook names for one step is over %d words (split it into the module's sub-files): %s" % (STEP_FILE_WORDS, over)


def test_the_hook_asks_for_one_file_of_the_step_and_not_the_phase_s_whole_list():
    """The budget above bounds a re-read only while the hook asks for one file: its sentence says so, and no line of its output
    asks for a reference text whole."""
    h = hook()
    assert "the ONE phase file" in h.READ_ONE and "the other phase files when the work reaches their step" in h.READ_ONE
    source = open(os.path.join(BRIDGE, "cursor-bridge", "session-start.py"), encoding="utf-8").read()
    assert not re.search(r'"  - and %s, whole"', source) and '"  - on demand: %s"' in source
