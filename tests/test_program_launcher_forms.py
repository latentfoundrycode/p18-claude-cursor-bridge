"""TASK-059, the supervisor's acceptance tests: the launcher's command forms (R-078).

enforces: docs/REQUIREMENTS.md R-078; docs/DESIGN.md, "Change: the program release", "What changes - the items by
home", "The launcher, `bridge-run.py`": C6 (the interpreter's two flags), F5 (a suite in a subfolder), J4 (the two
exit-125 messages), J9 (`merge_ids` sorted) and J12 (the plan glob escapes its root); docs/BUILD_PLAN.md, TASK-059's
Done when; docs/HARDENING.md, TASK-059's reality check (the environment names that move a runner's folder).

What each group pins, in the forms the brief repeats:
- C6: the test and the driver kind take the interpreter's own leading flags, exactly `-B` and the two words `-X utf8`,
  in either order and each once, and every reading of the command starts after them: the named suite, the runner's
  word, the `-p no:` rule, the target rule, the environment rule, the logged head (the same as without the flags) and
  the driver's checks of its program. Any other interpreter option before the module or the program is refused. A
  suite launched with both flags runs with them, and the launcher sets no `PYTHONUTF8`.
- F5: npm's `--prefix` and `-C` (npm's short form of `--prefix`, the reality check), pnpm's `--dir` and `-C` and
  yarn's `--cwd` are read wherever they stand before a bare `--`, in the two-word and the `=` form. The folder is
  accepted only where it exists, lies under the launch roots by its resolved path and is reached through no link; it is
  refused where it is given twice (an option and its other name count as one option), where its value is missing or
  starts with `-`, and, since round 3's security audit (npm's parser reads `~/` as the user's home folder, and ran a home
  folder's script with `<ws>/~/x` planted), where its value starts with `~`, by its text; since round 4's security audit
  (npm trims a value's leading Unicode or ASCII space before that rule and expands `${NAME}` in it after the folder rule
  read the literal text), a folder value is held to a list of characters: ASCII letters, digits, `.`, `_`, `-`, `/`,
  the backslash, a leading drive `X:`, never `-` or `~` first; every other value is refused by its text, before any filesystem call;
  and since round 5's security audit (Windows' path functions drop a last component's trailing dots, so the rule checked
  the launch folder for `...` while npm read the word through a junction planted under that name), the runner is given
  the absolute folder the rule checked in place of the value given, so the folder that runs is the folder checked. Since round 1's reviews (both reviewers reproduced npm, whose parser strips every leading dash,
  expands a cluster of one-letter options and takes an unambiguous abbreviation, running outside the launch roots by
  `-prefix`, `---prefix`, `-sC`, `--C` and the like), a named npm, pnpm or yarn suite takes, before a bare `--`, no
  option word but these folder options in exactly those forms and three harmless flags (`--silent`, `-s`,
  `--if-present`), each flag as that exact word and only after the subcommand: every other word that starts with `-`
  is refused, an abbreviation, a cluster, an attached `-C<folder>`, `--script-shell`, `-w` and, since round 2's
  reviews (both reproduced npm running outside by `--silent=--prefix <folder>`: npm splits a word at `=` and reads the
  value of a flag that takes none as a word of its own), a flag with `=` among them, as `uv_run_pytest` holds uv's
  options to a list; a flag before the subcommand leaves the command unnamed. A suite so launched is stripped, logged as
  `npm test` (the folder never in the head) and limited as any named suite.
- The environment, since round 2's reviews: an environment name is a command-line option in another form
  (`npm_config_<x>` is npm's `--<x>`: round 2's security audit ran an outside `npm-cli.js` through
  `npm_config_prefix`, which npm.cmd reads before npm itself starts), so the option list above holds there too. For a
  named npm, pnpm or yarn suite, a name in the run's environment (the launcher's own or a key file's line) that begins,
  in any letter case, with `npm_config_` (all three runners read it), `pnpm_config_` (pnpm) or `yarn_` (yarn) is
  refused whatever its value, empty included, the name printed and its value never; but the two cache names the
  bridge itself passes to its runs (`NPM_CONFIG_CACHE`, `YARN_CACHE_FOLDER`, bridge_env's APP_CACHES). The
  interpreter's own names (`NODE_OPTIONS`, as `PYTHONPATH` for python) and `INIT_CWD` stay outside, recorded in the
  inventory's threat-model row; no other runner's run is held to these prefixes.
- On Windows a `.cmd` or `.bat` runner is started through cmd.exe, which reads `& | < > ^ % ! " ( )` and line breaks
  in its arguments as its own (round 1's security audit ran a command through it): such an argument is refused before
  anything starts, for every kind but the builder's and the reviewer's (a watch's `gh` among them, round 2's reviews).
- The logged head, since round 2's reviews: the two words read from where the command proper begins keep only the
  words main kept (`pr`, `checks`, `test`, `run`, `pytest`, `unittest`, `vitest`, `jest`, `playwright`, `--test`, `-m`
  and words beginning `test`), so a folder option, a flag or a script's argument never joins it; and `named_suite`
  knows a python head by its name (`python`, `python3`, `py`), a path-qualified one included, so the list refuses a
  python outside the project's .venv with the known message as before round 1.
- J4: a refused option of a named suite (an escape option, an option outside the npm, pnpm and yarn list, every refusal
  of the folder rule, a cmd.exe character), and an interpreter option before `-m pytest` or `-m unittest` that the
  interpreter's options lead to, gets the message beginning KNOWN below, naming the word and saying it is a defect to
  report, never a run to start by hand, with no `# wake`; every other refused command (an unknown runner, or a known one
  that is no named suite, `npm run dev --prefix <folder>` among them) keeps today's message, beginning UNKNOWN, with its
  advice to run directly in the background marked `# wake`.
- J9: a builder run's `merge_ids` is written sorted, whatever order the brief's `Merge unit:` line gives.
- J12: both plan globs (bridge-run.py's header check and `bridge_env.plan_increment_ids`) escape their root, so a
  Workspace whose path holds `[` reads its plan.

At the first checkpoint (6e3d569) every case was red but the three that pin what stays as it is: every other interpreter
option refused, the unknown runner's message, and the names the reality check found not to move a folder; the cases
added after round 1's reviews are red on round 1's code, those added after round 2's on round 2's (e50cb1d), the one
added after round 3's on round 3's (02e9ad7), the two added after round 4's on round 4's (25414fa), and the two added after round 5's on round 5's
(f62855a). npm, pnpm and yarn are stand-ins on PATH that print STAND-IN and whether
the made-up secret-like name reached them, so no runner needs to be installed; the one test that reads the folder a real
npm runs in is skipped where npm is not installed. The builder adds its cases to tests/test_bridge_run.py,
tests/test_bridge_run_driver.py and tests/test_release_s_launcher.py and edits nothing in this file.
"""
import json
import os
import shutil
import subprocess
import sys

