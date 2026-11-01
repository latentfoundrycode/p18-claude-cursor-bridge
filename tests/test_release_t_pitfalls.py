"""R-054 (release T, TASK-036): the Known Pitfalls catalogue holds the report cycle's lessons, and D-004's first
deviation is closed by KP-038's narrowed text.

enforces: docs/REQUIREMENTS.md R-054; docs/BUILD_PLAN.md TASK-036, Done when; docs/diagrams/D-004-context-dfd.md (the
edge from the agents to the owner's profile stores, drawn as built); docs/diagrams/DEVIATIONS.md (D-004's first row
removed).

Each test pins an entry's number and title (its heading, once) and one sentence of it, by the item label of R-054's
row (D5, D13, T27, T13, P21). KP-052: the one non-ASCII character these pins need, the catalogue's em dash, is built
with chr(), never typed."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KP = os.path.join(ROOT, "bridge", "cursor-bridge", "Known-Pitfalls.md")
D004 = os.path.join(ROOT, "docs", "diagrams", "D-004-context-dfd.md")
DEV = os.path.join(ROOT, "docs", "diagrams", "DEVIATIONS.md")
DASH = chr(0x2014)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")


def heading(number, title):
    return "### KP-%03d %s %s\n" % (number, DASH, title)


def entry(text, number):
    """The entry's text, from its heading to the next heading or the end."""
    start = text.index("### KP-%03d " % number)
    nxt = text.find("\n### ", start + 1)
    return text[start:] if nxt < 0 else text[start:nxt]


def assert_entry(text, number, title, sentence):
    h = heading(number, title)
    assert text.count(h) == 1, "KP-%03d's heading, once: %r" % (number, h)
    assert text.count("### KP-%03d " % number) == 1, "KP-%03d is numbered once" % number
    body = entry(text, number)
    assert sentence in body, "KP-%03d holds: %r" % (number, sentence)
    for part in ("- **Surfaced:**", "- **Correction", "- **Applies:**"):
        assert part in body, "KP-%03d keeps the catalogue's four-part shape (%s)" % (number, part)
    assert "- **Misconception:**" in body or "- **Mistake:**" in body or "- **Temptation:**" in body, number


def test_r054_d5_kp061_outcome_line_corrected():
    """D5: KP-061's outcome line says the app moved the suite's command to the background and the result was waited
    for; the rule stands. The heading stays as tests/test_a5_followups.py pins it."""
    kp = read(KP)
    assert_entry(kp, 61, "A test suite over ten minutes ended inside a subagent's foreground call",
                 "at the ten-minute limit the app moved the suite's command to the background, and the result was "
                 "waited for and read, not lost")
    assert "and the result was lost." not in entry(kp, 61), "the wrong outcome line is gone"
    assert "The rule stands" in entry(kp, 61)


def test_r054_d13_kp063_to_kp065():
    """D13: a provider's bill in its own unit, failed attempts included; a harness below the product's entry point; a
    driver anchored on a moved line."""
    kp = read(KP)
    assert_entry(kp, 63, "A provider's bill is in its own unit, failed attempts included",
                 "a cap is set in the provider's own billing unit, every failed or retried attempt counted at its price")
    assert_entry(kp, 64, "A harness that calls below the product's entry point creates a state the product cannot",
                 "a harness drives the product's own entry points (its command, its API, its screen), never a function "
                 "the product wraps")
    assert_entry(kp, 65, "A mutation driver anchored on a line a fix moved matches nothing while its results claim a kill",
                 "a mutant that applies nowhere is never a kill")


