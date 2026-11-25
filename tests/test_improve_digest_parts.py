"""R-109, TASK-087b: the digest in two parts. The digest between its markers in supervisor.md holds one line
`<!-- digest:part -->` directly before its standing rules; the SessionStart hook prints the text before that line
under `--part digest` and the text after it under `--part digest-2`, each under a header of its own and each cut by
the hook's `cap` at `MAX_OUTPUT`; the bridge's settings register the second part as a SessionStart group of its own,
which the installer appends once to a home that holds 2026.11.23a's entries and the rollback takes out alone.

The host probe (run/supervisor/probe-087b.md, Claude Code 2.1.330) delivered three outputs whole: 2,700, 8,800 and 8,800
characters, one of 9,400 bytes; so a part prints at most 8,800 characters of text under its header, and the whole digest
stays at most 10,500.

Mutation labels the tests name (the mutants file sweeps the split):
  K1  the second part never printed;
  K2  the marker printed inside a part;
  K3  the first part printing the whole digest beside the second;
  K4  the second part printed uncut by the cap.

Every hook run is a subprocess with the windowless creation flag; the installer is loaded as a module and its
replace_release runs on fake release trees and a scratch home under pytest's tmp_path, never the real home."""
import copy
import json
import os
import re
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
CLAUDE = os.path.abspath(os.path.join(HERE, os.pardir, "bridge"))
PROG = os.path.join(CLAUDE, "cursor-bridge", "session-start.py")
SV = os.path.join(CLAUDE, "commands", "supervisor.md")
SETTINGS_PATH = os.path.join(CLAUDE, "cursor-bridge", "settings.bridge.json")

START = "<!-- digest:start -->"
END = "<!-- digest:end -->"
MARK = "<!-- digest:part -->"
HOST_CAP = 10000            # Claude Code's cap on a hook's plain output; the host's unit is not stated, so characters and bytes
PART_MAX = 8800             # the most a part may hold (the probe's number)
WHOLE_MAX = 10500           # the most the whole digest may hold
SECOND = re.compile(r"second part|part 2\b|part two|digest-2|2 of 2|two of two", re.I)
WIDE = "→"             # three bytes in UTF-8

PREVIOUS_VERSION = "2026.11.23a"
POINTERS_CMD = 'python "$HOME/.claude/cursor-bridge/session-start.py" --part pointers'
DIGEST_CMD = 'python "$HOME/.claude/cursor-bridge/session-start.py" --part digest'
DIGEST2_CMD = 'python "$HOME/.claude/cursor-bridge/session-start.py" --part digest-2'
# 2026.11.23a's SessionStart entries: one group, the pointers and the digest.
PREVIOUS_GROUP = {"matcher": "compact|resume|fork", "hooks": [
    {"type": "command", "command": POINTERS_CMD, "timeout": 20},
    {"type": "command", "command": DIGEST_CMD, "timeout": 20},
]}


def installed_version():
    with open(os.path.join(CLAUDE, "cursor-bridge", "VERSION"), encoding="utf-8-sig") as f:
        return f.read().strip().split()[0]


def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def bridge_settings():
    with open(SETTINGS_PATH, encoding="utf-8-sig") as f:
        return json.load(f)


# ---------------------------------------------------------------------------------------------------------------
# Helpers: a scratch home and project, the hook run windowless, a synthetic supervisor.md.