import pytest

import test_task032_supervisor_launcher as t32
import test_header_plan as hp
from test_header_plan_r3 import _with_orphan

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "bridge-run.py")
KNOWN = "bridge-run: refused - the launcher knows this runner and refuses "
UNKNOWN = "bridge-run: refused - the launcher runs only cursor-agent"
PROBE = "FIX059_PROBE_TOKEN"                     # made up, secret-like: the strip withholds it
HIDDEN = "VALUE-NEVER-PRINTED"                    # part of every value a refusal must not print

ACCEPTED_FLAGS = [["-B"], ["-X", "utf8"], ["-B", "-X", "utf8"], ["-X", "utf8", "-B"]]
REFUSED_FLAGS = [["-B", "-B"], ["-X", "utf8", "-X", "utf8"], ["-B", "-X", "utf8", "-B"], ["-Xutf8"], ["-X", "dev"], ["-X", "utf8=1"],
                 ["-X"], ["-E"], ["-I"], ["-O"], ["-u"], ["-S"], ["-B", "-E"], ["-X", "utf8", "-I"]]
OPTIONS = [("npm", "--prefix"), ("npm", "-C"), ("pnpm", "--dir"), ("pnpm", "-C"), ("yarn", "--cwd")]
OTHER_NAME = {("npm", "--prefix"): "-C", ("npm", "-C"): "--prefix", ("pnpm", "--dir"): "-C", ("pnpm", "-C"): "--dir"}
ALLOWED_FLAGS = ["--silent", "-s", "--if-present"]
# Option words npm's parser (nopt) reads as the folder option or another one, refused whatever their value
# (round 1's reviews ran npm in a folder outside by the first five of npm's).
NOT_LISTED = {"npm": ["-prefix", "---prefix", "-prefi=frontend", "--C", "-sC", "-dC", "-sC=frontend", "--pre", "--prefi=frontend", "--p",
                      "-Cfrontend", "--script-shell", "--node-options=--require=x.js", "-w", "--workspace=frontend", "--workspaces", "--loglevel"],
              "pnpm": ["-dir", "---dir", "--C", "-sC", "--di", "-Cfrontend", "--filter", "-r", "-w", "--script-shell"],
              "yarn": ["-cwd", "---cwd", "--cw", "--cwdx", "-C", "--verbose"]}
# Round 2's reviews: a flag's `=` form, whose value npm reads as a word of its own (`--prefix`, a subcommand).
FLAG_EQUALS = ["--silent=--prefix", "-s=--prefix", "--if-present=--prefix", "--silent=x", "-s=", "--if-present=exec", "--if-present=true"]
for _runner in NOT_LISTED:
    NOT_LISTED[_runner] += FLAG_EQUALS


@pytest.fixture
def br(program, monkeypatch):
    monkeypatch.delenv("BRIDGE_RUN_ALLOW_ANY", raising=False)
    return program("bridge-run")


def _link(link, target):
    try:
        os.symlink(str(target), str(link), target_is_directory=True)
    except (OSError, NotImplementedError):
        try:
            import _winapi
            _winapi.CreateJunction(str(target), str(link))
        except (ImportError, OSError):
            pytest.skip("this account can make neither a symbolic link nor a junction")


def _unlink(link):
    if os.path.lexists(str(link)):
        os.rmdir(str(link)) if os.name == "nt" else os.unlink(str(link))


def write_runners(bin_dir):
    """npm, pnpm and yarn stand-ins: each prints STAND-IN, its name and whether the made-up secret-like name reached it."""
    bin_dir.mkdir(parents=True, exist_ok=True)
    for name in ("npm", "pnpm", "yarn"):
        if sys.platform == "win32":
            text = ("@echo off\r\nif defined %s (echo STAND-IN %s TOKEN-SEEN) else (echo STAND-IN %s TOKEN-ABSENT)\r\nexit /b 0\r\n"
                    % (PROBE, name, name))
            (bin_dir / (name + ".cmd")).write_text(text, encoding="ascii")
        else:
            text = ('#!/bin/sh\nif [ -n "${%s+x}" ]; then echo "STAND-IN %s TOKEN-SEEN"; else echo "STAND-IN %s TOKEN-ABSENT"; fi\n'
                    % (PROBE, name, name))
            path = bin_dir / name
            path.write_text(text, encoding="ascii")
            path.chmod(0o755)


@pytest.fixture
def ws(tmp_path):
    """A launch folder with a frontend subfolder, a folder beside it (outside) and the stand-ins."""
    ws = tmp_path / "ws"
    (ws / "frontend").mkdir(parents=True)
    (ws / "tests").mkdir()
    (ws / "run").mkdir()                          # the launcher logs a run only where the launch folder holds run/
    (tmp_path / ("elsewhere-" + HIDDEN)).mkdir()
    write_runners(tmp_path / "bin")
    return ws


def outside_of(ws):
    return ws.parent / ("elsewhere-" + HIDDEN)


def launch(ws, words, extra=None, key_file=None, strip=True, stand_ins=True, limit="60", kind="test"):
    tmp = ws.parent
    env = {k: v for k, v in os.environ.items() if not k.lower().startswith(("npm_config_", "pnpm_config_", "yarn_"))
           and k.upper() not in ("BRIDGE_RUN_ALLOW_ANY", "BRIDGE_RUN_SLOT_SCALE", "PYTHONUTF8", PROBE, "INIT_CWD")}
    env["LOCALAPPDATA"] = str(tmp / "localappdata")
    if stand_ins:
        env["PATH"] = str(tmp / "bin") + os.pathsep + env.get("PATH", "")
    env.update(extra or {})
    argv = [sys.executable, PROG, "--limit", limit] + (["--strip"] if strip else []) + ["--kind", kind]
    argv += (["--key-file", str(key_file)] if key_file is not None else []) + ["--"] + list(words)
    return subprocess.run(argv, capture_output=True, text=True, cwd=str(ws), env=env, timeout=300)