def test_r054_t27_kp066_to_kp070_and_the_kp058_addendum():
    """T27: a security floor trusted before it ran; git show --output creates the file empty (the KP-067
    review-guard.py already cites); a vendor banner's partial key; a squash-merged pre-gate status file; a naive
    local-time schedule walk; and KP-058's addendum on working-folder defaults."""
    kp = read(KP)
    assert_entry(kp, 66, "A security floor trusted before it ran against the real service",
                 "a floor's first increment runs each scanner against the real service and reads its log")
    assert_entry(kp, 67, "`git show <rev>:<path> --output=<file>` creates the file empty",
                 "`review-guard.py snapshot` lists every review input under `run/review/` with its size and refuses an "
                 "empty one, citing this entry")
    assert_entry(kp, 68, "A vendor CLI's banner printed part of a key into a public repository's CI logs",
                 "GitHub masks a secret only where the whole value appears")
    assert_entry(kp, 69, "A squash-merged status file describes the pre-gate state on `main`",
                 "every pull request carries the status file as it reads at that pull request's merge")
    assert_entry(kp, 70, "A wall-clock schedule walked in naive local time never revisits the hour that repeats when "
                         "summer time ends",
                 "a schedule walk iterates over instants and converts each to wall time")
    assert ("- **Addendum (2026-11-01):** a test that runs a program with working-folder defaults reads the live state "
            "of the folder it runs from") in entry(kp, 58), "KP-058's addendum (ISS-006)"


def test_r054_t13_kp052_corrected():
    """T13: no tool is safe for a typed backslash-u escape: chr() in a test, the code point in a document, a byte
    search after a write that quotes one."""
    kp = read(KP)
    assert_entry(kp, 52, "An escape typed in a here-document arrived as the real character",
                 "no tool is safe for a typed backslash-u escape, the Write and Edit tools included")
    body = entry(kp, 52)
    for clause in ("a test builds such a character with `chr()`", "a document names it by its code point",
                   "searched for the character's bytes after it is written"):
        assert clause in body, clause


def test_r054_p21_kp071_to_kp074():
    """P21: KP-071 to KP-074 from release B's Issues (ISS-016, ISS-021, ISS-023, ISS-022)."""
    kp = read(KP)
    assert_entry(kp, 71, "A test that patches a standard-library function records the library's own calls",
                 "replaces the module's own binding (`monkeypatch.setattr(mod, \"time\", stand_in)`)")
    assert_entry(kp, 72, "A count seeded from files another mechanism also writes",
                 "a seed names what writes its files before and after the release that seeds it")
    assert_entry(kp, 73, "A check that scans shipped code found its own description",
                 "a check that scans shipped code runs once on its own repository before its release")
    assert_entry(kp, 74, "Status-file tests gated on CI variables skip locally",
                 "`GITHUB_REF=refs/pull/<n>/merge`, `GITHUB_BASE_REF=main` and `GITHUB_EVENT_NAME=pull_request`")


def test_r054_kp038_narrowed_and_d004_first_deviation_closed():
    """KP-038 says what the code does: the stores under the profile root are not found by default, a store reached
    through APPDATA or LOCALAPPDATA is, until a probed release redirects them. D-004 draws the edge so, and
    DEVIATIONS.md no longer lists it (the design corrected to the code, conventions section 8's second case)."""
    kp = read(KP)
    body = entry(kp, 38)
    assert ("the owner's stores under the profile root (`.ssh`, `.aws`, `.docker` and the like) are no longer found "
            "by default; a store a tool reaches through `APPDATA` or `LOCALAPPDATA` still is") in body
    assert "`.docker` and other stores are no longer found by default" not in body, "the over-wide sentence is gone"
    d004 = read(D004)
    assert "(DEVIATIONS; KP-038 narrowed)" not in d004, "the edge no longer marks a deviation"
    assert ("found by default: ~/AppData through APPDATA and LOCALAPPDATA, which stay the owner's until a probed "
            "release redirects them (KP-038)") in d004
    dev = read(DEV)
    assert "| D-004 | p_bridge_env |" not in dev, "D-004's first deviation is removed"
    assert dev.count("| D-004 |") == 2, "D-004's two other rows stay (TASK-041, TASK-043)"