def run_hook_bytes(cwd, home, part):
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home))
    data = json.dumps({"cwd": str(cwd), "hook_event_name": "SessionStart", "source": "compact"}).encode("utf-8")
    p = subprocess.run([sys.executable, PROG, "--part", part], input=data, capture_output=True, env=env,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return p.returncode, p.stdout


def run_hook(cwd, home, part):
    rc, raw = run_hook_bytes(cwd, home, part)
    return rc, raw.decode("utf-8").replace("\r\n", "\n")


def make_home(tmp_path, supervisor_text):
    h = tmp_path / "home"
    (h / ".claude" / "commands").mkdir(parents=True)
    (h / ".claude" / "commands" / "supervisor.md").write_text(supervisor_text, encoding="utf-8", newline="\n")
    return h


def make_project(tmp_path):
    root = tmp_path / "proj"
    (root / "Workspace" / "docs").mkdir(parents=True)
    (root / "Workspace" / "docs" / "PROJECT_STATUS.md").write_text(
        "# Project Status\nPhase: building (Stage 2)\nAwaiting user on: nothing\n", encoding="utf-8")
    return root / "Workspace"


def synthetic_supervisor(part1, part2=None):
    """A supervisor.md whose digest is `part1`, then the marker line and `part2` where `part2` is given."""
    digest = part1 if part2 is None else part1 + "\n" + MARK + "\n" + part2
    return ("---\ndescription: synthetic\n---\n\n# Role: Supervising Architect\n\n"
            + START + "\n" + digest + "\n" + END + "\n\n## The rest of the rulebook\n\nNot part of the digest.\n")


def block(start, end, total, wide=0):
    """Text of exactly `total` characters from `start` to `end`, `wide` of them three-byte characters,
    a line break every hundred characters, nothing blank at either end."""
    n = total - len(start) - len(end) - 2
    out, w = [], wide
    for i in range(n):
        if i % 100 == 99:
            out.append("\n")
        elif w and i % 3 == 0:
            out.append(WIDE)
            w -= 1
        else:
            out.append("x")
    assert w == 0
    text = start + "\n" + "".join(out) + "\n" + end
    assert len(text) == total and text == text.strip()
    return text


def head_of(out, body):
    """The header printed before `body`: `body` stands once, nothing but white space follows it."""
    assert out.count(body) == 1, "the part's text must stand once in the output"
    i = out.index(body)
    assert out[i + len(body):].strip() == "", "nothing but white space follows the part's text: %r" % out[i + len(body):][:200]
    head = out[:i].strip()
    assert head, "the part is printed under a header"
    return head


def file_parts(text):
    """(whole slice from the start marker to the end marker, part one, part two) of a supervisor.md, the parts as
    the hook prints them: the digest's text before the marker line and after it, without white space at either end."""
    a, b = text.find(START), text.find(END)
    assert 0 <= a < b
    digest = text[a + len(START):b].strip()
    lines = digest.split("\n")
    at = [k for k, line in enumerate(lines) if line.strip() == MARK]
    assert len(at) == 1, "the digest holds the line %s exactly once (found %d)" % (MARK, len(at))
    return text[a:b], "\n".join(lines[:at[0]]).strip(), "\n".join(lines[at[0] + 1:]).strip()


ALPHA = block("ALPHA-START first part of the digest", "ALPHA-END", 1200)
OMEGA = block("OMEGA-START **Standing rules.** second part", "OMEGA-END", 1500)


@pytest.fixture
def split_setup(tmp_path):
    home = make_home(tmp_path, synthetic_supervisor(ALPHA, OMEGA))
    return home, make_project(tmp_path)


# ---------------------------------------------------------------------------------------------------------------
# The hook: each part, its header, a digest without the line.

def test_r109_part_digest_prints_its_header_and_the_text_before_the_line(split_setup):
    """R-109, TASK-087b, Done when: `session-start.py --part digest` prints its header and the digest's text before
    the line `<!-- digest:part -->`. Mutations K3 (the first part printing the whole digest beside the second) and
    K2 (the marker printed inside a part)."""
    home, cwd = split_setup
    rc, out = run_hook(cwd, home, "digest")
    assert rc == 0
    assert "OMEGA-START" not in out and "OMEGA-END" not in out, "K3: the first part holds nothing after the line"
    assert "digest:part" not in out, "K2: the marker line is never printed"
    head = head_of(out, ALPHA)
    first = head.splitlines()[0]
    assert "CLAUDE-CURSOR BRIDGE core digest" in first and "(bridge %s)" % installed_version() in first, first


def test_r109_part_digest_2_prints_a_header_of_its_own_and_the_text_after_the_line(split_setup):
    """R-109, TASK-087b, Done when: `--part digest-2` prints a header of its own that names the second part and the
    installed version, then the text after the line (red on the checkpoint, which prints nothing for that part).
    Mutations K1 (the second part never printed) and K2 (the marker printed inside a part)."""
    home, cwd = split_setup
    rc, out = run_hook(cwd, home, "digest-2")
    assert rc == 0
    assert out.strip(), "K1: the second part is printed"
    assert "ALPHA-START" not in out and "ALPHA-END" not in out, "the second part holds nothing before the line"
    assert "digest:part" not in out, "K2: the marker line is never printed"
    head = head_of(out, OMEGA)
    assert installed_version() in head, "the second part's header names the installed version: %r" % head
    assert SECOND.search(head), "the second part's header names the second part: %r" % head
    _rc1, out1 = run_hook(cwd, home, "digest")
    assert head != head_of(out1, ALPHA), "the second part's header is its own, not the first part's"


def test_r109_part_all_prints_the_pointers_and_both_parts(split_setup):
    """R-109, TASK-087b, Done when: `--part all` prints the pointers and both parts. Mutations K1 (the second part
    never printed), K2 (the marker printed inside a part) and K3 (the first part printing the whole digest beside
    the second)."""
    home, cwd = split_setup
    rc, out = run_hook(cwd, home, "all")
    assert rc == 0
    assert "PROJECT STATE: Phase: building" in out, "the pointers are printed"
    assert out.count("ALPHA-START") == 1 and out.count("ALPHA-END") == 1, "K3: the first part is printed once"
    assert out.count("OMEGA-START") == 1 and out.count("OMEGA-END") == 1, "K1/K3: the second part is printed once"
    assert "digest:part" not in out, "K2: the marker line is never printed"
    assert out.index("PROJECT STATE") < out.index("ALPHA-START") < out.index("OMEGA-START")
    between = out[out.index("ALPHA-END") + len("ALPHA-END"):out.index("OMEGA-START")]
    assert installed_version() in between and SECOND.search(between), "the second part stands under its own header: %r" % between


def test_r109_a_digest_without_the_line_is_printed_whole_and_the_second_part_prints_nothing(tmp_path):
    """R-109, TASK-087b, Done when: a digest without the line is printed whole by `--part digest`, as on the
    checkpoint, and `--part digest-2` then prints nothing. Mutation K3 (the first part printing the whole digest
    beside the second: here no second part may echo it)."""
    whole = ALPHA + "\n\n" + OMEGA
    home = make_home(tmp_path, synthetic_supervisor(whole))
    cwd = make_project(tmp_path)
    rc, out = run_hook(cwd, home, "digest")
    assert rc == 0
    head = head_of(out, whole)
    first = head.splitlines()[0]
    assert "CLAUDE-CURSOR BRIDGE core digest" in first and "(bridge %s)" % installed_version() in first, first
    assert "cut at" not in out
    rc2, out2 = run_hook(cwd, home, "digest-2")
    assert rc2 == 0 and out2.strip() == "", "without the line the second part prints nothing: %r" % out2[:300]


# ---------------------------------------------------------------------------------------------------------------
# The cap: each part cut at MAX_OUTPUT as on the checkpoint, the constant unchanged, the note naming the part.

def test_r109_max_output_is_unchanged(program):
    """R-109, TASK-087b, Done when: each part is cut by the hook's `cap` at `MAX_OUTPUT` as on the checkpoint, the
    constant unchanged (9,800). Mutation K4 (the second part printed uncut by the cap)."""
    mod = program("session-start")
    assert mod.MAX_OUTPUT == 9800


@pytest.mark.parametrize("part", ["digest", "digest-2"])
def test_r109_each_part_is_cut_by_the_cap_and_the_note_names_the_part(tmp_path, program, part):
    """R-109, TASK-087b, Done when: each part is cut by the hook's `cap` at `MAX_OUTPUT` as on the checkpoint (the
    header and the part's text together, the note starting at MAX_OUTPUT - 90 characters), and the cut's note names
    the part. Mutation K4 (the second part printed uncut by the cap); the first part's case holds the cap's place."""
    limit = program("session-start").MAX_OUTPUT
    big1 = block("ALPHA-START long first part", "ALPHA-END", 12000)
    big2 = block("OMEGA-START long second part", "OMEGA-END", 12000)
    home = make_home(tmp_path, synthetic_supervisor(big1, big2))
    cwd = make_project(tmp_path)
    rc, out = run_hook(cwd, home, part)
    assert rc == 0
    text = out.rstrip("\n")
    assert "ALPHA-END" not in text and "OMEGA-END" not in text, "K4: the part is cut"
    assert len(text) < HOST_CAP, "K4: the cut part stays under the host's cap (%d)" % len(text)
    at = text.rfind("\n[")
    assert at == limit - 90, "the cap keeps MAX_OUTPUT - 90 characters of the header and the part (note at %d)" % at
    note = text[at + 1:]
    assert "cut at %d characters" % limit in note, note
    assert "\n" not in note, note
    if part == "digest-2":
        assert "OMEGA-START" in text and "ALPHA-START" not in text
        assert SECOND.search(note), "the second part's cut note names the second part: %r" % note
    else:
        assert "ALPHA-START" in text and "OMEGA-START" not in text
        assert "digest" in note and not SECOND.search(note), "the first part's cut note names the first part: %r" % note


# ---------------------------------------------------------------------------------------------------------------
# A part at its cap under the host's number, in characters and in bytes.

@pytest.mark.parametrize("larger", ["first", "second"])
def test_r109_a_part_of_8800_characters_300_of_three_bytes_prints_whole_under_the_host_cap(tmp_path, larger):
    """R-109, TASK-087b, Done when: the hook's own test prints each part with its header from a digest whose larger
    part is exactly 8,800 characters, 300 of them characters of three bytes, and asserts no cut mark, fewer than
    10,000 characters and fewer than 10,000 bytes (the host's unit is not stated). Mutations K1 (the second part never
    printed) and K3 (the first part printing the whole digest beside the second, which would pass the cap and be cut)."""
    big = block("BIG-START the larger part", "BIG-END", PART_MAX, wide=300)
    small = block("SMALL-START the smaller part", "SMALL-END", 1700)
    part1, part2 = (big, small) if larger == "first" else (small, big)
    home = make_home(tmp_path, synthetic_supervisor(part1, part2))
    cwd = make_project(tmp_path)
    for part, body in (("digest", part1), ("digest-2", part2)):
        rc, raw = run_hook_bytes(cwd, home, part)
        assert rc == 0
        out = raw.decode("utf-8")
        norm = out.replace("\r\n", "\n")
        head_of(norm, body)
        assert "cut at" not in out and "by the hook's cap" not in out, "%s: no cut mark" % part
        assert len(out) < HOST_CAP, "%s: %d characters" % (part, len(out))
        assert len(raw) < HOST_CAP, "%s: %d bytes" % (part, len(raw))


def test_r109_each_part_of_the_digest_as_it_stands_prints_whole_under_the_host_cap(tmp_path):
    """R-109, TASK-087b, Done when: the hook's own test asserts of each part of the digest as it stands in
    bridge/commands/supervisor.md: printed with its header, no cut mark, fewer than 10,000 characters and fewer than
    10,000 bytes. Mutations K1 (the second part never printed) and K4 (the second part printed uncut by the cap)."""
    text = read_text(SV)
    _whole, part1, part2 = file_parts(text)
    home = make_home(tmp_path, text)
    cwd = make_project(tmp_path)
    for part, body in (("digest", part1), ("digest-2", part2)):
        rc, raw = run_hook_bytes(cwd, home, part)
        assert rc == 0
        out = raw.decode("utf-8")
        norm = out.replace("\r\n", "\n")
        assert norm.strip(), "%s: printed" % part
        head_of(norm, body)
        assert MARK not in norm
        assert "cut at" not in out and "by the hook's cap" not in out, "%s: no cut mark" % part
        assert len(out) < HOST_CAP, "%s: %d characters" % (part, len(out))
        assert len(raw) < HOST_CAP, "%s: %d bytes" % (part, len(raw))


# ---------------------------------------------------------------------------------------------------------------
# The digest as it stands: the line in its place, the whole and each part within their numbers.

def test_r109_the_digest_holds_the_line_once_directly_before_its_standing_rules():
    """R-109, TASK-087b, Done when: the digest between its markers holds one line `<!-- digest:part -->` directly
    before its standing rules. Mutation K1 (the second part never printed: without the line there is none)."""
    text = read_text(SV)
    a, b = text.find(START), text.find(END)
    assert 0 <= a < b
    lines = text.splitlines()
    assert sum(1 for line in lines if line.strip() == MARK) == 1, "the file holds the line once"
    digest_lines = text[a:b].splitlines()
    at = [k for k, line in enumerate(digest_lines) if line.strip() == MARK]
    assert len(at) == 1, "the line stands between the digest's markers"
    following = [line for line in digest_lines[at[0] + 1:] if line.strip()]
    assert following and following[0].startswith("**Standing rules.**"), "the line stands directly before the standing rules"


def test_r109_the_whole_digest_is_at_most_10500_and_each_part_at_most_8800():
    """R-109, TASK-087b, Done when: the whole digest at most 10,500 characters (the slice from the start marker to the
    end marker, as the four tests measured 9,500) and each part at most 8,800 (its text as the hook prints it).
    Mutation K4 (the second part printed uncut by the cap: a part within 8,800 never reaches the cap)."""
    whole, part1, part2 = file_parts(read_text(SV))
    assert len(whole) <= WHOLE_MAX, "the whole digest is %d characters" % len(whole)
    assert len(part1) <= PART_MAX, "the first part is %d characters" % len(part1)
    assert len(part2) <= PART_MAX, "the second part is %d characters" % len(part2)


# ---------------------------------------------------------------------------------------------------------------
# The settings: a second SessionStart group, and the installer's merge and rollback.

def test_r109_the_settings_gain_a_second_session_start_group_for_the_second_part():
    """R-109, TASK-087b, Done when: the hook settings gain a second `SessionStart` entry, a group of its own with the
    first one's matcher and timeout and the one command `--part digest-2`. Mutation K1 (the second part never
    printed: the host runs only what the settings name)."""
    groups = bridge_settings()["hooks"]["SessionStart"]
    assert len(groups) == 2, groups
    first, second = groups
    assert first == PREVIOUS_GROUP, "the first group is unchanged"
    assert second == {"matcher": first["matcher"], "hooks": [
        {"type": "command", "command": DIGEST2_CMD, "timeout": first["hooks"][0]["timeout"]}]}, second
    cmds = [h["command"] for g in groups for h in g["hooks"]]
    assert cmds.count(DIGEST2_CMD) == 1 and cmds.count(DIGEST_CMD) == 1 and cmds.count(POINTERS_CMD) == 1


def fake_release(folder, version, settings):
    """A release tree holding only cursor-bridge/settings.bridge.json and its manifest: no shim, no bridge_env.py,
    so replace_release touches nothing outside the scratch folders."""
    cb = folder / "cursor-bridge"
    cb.mkdir(parents=True)
    (cb / "settings.bridge.json").write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    (cb / "MANIFEST.json").write_text(json.dumps(
        {"version": version, "files": {"cursor-bridge/settings.bridge.json": "0" * 64}}, indent=2) + "\n", encoding="utf-8")
    return folder


def test_r109_the_installer_appends_the_new_group_once_and_the_rollback_removes_it_alone(tmp_path, program, monkeypatch, capsys):
    """R-109, TASK-087b, Done when: a test merges the release's settings into a scratch home that holds 2026.11.23a's
    entries and finds the older group unchanged and the new one appended once, a second merge changing nothing and
    the rollback removing the new group alone. Mutation K1 (the second part never printed: an install that does not
    register it leaves it unrun)."""
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "localappdata"))
    bi = program("bridge-install")
    new_settings = bridge_settings()
    assert len(new_settings["hooks"]["SessionStart"]) == 2, "the release's settings hold the second part's group"
    old_settings = copy.deepcopy(new_settings)
    old_settings["hooks"]["SessionStart"] = [copy.deepcopy(PREVIOUS_GROUP)]
    new_tree = fake_release(tmp_path / "release-new", installed_version(), new_settings)
    old_tree = fake_release(tmp_path / "kept" / PREVIOUS_VERSION, PREVIOUS_VERSION, old_settings)

    target = tmp_path / "home" / ".claude"
    fake_release(target, PREVIOUS_VERSION, old_settings)   # the installed 2026.11.23a
    owner_group = {"matcher": "startup", "hooks": [{"type": "command", "command": "echo owner"}]}
    owner = {"theme": "dark", "permissions": {"allow": ["Bash(ls:*)"]}, "hooks": {"SessionStart": [owner_group]}}
    before = bi.merge_settings(owner, old_settings)[0]
    settings_path = str(target / "settings.json")
    bi.write_settings(settings_path, before)
    assert before["hooks"]["SessionStart"] == [owner_group, PREVIOUS_GROUP]

    bi.replace_release(str(target), str(new_tree), bi.read_settings(settings_path), new_settings, False)
    after = bi.read_settings(settings_path)
    groups = after["hooks"]["SessionStart"]
    new_group = new_settings["hooks"]["SessionStart"][1]
    assert groups == [owner_group, PREVIOUS_GROUP, new_group], groups
    assert sum(1 for g in groups for h in g["hooks"] if h.get("command") == DIGEST2_CMD) == 1, "appended once"
    rest_after = {k: v for k, v in after.items() if k != "hooks"}
    rest_before = {k: v for k, v in before.items() if k != "hooks"}
    assert rest_after == rest_before, "nothing else of the settings changes"
    assert {e: v for e, v in after["hooks"].items() if e != "SessionStart"} == {e: v for e, v in before["hooks"].items() if e != "SessionStart"}

    with open(settings_path, encoding="utf-8") as f:
        written = f.read()
    bi.replace_release(str(target), str(new_tree), bi.read_settings(settings_path), new_settings, False)
    with open(settings_path, encoding="utf-8") as f:
        assert f.read() == written, "a second merge changes nothing"

    bi.replace_release(str(target), str(old_tree), bi.read_settings(settings_path), old_settings, False)
    back = bi.read_settings(settings_path)
    assert back == before, "the rollback removes the new group alone"
    assert back["hooks"]["SessionStart"] == [owner_group, PREVIOUS_GROUP]
    capsys.readouterr()