def assert_started(p, words):
    assert "Traceback" not in p.stderr, p.stderr
    assert "bridge-run: refused" not in p.stderr and "bridge-run: started" in p.stderr, (words, p.stderr)
    assert p.returncode == 0 and "STAND-IN" in p.stdout, (words, p.returncode, p.stdout, p.stderr)


def refusal_line(p, words):
    assert "Traceback" not in p.stderr, p.stderr
    assert p.returncode == 125, (words, p.returncode, p.stderr)
    assert "bridge-run: started" not in p.stderr and "STAND-IN" not in p.stdout, (words, p.stderr)
    lines = [line for line in p.stderr.splitlines() if line.startswith("bridge-run: refused")]
    assert lines, (words, p.stderr)
    return lines[0]


def assert_known_refusal(p, words, option):
    line = refusal_line(p, words)
    assert line.startswith(KNOWN), (words, line)
    assert option in line and "defect" in line, (words, line)
    assert "# wake" not in p.stderr, (words, p.stderr)
    return line


# ---------------------------------------------------------------- C6: the interpreter's two flags


def test_r078_the_two_flags_name_the_suite_after_them(br, tmp_path):
    """Each accepted form is a named suite of the test kind, its runner's word read after the flags, and logged with the
    head it has without them."""
    for head in ("python", "python3", "py"):
        for mod in ("pytest", "unittest"):
            plain = [head, "-m", mod]
            assert br.named_suite(plain) and br.accepted(plain, str(tmp_path)), plain        # the control: today's form
            for flags in ACCEPTED_FLAGS:
                argv = [head] + flags + ["-m", mod]
                assert br.named_suite(argv) and br.kind_of(argv) == "test" and br.accepted(argv, str(tmp_path)), argv
                assert br.runner_word(argv + ["-q"]) == (mod, len(flags) + 3), argv
                assert br.head_text(argv + ["-q"]) == br.head_text(plain + ["-q"]), argv


def test_r078_every_other_interpreter_option_is_refused(br, tmp_path):
    for flags in REFUSED_FLAGS:
        for mod in ("pytest", "unittest"):
            argv = ["python"] + flags + ["-m", mod, "tests"]
            assert not br.accepted(argv, str(tmp_path)), argv


def test_r078_the_target_the_environment_and_the_plugin_rules_read_after_the_flags(br, tmp_path):
    """Release S's target rule and environment rule, and the `-p no:` exception, see the runner behind the flags."""
    base = str(tmp_path / "ws")
    os.makedirs(os.path.join(base, "tests"))
    out = str(tmp_path / "elsewhere" / "test_a.py")
    for flags in ACCEPTED_FLAGS:
        lead = ["python"] + flags + ["-m", "pytest"]
        assert br.outside_target(lead + [out], base) is not None, flags
        assert br.outside_target(lead + ["tests"], base) is None, flags
        assert br.outside_target(["python"] + flags + ["-m", "unittest", "discover", "-s", str(tmp_path / "elsewhere")], base) is not None, flags
        assert br.outside_by_environment(lead, {"PYTEST_PLUGINS": "x"}, base) == "PYTEST_PLUGINS", flags
        assert br.outside_by_environment(lead, {"PYTEST_ADDOPTS": out}, base) == "PYTEST_ADDOPTS", flags
        assert br.test_suite(lead + ["-p", "no:cacheprovider", "-q"], base), flags
        for escape in (["-p", "evil"], ["-c", "x.ini"], ["--basetemp=../.."]):
            assert not br.test_suite(lead + escape, base), (flags, escape)


def test_r078_the_driver_kind_takes_the_two_flags_before_its_program(br, tmp_path):
    ws = tmp_path / "ws"
    (ws / "run" / "supervisor").mkdir(parents=True)
    prog = ws / "run" / "supervisor" / "probe.py"
    prog.write_text("print('probe')\n", encoding="utf-8")
    (tmp_path / "elsewhere.py").write_text("print('elsewhere')\n", encoding="utf-8")
    assert br.resolve_driver_program(["python", "run/supervisor/probe.py"], str(ws)) == os.path.abspath(str(prog))   # the control
    for flags in ACCEPTED_FLAGS:
        assert br.resolve_driver_program(["python"] + flags + ["run/supervisor/probe.py"], str(ws)) == os.path.abspath(str(prog)), flags
        for bad in ("../elsewhere.py", str(tmp_path / "elsewhere.py"), "run/supervisor/../../elsewhere.py", "run/supervisor/missing.py"):
            assert br.resolve_driver_program(["python"] + flags + [bad], str(ws)) is None, (flags, bad)
    for flags in REFUSED_FLAGS:
        assert br.resolve_driver_program(["python"] + flags + ["run/supervisor/probe.py"], str(ws)) is None, flags


def _clean_env(tmp_path):
    env = {k: v for k, v in os.environ.items() if k.upper() not in ("BRIDGE_RUN_ALLOW_ANY", "BRIDGE_RUN_SLOT_SCALE", "PYTHONUTF8", "PYTHONDONTWRITEBYTECODE")}
    env["LOCALAPPDATA"] = str(tmp_path / "localappdata")
    return env


def test_r078_a_suite_launched_with_both_flags_runs_with_them_and_no_pythonutf8(tmp_path):
    ws = tmp_path / "ws"
    (ws / "tests").mkdir(parents=True)
    (ws / "run").mkdir()                          # the launcher logs a run only where the launch folder holds run/
    (ws / "tests" / "test_flags.py").write_text(
        "import os\nimport sys\n\n\ndef test_flags():\n    assert sys.flags.dont_write_bytecode == 1\n    assert sys.flags.utf8_mode == 1\n"
        "    assert 'PYTHONUTF8' not in os.environ\n", encoding="utf-8")
    p = subprocess.run([sys.executable, PROG, "--limit", "120", "--kind", "test", "--", "python", "-B", "-X", "utf8", "-m", "pytest", "-q",
                        "-p", "no:cacheprovider", "tests/test_flags.py"], capture_output=True, text=True, cwd=str(ws), env=_clean_env(tmp_path), timeout=300)
    assert p.returncode == 0 and "bridge-run: exit 0" in p.stderr and "1 passed" in p.stdout, (p.stdout, p.stderr)
    rows = t32.log_lines(ws / "run" / "launcher" / "runs.jsonl")
    row = json.loads(rows[-1].decode("utf-8"))
    assert row["kind"] == "test" and row["head"] == "python -m pytest" and row["exit"] == 0, row


def test_r078_a_driver_launched_with_both_flags_runs_its_program_with_them(tmp_path):
    ws = tmp_path / "ws"
    (ws / "run" / "supervisor").mkdir(parents=True)
    (ws / "run" / "supervisor" / "probe.py").write_text(
        "import os\nimport sys\nprint('flags', sys.flags.dont_write_bytecode, sys.flags.utf8_mode, 'PYTHONUTF8' in os.environ)\n", encoding="utf-8")
    p = subprocess.run([sys.executable, PROG, "--limit", "60", "--kind", "driver", "--", "python", "-X", "utf8", "-B", "run/supervisor/probe.py"],
                       capture_output=True, text=True, cwd=str(ws), env=_clean_env(tmp_path), timeout=300)
    assert p.returncode == 0 and "flags 1 1 False" in p.stdout, (p.stdout, p.stderr)


# ---------------------------------------------------------------- F5: the folder options


def forms(runner, option, value):
    return [[runner, option, value, "test"], [runner, option + "=" + value, "test"], [runner, "test", option, value],
            [runner, "test", option + "=" + value], [runner, option, value, "run", "test:unit"]]


@pytest.mark.parametrize("runner,option", OPTIONS)
def test_r078_a_folder_inside_the_launch_folder_is_accepted_in_every_form(ws, runner, option):
    for words in forms(runner, option, "frontend") + [[runner, option, ".", "test"], [runner, "test", option, str(ws / "frontend")]]:
        assert_started(launch(ws, words), words)
    for flag in ALLOWED_FLAGS:                                          # the three harmless flags, before and after the folder option
        for words in ([runner, option, "frontend", "test", flag], [runner, "test", flag, option + "=frontend"]):
            assert_started(launch(ws, words), words)
    words = [runner, "test", "--", option, str(outside_of(ws)), "-sC", "--script-shell"]   # after a bare --: the script's own arguments
    assert_started(launch(ws, words), words)


@pytest.mark.parametrize("runner,option", OPTIONS)
def test_r078_a_folder_outside_missing_or_through_a_link_is_refused_naming_the_option(ws, runner, option):
    out = str(outside_of(ws))
    _link(ws / "out-link", outside_of(ws))
    _link(ws / "in-link", ws / "frontend")
    try:
        for value in (out, os.path.join("..", "elsewhere-" + HIDDEN), "out-link", "in-link", os.path.join("in-link", os.curdir), "no-such-folder"):
            for words in forms(runner, option, value):
                assert_known_refusal(launch(ws, words), words, option)
    finally:
        _unlink(ws / "out-link")
        _unlink(ws / "in-link")


@pytest.mark.parametrize("runner,option", OPTIONS)
def test_r078_a_folder_option_given_twice_or_without_its_value_is_refused(ws, runner, option):
    (ws / "-x").mkdir()                                                 # a folder named like an option: still no value
    cases = [[runner, option, "frontend", "test", option, "frontend"], [runner, option + "=frontend", "test", option + "=frontend"],
             [runner, "test", option], [runner, "test", option + "="], [runner, "test", "--silent", option],
             [runner, "test", option, "-x"], [runner, "test", option + "=-x"], [runner, option, "-x", "test"]]
    if (runner, option) in OTHER_NAME:
        cases.append([runner, option, "frontend", OTHER_NAME[(runner, option)], "frontend", "test"])
    for words in cases:
        assert_known_refusal(launch(ws, words), words, option)


@pytest.mark.parametrize("runner,option", OPTIONS)
def test_r078_a_folder_value_beginning_with_a_tilde_is_refused(ws, runner, option):
    """Round 3's security audit: npm's parser reads a folder value beginning with `~/` (or `~\\` on Windows) as the
    user's home folder, while the folder rule read it as a folder named `~` under the launch folder, so `npm --prefix ~/x
    test` ran a home folder's script with `<ws>/~/x` planted. A value beginning with `~` is refused by its text, before
    any filesystem call; the control: the same option with an inside folder, accepted."""
    (ws / "~" / "x").mkdir(parents=True)
    (ws / "~x").mkdir()                                                   # each value names a folder that exists inside
    assert_started(launch(ws, [runner, option, "frontend", "test"]), [runner, option, "frontend", "test"])
    for value in ("~/x", "~" + os.sep + "x", "~", "~x"):
        for words in forms(runner, option, value):
            assert_known_refusal(launch(ws, words), words, option)


# Round 4's security audit: npm trims a folder value (JS trim: U+00A0, U+2000-U+200A, U+3000, U+FEFF and the ASCII
# spaces) before its home rule, and expands `${NAME}` in it after the folder rule checked the literal text, so a value
# the rule read as a folder inside ran npm elsewhere. A folder value is now held to a list of characters (ASCII letters,
# digits, `.`, `_`, `-`, `/`, `\`, a leading drive `X:`), never `-` or `~` first, as the option words are held to theirs.
NOT_A_FOLDER = [chr(0xA0) + "~/x", chr(0x3000) + "~/x", chr(0xFEFF) + "~/x", chr(0x2002) + "~/x", " ~/x", "frontend ", " frontend",
                "\tfrontend", "a${OS}/x", "${HOME}", "a${Z?}b", "a{b}", "front" + chr(0xEB) + "nd", "a$b", "a b", "a;b", "a'b", "a,b"]
FOLDER_SHAPED = ["frontend", "./frontend", "sub-dir_1.x", os.path.join("frontend", "pkg"), "frontend/pkg"]