# ---------------------------------------------------------------------------------------------------------------
# Round 2 (handoff/TASK-087b-r2.md): the gate's round-1 findings, each case naming its requirement and finding.
# Mutation labels: K5 a cut note longer than the room the cap leaves; K6 a placeholder that says no digest was found
# beside a digest; K7 a later marker line printed inside a part; K8 a part with nothing to print writing a line feed.

@pytest.mark.parametrize("part", ["digest", "digest-2"])
def test_r2_a_cut_part_never_passes_max_output(tmp_path, program, part):
    """R-109, TASK-087b round 2, Requirement 1 (Review A and the security audit, R4): a part cut by the cap, its note
    included, is at most MAX_OUTPUT characters; the note still names its part. Mutation K5 (a cut note longer than the
    room the cap leaves)."""
    limit = program("session-start").MAX_OUTPUT
    big1 = block("ALPHA-START long first part", "ALPHA-END", 12000)
    big2 = block("OMEGA-START long second part", "OMEGA-END", 12000)
    home = make_home(tmp_path, synthetic_supervisor(big1, big2))
    cwd = make_project(tmp_path)
    rc, out = run_hook(cwd, home, part)
    assert rc == 0
    text = out.rstrip("\n")
    assert "cut at %d characters" % limit in text
    assert len(text) <= limit, "K5: the cut %s is %d characters, over MAX_OUTPUT (%d)" % (part, len(text), limit)
    note = text[text.rfind("\n[") + 1:]
    if part == "digest-2":
        assert SECOND.search(note), note
    else:
        assert not SECOND.search(note), note