def test_r078_a_folder_value_outside_the_character_list_is_refused(br, tmp_path):
    """Each value names a folder that exists inside the launch folder where the system allows the name, so the refusal
    is the character list's, not the folder rule's; the controls: plain names, accepted."""
    base = tmp_path / "ws"
    (base / "frontend" / "pkg").mkdir(parents=True)
    (base / "sub-dir_1.x").mkdir()
    for value in NOT_A_FOLDER:
        try:
            (base / value.strip(chr(0xA0) + chr(0x3000) + chr(0xFEFF) + chr(0x2002) + " \t")).mkdir(parents=True, exist_ok=True)
            (base / value).mkdir(parents=True, exist_ok=True)
        except (OSError, ValueError):
            pass                                                        # a name the system refuses is refused all the more
    for runner, option in OPTIONS:
        for value in FOLDER_SHAPED:
            for argv in ([runner, option, value, "test"], [runner, "test", option + "=" + value]):
                assert br.test_suite(argv, str(base)), (argv, br.known_runner_refuse_word(argv, str(base)))
        for value in NOT_A_FOLDER:
            for argv in ([runner, option, value, "test"], [runner, "test", option + "=" + value], [runner, "test", option, value]):
                assert not br.test_suite(argv, str(base)), argv
                assert br.known_runner_refuse_word(argv, str(base)) == option, (argv, br.known_runner_refuse_word(argv, str(base)))


@pytest.mark.parametrize("value", [chr(0xA0) + "~/x", "a${OS}/x"])
def test_r078_a_trimmed_or_expanded_folder_value_is_refused_before_anything_starts(ws, value):
    """Round 4's security audit's two reproductions, through the launcher: the planted folder exists, the run is refused
    with the known message naming the option, before `bridge-run: started`."""
    try:
        (ws / value).mkdir(parents=True)
    except OSError:
        pass
    words = ["npm", "--prefix", value, "test"]
    assert_known_refusal(launch(ws, words), words, "--prefix")
    assert_started(launch(ws, ["npm", "--prefix", "frontend", "test"]), ["npm", "--prefix", "frontend", "test"])


def write_arg_runners(bin_dir):
    """npm, pnpm and yarn stand-ins that print ARGS and their command line as given (cmd.exe's %* keeps a word with
    `=` whole, as npm.cmd passes it on), then STAND-IN."""
    bin_dir.mkdir(parents=True, exist_ok=True)
    for name in ("npm", "pnpm", "yarn"):
        if sys.platform == "win32":
            (bin_dir / (name + ".cmd")).write_text("@echo off\r\necho ARGS %*\r\necho STAND-IN\r\nexit /b 0\r\n", encoding="ascii")
        else:
            path = bin_dir / name
            path.write_text('#!/bin/sh\necho "ARGS $*"\necho STAND-IN\n', encoding="ascii")
            path.chmod(0o755)


def given_words(p):
    """The words the stand-in was given (the test's folders hold no space)."""
    lines = [line for line in p.stdout.splitlines() if line.startswith("ARGS")]
    return lines[0].split()[1:] if lines else []


def same_folder(a, b):
    return os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(b))


@pytest.mark.parametrize("runner,option", OPTIONS)
def test_r078_the_runner_is_given_the_folder_the_rule_checked(ws, runner, option):
    """Round 5's security audit: Windows' path functions drop a last component's trailing dots, so the rule checked the
    launch folder for `...` (or `a` for `a..`) while npm read the word as written, through a junction planted under that
    name. The launcher now hands the runner the absolute folder it checked in place of the value given, in both forms,
    before or after the subcommand, so the folder that runs is the folder checked whatever either side normalises; the
    words after a bare `--` stay as given."""
    argbin = ws.parent / "argbin"
    write_arg_runners(argbin)
    path = {"PATH": str(argbin) + os.pathsep + os.environ.get("PATH", "")}
    frontend = ws / "frontend"
    for words in ([runner, option, "frontend", "test"], [runner, "test", option, "frontend"], [runner, option, "./frontend", "test"]):
        p = launch(ws, words, extra=path, stand_ins=False)
        assert_started(p, words)
        got = given_words(p)
        i = got.index(option)
        assert os.path.isabs(got[i + 1]) and same_folder(got[i + 1], frontend), (words, got)
    for words in ([runner, option + "=frontend", "test"], [runner, "test", option + "=frontend"]):
        p = launch(ws, words, extra=path, stand_ins=False)
        assert_started(p, words)
        got = [w for w in given_words(p) if w.startswith(option + "=")]
        assert len(got) == 1, (words, given_words(p))
        value = got[0].split("=", 1)[1]
        assert os.path.isabs(value) and same_folder(value, frontend), (words, given_words(p))
    words = [runner, "test", "--", option, "frontend"]                   # after a bare --: the script's own words, untouched
    p = launch(ws, words, extra=path, stand_ins=False)
    assert_started(p, words)
    assert given_words(p)[-2:] == [option, "frontend"], given_words(p)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows drops a last component's trailing dots")
def test_r078_a_trailing_dot_name_never_reaches_the_runner_as_written(ws):
    """Round 5's security audit's reproduction: `...` and `a..` planted as junctions to a folder outside (made through the
    `\\\\?\\` prefix, which keeps the dots); the run is refused, or the runner is given a folder inside, never the word."""
    import _winapi
    argbin = ws.parent / "argbin"
    write_arg_runners(argbin)
    path = {"PATH": str(argbin) + os.pathsep + os.environ.get("PATH", "")}
    (ws / "a").mkdir()
    out = outside_of(ws)
    planted = []
    try:
        for name in ("...", "a..", "...."):
            target = "\\\\?\\" + str(ws) + "\\" + name
            try:
                _winapi.CreateJunction(str(out), target)
            except OSError:
                pytest.skip("this account cannot make a junction")
            planted.append(target)
        for value in ("...", "a..", "a...", "....", ".../"):
            words = ["npm", "--prefix", value, "test"]
            p = launch(ws, words, extra=path, stand_ins=False)
            if p.returncode == 125:
                assert_known_refusal(p, words, "--prefix")
                continue
            assert_started(p, words)
            got = given_words(p)
            given = got[got.index("--prefix") + 1]
            assert given != value and os.path.isabs(given), (value, got)
            assert not same_folder(given, out) and os.path.normcase(os.path.realpath(given)).startswith(os.path.normcase(os.path.realpath(str(ws)))), (value, got)
    finally:
        for target in planted:
            try:
                os.rmdir(target)
            except OSError:
                pass


@pytest.mark.parametrize("runner", ["npm", "pnpm", "yarn"])
def test_r078_an_option_word_outside_the_list_is_refused_whatever_its_value(ws, runner):
    """Each word refused with the folder an inside one, so the refusal is the word's, not the folder rule's; the control
    is the listed form, accepted."""
    listed = {"npm": "--prefix", "pnpm": "--dir", "yarn": "--cwd"}[runner]
    assert_started(launch(ws, [runner, "test", listed, "frontend"]), [runner, "test", listed, "frontend"])
    for word in NOT_LISTED[runner]:
        for words in ([runner, "test", word, "frontend"], [runner, word, "frontend", "test"] if "=" not in word else [runner, "test", word]):
            p = launch(ws, words)
            line = refusal_line(p, words)
            if words[1] == word:                                        # a leading word outside the list leaves the command unnamed
                continue
            assert line.startswith(KNOWN) and word.split("=", 1)[0] in line and "# wake" not in p.stderr, (words, line)


def test_r078_a_suite_in_a_subfolder_is_stripped_logged_and_limited(ws):
    words = ["npm", "--prefix", "frontend", "test"]
    control = launch(ws, words, extra={PROBE: "t"}, strip=False)
    assert_started(control, words)
    assert "TOKEN-SEEN" in control.stdout, control.stdout                 # the probe reaches a run nothing strips
    p = launch(ws, words, extra={PROBE: "t"}, limit="45")
    assert_started(p, words)
    assert "TOKEN-ABSENT" in p.stdout, p.stdout
    row = json.loads(t32.log_lines(ws / "run" / "launcher" / "runs.jsonl")[-1].decode("utf-8"))
    assert row["kind"] == "test" and row["head"] == "npm test" and row["limit"] == 45 and row["exit"] == 0, row


@pytest.mark.skipif(shutil.which("npm") is None, reason="npm is not installed")
def test_r078_npm_runs_in_the_folder_its_option_names(ws):
    for folder, name in ((ws, "WS"), (ws / "frontend", "FRONTEND")):
        (folder / "package.json").write_text(json.dumps({"name": "probe-" + name.lower(), "version": "0.0.0", "private": True,
                                                          "scripts": {"test": "node -e \"console.log('RAN-IN-%s')\"" % name}}), encoding="utf-8")
    for words in (["npm", "--prefix", "frontend", "test"], ["npm", "test", "-C", "frontend"]):
        p = launch(ws, words, strip=False, stand_ins=False, limit="300")
        assert p.returncode == 0 and "RAN-IN-FRONTEND" in p.stdout and "RAN-IN-WS" not in p.stdout, (words, p.stdout, p.stderr)


# ---------------------------------------------------------------- the environment: the option list in another form


FOLDER_OPTION = {"npm": "--prefix", "pnpm": "--dir", "yarn": "--cwd"}
# The names each runner reads as its own options (npm and pnpm by nopt from `npm_config_<x>`, pnpm also `pnpm_config_<x>`,
# yarn 1 from `npm_config_<x>` and `yarn_<x>`), any letter case: round 2's security audit ran an outside npm-cli.js by
# npm_config_prefix and named npm_config_userconfig and npm_config_globalconfig as the way to every other option.
CONFIG_NAMES = {"npm": ["npm_config_workspace", "NPM_CONFIG_WORKSPACES", "npm_config_prefix", "NPM_CONFIG_PREFIX", "npm_config_userconfig",
                        "npm_config_globalconfig", "npm_config_script_shell", "Npm_Config_Node_Options", "npm_config_loglevel"],
                "pnpm": ["npm_config_workspace_dir", "npm_config_prefix", "NPM_CONFIG_USERCONFIG", "pnpm_config_dir", "PNPM_CONFIG_SCRIPT_SHELL"],
                "yarn": ["npm_config_prefix", "YARN_CWD", "yarn_rc_filename", "Yarn_Ignore_Scripts"]}


def test_r078_a_config_name_of_the_runner_is_refused_whatever_its_value(br, tmp_path):
    """Each name refused with every value, an inside folder and the empty value among them, so the refusal is the name's;
    the controls: no name, and the names that stay outside or are the bridge's own, pass."""
    base = tmp_path / "ws"
    (base / "frontend").mkdir(parents=True)
    elsewhere = str(tmp_path / "elsewhere")
    passing = {"NPM_CONFIG_CACHE": elsewhere, "YARN_CACHE_FOLDER": elsewhere, "INIT_CWD": elsewhere, "NODE_OPTIONS": "--max-old-space-size=64",
               "SOME_NAME": "x"}
    for runner, names in CONFIG_NAMES.items():
        for argv in ([runner, "test"], [runner, FOLDER_OPTION[runner], "frontend", "test"], [runner, "run", "test:unit"]):
            assert br.outside_by_environment(argv, {}, str(base)) is None, argv
            assert br.outside_by_environment(argv, dict(passing), str(base)) is None, argv
            for name in names:
                for value in ("frontend", str(base / "frontend"), elsewhere, "true", ""):
                    got = br.outside_by_environment(argv, dict(passing, **{name: value}), str(base))
                    assert (got or "").upper() == name.upper(), (argv, name, value, got)


def test_r078_no_other_runner_is_held_to_the_config_names(br, tmp_path):
    for argv in (["python", "-m", "pytest"], ["pytest"], ["python", "-B", "-m", "unittest"]):
        for name in ("npm_config_prefix", "pnpm_config_dir", "YARN_CWD"):
            assert br.outside_by_environment(argv, {name: str(tmp_path / "elsewhere")}, str(tmp_path)) is None, (argv, name)