def test_r2_a_marker_first_never_says_no_digest_was_found(tmp_path):
    """R-109, TASK-087b round 2, Requirement 3 (Review A, should-fix): where the marker stands first, so the first
    part is empty, `--part digest` prints its header and never the words that no digest was found, since there is
    one; `--part digest-2` prints the text after the marker. Mutation K6 (a placeholder that says no digest was found
    beside a digest)."""
    home = make_home(tmp_path, synthetic_supervisor("", OMEGA))
    cwd = make_project(tmp_path)
    rc, out = run_hook(cwd, home, "digest")
    assert rc == 0
    first = out.strip().splitlines()[0]
    assert "CLAUDE-CURSOR BRIDGE core digest" in first and "(bridge %s)" % installed_version() in first, first
    assert "no digest found" not in out, "K6: a digest stands in the file; the empty first part says otherwise: %r" % out[:400]
    assert "OMEGA-START" not in out and "digest:part" not in out
    rc2, out2 = run_hook(cwd, home, "digest-2")
    assert rc2 == 0
    head_of(out2.replace("\r\n", "\n"), OMEGA)


def test_r2_a_repeated_marker_line_is_never_printed(tmp_path):
    """R-109, TASK-087b round 2, Requirement 4 (Review A, should-fix; R2's "without the marker line"): where the
    marker line stands twice, the digest splits at the first, no part prints a marker line, and the text after the
    second marker stays in the second part. Mutation K7 (a later marker line printed inside a part)."""
    tail = block("TAIL-START after a second marker", "TAIL-END", 400)
    home = make_home(tmp_path, synthetic_supervisor(ALPHA, OMEGA + "\n" + MARK + "\n" + tail))
    cwd = make_project(tmp_path)
    for part in ("digest", "digest-2", "all"):
        rc, out = run_hook(cwd, home, part)
        assert rc == 0
        assert "digest:part" not in out, "K7: %s prints a marker line" % part
    _rc, out1 = run_hook(cwd, home, "digest")
    assert "OMEGA-START" not in out1 and "TAIL-START" not in out1
    _rc, out2 = run_hook(cwd, home, "digest-2")
    assert "OMEGA-START" in out2 and "TAIL-START" in out2 and "TAIL-END" in out2
    assert out2.index("OMEGA-END") < out2.index("TAIL-START")