@pytest.mark.parametrize("route", ["environment", "key file"])
@pytest.mark.parametrize("name", ["npm_config_workspace", "npm_config_prefix"])
def test_r078_a_config_name_is_refused_by_name_and_its_value_is_never_printed(ws, route, name):
    out = str(outside_of(ws))
    words = ["npm", "test"]
    assert_started(launch(ws, words, extra={"NPM_CONFIG_CACHE": out}), words)    # the control: the bridge's own cache name passes
    extra, key_file = None, None
    if route == "environment":
        extra = {name: out}
    else:
        key_file = ws.parent / "keys.env"
        key_file.write_text("%s=%s\n" % (name, out), encoding="utf-8")
    p = launch(ws, words, extra=extra, key_file=key_file)
    line = refusal_line(p, words)
    assert name.upper() in line.upper(), line
    assert HIDDEN not in p.stderr and HIDDEN not in p.stdout, "the value is never printed"


# ---------------------------------------------------------------- J4: the two exit-125 messages


def test_r078_a_refused_option_of_a_known_runner_is_a_defect_to_report(ws):
    out = str(outside_of(ws))
    for words, option in ((["pytest", "-p", "evil"], "-p"), (["python", "-m", "pytest", "-c", "x.ini"], "-c"), (["python", "-X", "dev", "-m", "pytest"], "-X"),
                          (["python", "-E", "-m", "pytest", "tests"], "-E"), (["python", "-B", "-B", "-m", "unittest"], "-B"),
                          (["npm", "--prefix", out, "test"], "--prefix"), (["pnpm", "test", "--dir"], "--dir"),
                          (["yarn", "--cwd", "frontend", "test", "--cwd", "frontend"], "--cwd")):
        assert_known_refusal(launch(ws, words), words, option)


def test_r078_an_unknown_runner_keeps_todays_advice(ws):
    """Round 1's Review A: a known runner that is no named suite keeps the unknown runner's advice, a folder option and a
    script run behind interpreter options among them."""
    out = str(outside_of(ws))
    for words in (["make", "test"], ["python", "-c", "print(1)"], ["npm", "run", "dev"], ["bash", "-c", "true"],
                  ["npm", "run", "dev", "--prefix", out], ["npm", "install", "--prefix", out], ["pnpm", "build", "-Cfrontend"],
                  ["python", "-I", "x.py", "-m", "pytest"],
                  # round 2's Review A: a flag before the subcommand leaves the command unnamed (Requirement 1)
                  ["npm", "--silent", "test"], ["pnpm", "-s", "test"], ["yarn", "--if-present", "test"], ["npm", "--prefix", "frontend", "-s", "test"]):
        line = refusal_line(launch(ws, words), words)
        assert line.startswith(UNKNOWN) and "# wake" in line, (words, line)


def test_r078_the_logged_head_is_the_heads_as_before(br):
    """Round 1's Review A: the logged head reads two words from where the command proper begins, as it read two from the
    first argument before, so a target or an option never joins it."""
    for flagged, plain in ((["python", "-B", "-m", "pytest", "tests", "-q"], ["python", "-m", "pytest", "tests", "-q"]),
                           (["python", "-X", "utf8", "-m", "unittest", "discover"], ["python", "-m", "unittest", "discover"]),
                           (["npm", "--prefix", "frontend", "test", "test-x", "test-y"], ["npm", "test", "test-x", "test-y"]),
                           (["pnpm", "-C", "frontend", "run", "test:unit", "x"], ["pnpm", "run", "test:unit", "x"])):
        assert br.head_text(flagged) == br.head_text(plain), (flagged, br.head_text(flagged), br.head_text(plain))
    assert br.head_text(["python", "-m", "pytest", "tests"]) == "python -m pytest"
    assert br.head_text(["npm", "test", "test-x", "test-y"]) == "npm test test-x"


def test_r078_the_logged_head_never_holds_an_argument_or_a_folder_option(br):
    """Round 2's reviews (Requirements 7 and 20): the two words keep only the words main kept from argv[1:3], so a folder
    option, a flag, a bare `--` or a script's argument never joins the head."""
    for argv, head in ((["npm", "test", "--prefix", "frontend"], "npm test"),
                       (["npm", "test", "-C", "frontend"], "npm test"),
                       (["npm", "test", "--silent"], "npm test"),
                       (["npm", "test", "--", "--grep", "x"], "npm test"),
                       (["pnpm", "test", "--dir=frontend"], "pnpm test"),
                       (["pnpm", "test", HIDDEN], "pnpm test"),
                       (["yarn", "test", "--cwd", "frontend"], "yarn test"),
                       (["npm", "run", "test:unit", "--if-present"], "npm run test:unit"),
                       (["python", "run/supervisor/probe.py", HIDDEN], "python"),
                       (["python", "-B", "-X", "utf8", "run/supervisor/probe.py", HIDDEN], "python"),
                       (["python", "-m", "pytest", "tests"], "python -m pytest"),
                       (["gh", "pr", "checks", "12"], "gh pr checks")):
        assert br.head_text(argv) == head, (argv, br.head_text(argv))


def test_r078_a_path_qualified_python_stays_a_named_suite_the_list_refuses(br, ws):
    """Round 2's reviews (Requirement 9): named_suite and runner_word know a python head by its name, as before round 1,
    so a path-qualified python outside the project's .venv stays a named suite: test_suite refuses it, the target rule
    reads it, and a refused escape option gets the known message."""
    base = str(ws)
    out = str(outside_of(ws) / "test_a.py")
    for prog in (str(ws.parent / "elsewhere" / "python"), str(ws.parent / "elsewhere" / "python3"), str(ws.parent / "elsewhere" / "python.exe")):
        argv = [prog, "-m", "pytest", "tests"]
        assert br.named_suite(argv, base) and br.kind_of(argv, base) == "test", argv
        assert br.runner_word(argv)[0] == "pytest", (argv, br.runner_word(argv))
        assert not br.test_suite(argv, base), argv
        assert br.outside_target([prog, "-m", "pytest", out], base) is not None, prog
        words = [prog, "-m", "pytest", "-p", "evil"]
        assert_known_refusal(launch(ws, words), words, "-p")


def test_r078_the_escape_lists_hold_every_python_head_and_uv_from_its_first_word(br, tmp_path):
    """Round 1's Review A: python's escape list now holds python3 and py too (they had none at 3a37bde, so `py -m pytest
    -p evil` passed there); uv's options are read from its first word, as before round 1."""
    base = str(tmp_path)
    for head in ("python", "python3", "py"):
        assert not br.test_suite([head, "-m", "pytest", "-c", "x.ini"], base), head
        assert not br.test_suite([head, "-m", "pytest", "-p", "evil"], base), head
        assert br.test_suite([head, "-m", "pytest", "-p", "no:cacheprovider"], base), head
    for argv in (["uv", "-p=x", "pytest"], ["uv", "-p", "3.12", "run", "pytest"]):
        assert not br.test_suite(argv, base), argv


@pytest.mark.skipif(sys.platform != "win32", reason="cmd.exe starts a .cmd runner on Windows only")
def test_r078_a_cmd_character_in_an_argument_of_a_cmd_runner_is_refused(ws):
    """Round 1's security audit: npm.cmd is started through cmd.exe, which reads these characters as its own; the run
    is refused before anything starts, the stand-in never runs."""
    for extra in (["&", "echo", "INJECTED"], ["|", "echo", "INJECTED"], ['x"&echo INJECTED&"'], ["a>b"], ["a<b"], ["^x"], ["%PATH%"], ["!x!"],
                  ["(x)"], ["a\nb"]):
        for words in (["npm", "test"] + extra, ["npm", "--prefix", "frontend", "test", "--"] + extra):
            p = launch(ws, words)
            line = refusal_line(p, words)
            assert line.startswith(KNOWN) and "defect" in line, (words, line)
            assert "INJECTED" not in p.stdout, (words, p.stdout)
    assert_started(launch(ws, ["npm", "test", "--", "plain", "words"]), ["npm", "test", "--", "plain", "words"])


@pytest.mark.skipif(sys.platform != "win32", reason="cmd.exe starts a .cmd runner on Windows only")
def test_r078_a_cmd_character_is_refused_for_a_watch_whose_gh_is_a_cmd(ws):
    """Round 2's reviews (Requirement 6): the check holds for every kind but the builder's and the reviewer's, not only
    for a named suite; a gh.cmd stand-in first on PATH, the control a plain argument, started."""
    bin_dir = ws.parent / "bin"
    (bin_dir / "gh.cmd").write_text("@echo off\r\necho STAND-IN gh\r\nexit /b 0\r\n", encoding="ascii")
    control = ["gh", "pr", "checks", "1", "--repo", "plain"]
    assert_started(launch(ws, control, kind="watch"), control)
    for extra in (["a&echo INJECTED"], ["&", "echo", "INJECTED"], ["%PATH%"]):
        words = ["gh", "pr", "checks", "1", "--repo"] + extra
        p = launch(ws, words, kind="watch")
        line = refusal_line(p, words)
        assert line.startswith(KNOWN) and "defect" in line, (words, line)
        assert "INJECTED" not in p.stdout, (words, p.stdout)


# ---------------------------------------------------------------- J9: merge_ids sorted


def test_r078_merge_ids_is_written_sorted_whatever_the_briefs_order(tmp_path, monkeypatch):
    """Four briefs of one merge unit, each listing the unit in another order and launched under another hash seed: the
    row's `merge_ids` is the sorted list every time."""
    ids = ["TASK-010", "TASK-012", "TASK-015", "TASK-020"]
    orders = [["TASK-020", "TASK-010", "TASK-015", "TASK-012"], ["TASK-015", "TASK-020", "TASK-012", "TASK-010"],
              ["TASK-012", "TASK-015", "TASK-010", "TASK-020"], ["TASK-010", "TASK-012", "TASK-020", "TASK-015"]]
    lab = t32.Lab(tmp_path, branch="task-010")
    t32.write_plan(lab, *ids)
    for seed, (brief, order) in enumerate(zip(ids, orders), 1):
        monkeypatch.setenv("PYTHONHASHSEED", str(seed))
        t32.write_brief(lab.root, brief, "\nMerge unit: %s\n" % " ".join(order))
        row = t32.assert_ran(t32.launch(lab, t32.build(brief)))
        assert row.get("merge_ids") == ids, (brief, order, row.get("merge_ids"))


# ---------------------------------------------------------------- J12: the plan globs escape their root


def test_r078_the_plan_reading_escapes_its_root(program, tmp_path):
    be = program("bridge_env")
    root = tmp_path / "p[1]" / "ws"
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "BUILD_PLAN.md").write_text("# Plan\n\n## Stage 1\n\n### TASK-010 %s the one\nKind: increment\n" % hp.DASH, encoding="utf-8")
    assert "TASK-010" in be.plan_increment_ids(str(root))


def test_r078_the_launcher_reads_a_merge_unit_under_a_root_that_holds_a_bracket(tmp_path):
    lab = t32.Lab(tmp_path, branch="task-010", name="la[u]nch")
    t32.write_plan(lab, "TASK-010", "TASK-015")
    t32.write_brief(lab.root, "TASK-010", "\nMerge unit: TASK-010 TASK-015\n")
    row = t32.assert_ran(t32.launch(lab, t32.build("TASK-010")))
    assert row.get("merge_ids") == ["TASK-010", "TASK-015"], row


def test_r078_the_launchers_plan_header_check_escapes_its_root(tmp_path):
    """The header check's own glob: a headed plan with a heading outside any stage is refused by the plan's header check,
    which an unescaped glob would never read (test_header_plan_r3's case, under a root that holds `[`)."""
    lab = t32.Lab(tmp_path, branch="task-010", name="la[v]nch")
    t32.write_plan(lab, "TASK-010")
    stages = [{"name": "Stage 9", "demo": "it runs.", "incs": [
        {"id": "TASK-015", "title": "two", "lines": ["Kind: increment", "Scope: src/two.py"],
         "h": {"kind": "increment", "parent": None, "depends_on": [], "parallel": False, "diagrams": [],
               "scope": ["src/two.py"], "satisfies": [], "historic": False}}]}]
    (lab.root / "docs" / "BUILD_PLAN-2026-11-04.md").write_bytes((hp.plan_header(stages) + _with_orphan(hp.plan_prose(stages))).encode("utf-8"))
    t32.write_brief(lab.root, "TASK-010", "\nMerge unit: TASK-010 TASK-009\n")
    line = t32.assert_refused(t32.launch(lab, t32.build("TASK-010")), "bridge-run: refused - header: ")
    assert "outside any stage" in line, line