def test_r2_the_second_part_without_the_marker_writes_nothing_at_all(tmp_path):
    """R-109, TASK-087b round 2, Requirement 5 (the security audit's advisory; R2's "it prints nothing"): where the
    digest holds no marker line, `--part digest-2` writes no byte, as the hook writes none outside a bridge project.
    Mutation K8 (a part with nothing to print writing a line feed)."""
    home = make_home(tmp_path, synthetic_supervisor(ALPHA + "\n\n" + OMEGA))
    cwd = make_project(tmp_path)
    rc, raw = run_hook_bytes(cwd, home, "digest-2")
    assert rc == 0 and raw == b"", "K8: %r" % raw[:200]


@pytest.mark.parametrize("rel", ["tests/test_session_start.py", "tests/test_loop_text_pace.py", "tests/test_a5_followups.py"])
def test_r2_each_cap_test_holds_the_whole_and_each_part(rel):
    """R-109, TASK-087b round 2, Requirement 2 (Review A, blocking: R7 and the plan's Done when, "the tests that held
    the digest at 9,500 characters hold the whole digest at 10,500 and each part at 8,800"): each of the three tests
    names both numbers and splits the digest at the marker line, as the maintainer's comment above the digest says
    they do. A text check of the test's source: the numbers themselves are run by that test."""
    src = read_text(os.path.join(HERE, os.pardir, rel))
    assert "10500" in src, "%s holds the whole digest at 10,500" % rel
    assert "8800" in src, "%s holds each part at 8,800" % rel
    assert "digest:part" in src, "%s splits the digest at the marker line" % rel
    assert "9500" not in src, "%s no longer holds the old cap" % rel
