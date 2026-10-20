"""CONFIG-B3b - the generated command reference (tools/dump-cli.py, docs/cli-reference.json, docs/CLI_REFERENCE.md).

enforces: handoff/CONFIG-B3b.md, Acceptance criteria 1-13; Delivery-Conventions.md section 4 (the command reference, rule 32).
Supervisor-authored before the builder's run. Most tests run the generator on a copy of the repository's programs in a
temporary folder (a "sandbox": tools/dump-cli.py and bridge/cursor-bridge/), so nothing here writes the repository's own
files, a path the generator takes from a program's location really moves, and extra programs can be added to the copy.
"""
import ast
import getpass
import importlib.util
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
GEN = ROOT / "tools" / "dump-cli.py"
BRIDGE = ROOT / "bridge" / "cursor-bridge"
WORKFLOW = ROOT / ".github" / "workflows" / "tests.yml"
PRE_COMMIT = ROOT / ".githooks" / "pre-commit"
JSON_REL = "docs/cli-reference.json"
MD_REL = "docs/CLI_REFERENCE.md"
EXTRACTED = ("completion-check.py", "diagram-check.py", "evaluate-reports.py", "inventory-check.py", "plan-check.py",
             "sync-check.py")
ARGPARSE = EXTRACTED + ("workflow-check.py", "trace-check.py")
ACTION_KEYS = {"option_strings", "dest", "nargs", "type", "default", "required", "choices", "help"}
CHECK_CMD = "python tools/dump-cli.py --check"
BRIDGE_PLACEHOLDER = "<bridge folder>/"


# --- helpers -------------------------------------------------------------------------------------------------------

def _tree(path):
    return ast.parse(pathlib.Path(path).read_text(encoding="utf-8"))


def _is_main_block(node):
    """`if __name__ == "__main__":` at module level."""
    if not isinstance(node, ast.If) or not isinstance(node.test, ast.Compare):
        return False
    t = node.test
    sides = [t.left] + list(t.comparators)
    return (len(t.ops) == 1 and isinstance(t.ops[0], ast.Eq)
            and any(isinstance(s, ast.Name) and s.id == "__name__" for s in sides)
            and any(isinstance(s, ast.Constant) and s.value == "__main__" for s in sides))


def _commands(folder):
    """The command programs of a bridge folder: every *.py directly in it with a module-level __main__ block."""
    return sorted(p.name for p in pathlib.Path(folder).glob("*.py") if any(_is_main_block(n) for n in _tree(p).body))


def _top_function(path, name):
    return next((n for n in _tree(path).body if isinstance(n, ast.FunctionDef) and n.name == name), None)


def _sandbox(base):
    """A copy of the generator and the bridge's programs under `base`, as the repository lays them out."""
    base = pathlib.Path(base)
    shutil.copytree(BRIDGE, base / "bridge" / "cursor-bridge", ignore=shutil.ignore_patterns("__pycache__"))
    (base / "tools").mkdir(parents=True)
    shutil.copyfile(GEN, base / "tools" / "dump-cli.py")
    (base / "docs").mkdir()
    return base


def _run(sandbox, *args, cwd=None, env=None):
    return subprocess.run([sys.executable, str(pathlib.Path(sandbox) / "tools" / "dump-cli.py"), *args],
                          cwd=str(cwd or sandbox), env=env, capture_output=True, text=True, encoding="utf-8",
                          timeout=120)


def _generated(sandbox):
    p = _run(sandbox)
    assert p.returncode == 0, p.stdout + p.stderr
    return json.loads((pathlib.Path(sandbox) / JSON_REL).read_text(encoding="utf-8"))


def _load(path, tag):
    spec = importlib.util.spec_from_file_location("cfgb3b_%s_%s" % (tag, pathlib.Path(path).stem.replace("-", "_")),
                                                  str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _jsonable(value):
    return json.loads(json.dumps(value))


def _expected_default(value, bridge_dir):
    """An absolute path under the program's own folder is recorded by the placeholder (handoff Requirement 5)."""
    if isinstance(value, str) and os.path.isabs(value):
        rel = os.path.relpath(value, bridge_dir)
        assert not rel.startswith(os.pardir), "an absolute default outside the bridge folder: %r" % value
        return BRIDGE_PLACEHOLDER + rel.replace(os.sep, "/")
    return _jsonable(value)


def _expected_action(a, bridge_dir):
    return {"option_strings": list(a.option_strings), "dest": a.dest, "nargs": _jsonable(a.nargs),
            "type": getattr(a.type, "__name__", None) if a.type is not None else None,
            "default": _expected_default(a.default, bridge_dir), "required": a.required,
            "choices": _jsonable(list(a.choices)) if a.choices is not None else None, "help": a.help}


def _expected_parser(parser, bridge_dir):
    import argparse
    pos, opt, subs = [], [], []
    for a in parser._actions:
        if isinstance(a, argparse._SubParsersAction):
            for name, sp in a.choices.items():
                part = _expected_parser(sp, bridge_dir)
                subs.append({"name": name, "description": sp.description, "positionals": part["positionals"],
                             "options": part["options"]})
            continue
        (opt if a.option_strings else pos).append(_expected_action(a, bridge_dir))
    return {"description": parser.description, "positionals": pos, "options": opt, "subcommands": subs}


def _entry(data, name):
    found = [c for c in data["commands"] if c["name"] == name]
    assert len(found) == 1, "%s: %d entries" % (name, len(found))
    return found[0]


PROGRAM_NEW = '"""zz-new: a hand-parsed test command.\n\nUsage: python zz-new.py [--flag]\n"""\nimport sys\n\n\ndef main():\n    return 0\n\n\nif __name__ == "__main__":\n    sys.exit(main())\n'
LIBRARY_NEW = '"""zz_lib: a test library."""\n\n\ndef helper():\n    return 1\n'
PROGRAM_ARGP = ('"""zz-argp: an argparse test command whose main() would leave a file."""\nimport argparse\nimport os\n\n\n'
                'def build_parser():\n    p = argparse.ArgumentParser(description="zz-argp test")\n'
                '    p.add_argument("target")\n    p.add_argument("--level", type=int, default=3, choices=[1, 2, 3])\n'
                '    return p\n\n\ndef main():\n'
                '    open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "RAN-MAIN"), "w").close()\n'
                '    build_parser().parse_args()\n\n\nif __name__ == "__main__":\n    main()\n')
PROGRAM_TRAP = ('"""zz-trap: a hand-parsed test command whose import would leave a file."""\nimport os\n\n'
                'open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "RAN-IMPORT"), "w").close()\n\n\n'
                'def main():\n    return 0\n\n\nif __name__ == "__main__":\n    main()\n')
PROGRAM_BAD = ('"""zz-bad: builds its parser inside main()."""\nimport argparse\n\n\ndef main():\n'
               '    ap = argparse.ArgumentParser(description="zz-bad")\n    ap.parse_args()\n\n\n'
               'if __name__ == "__main__":\n    main()\n')
PROGRAM_ABS = ('"""zz-abs: an argparse test command with an absolute default."""\nimport argparse\nimport os\n\n\n'
               'def build_parser():\n    p = argparse.ArgumentParser(description="zz-abs")\n'
               '    p.add_argument("--where", default=os.path.abspath("somewhere"))\n    return p\n\n\n'
               'if __name__ == "__main__":\n    build_parser().parse_args()\n')


# --- criterion 1: every command, no library ------------------------------------------------------------------------

def test_cfgb3b_covers_every_command_program_and_no_library(tmp_path):
    """Criterion 1: one entry per command program (module-level __main__ block), none for a library; ordered by name."""
    sb = _sandbox(tmp_path / "sb")
    data = _generated(sb)
    names = [c["name"] for c in data["commands"]]
    assert names == _commands(BRIDGE)
    assert len(names) >= 29 and "bridge_env.py" not in names
    assert names == sorted(names)
    assert all(c["path"] == "bridge/cursor-bridge/" + c["name"] for c in data["commands"])
    assert {c["source"] for c in data["commands"]} == {"argparse", "docstring"}


# --- criterion 2: argparse entries --------------------------------------------------------------------------------

@pytest.mark.parametrize("name", ARGPARSE)
def test_cfgb3b_argparse_entry_matches_its_parser(tmp_path, name):
    """Criterion 2: the entry is the parser's action objects (option strings, required, defaults with the placeholder,
    choices, help, nargs, type), positionals and options apart, sub-commands in the order added; source argparse."""
    sb = _sandbox(tmp_path / "sb")
    data = _generated(sb)
    bridge_dir = str(sb / "bridge" / "cursor-bridge")
    parser = _load(sb / "bridge" / "cursor-bridge" / name, "a").build_parser()
    entry = _entry(data, name)
    assert entry["source"] == "argparse"
    assert set(entry) == {"name", "path", "source", "description", "positionals", "options", "subcommands"}
    expected = _expected_parser(parser, bridge_dir)
    for key in ("description", "positionals", "options", "subcommands"):
        assert entry[key] == expected[key], "%s: %s differs" % (name, key)
    for action in entry["positionals"] + entry["options"]:
        assert set(action) == ACTION_KEYS


def test_cfgb3b_evaluate_reports_subcommands_in_order(tmp_path):
    """Criterion 2: evaluate-reports.py's four sub-commands, each with its own arguments."""
    data = _generated(_sandbox(tmp_path / "sb"))
    subs = _entry(data, "evaluate-reports.py")["subcommands"]
    assert [s["name"] for s in subs] == ["collect", "record", "seed", "extract"]
    for s in subs:
        assert set(s) == {"name", "description", "positionals", "options"}
        assert any(o["option_strings"] == ["-h", "--help"] for o in s["options"])


# --- criterion 3: docstring entries -------------------------------------------------------------------------------

def test_cfgb3b_docstring_entries_hold_the_whole_docstring(tmp_path):
    """Criterion 3: every command without a top-level build_parser() is its module docstring, whole (clean=False)."""
    sb = _sandbox(tmp_path / "sb")
    data = _generated(sb)
    hand = [n for n in _commands(BRIDGE) if n not in ARGPARSE]
    assert len(hand) >= 22
    for name in hand:
        entry = _entry(data, name)
        assert entry["source"] == "docstring", name
        assert set(entry) == {"name", "path", "source", "usage"}, name
        assert entry["usage"] == ast.get_docstring(_tree(BRIDGE / name), clean=False), name


# --- criterion 3b: discovery from the source, and nothing is run --------------------------------------------------

def test_cfgb3b_new_programs_are_found_and_none_is_run(tmp_path):
    """Criterion 3b: a new hand-parsed command is covered, a new library is not, a new top-level build_parser() makes an
    argparse entry; a program's import-time code and an argparse program's main() never run (they would leave a file)."""
    sb = _sandbox(tmp_path / "sb")
    folder = sb / "bridge" / "cursor-bridge"
    (folder / "zz-new.py").write_text(PROGRAM_NEW, encoding="utf-8")
    (folder / "zz_lib.py").write_text(LIBRARY_NEW, encoding="utf-8")
    (folder / "zz-argp.py").write_text(PROGRAM_ARGP, encoding="utf-8")
    (folder / "zz-trap.py").write_text(PROGRAM_TRAP, encoding="utf-8")
    data = _generated(sb)
    names = [c["name"] for c in data["commands"]]
    assert "zz-new.py" in names and "zz_lib.py" not in names
    assert _entry(data, "zz-new.py")["usage"] == ast.get_docstring(ast.parse(PROGRAM_NEW), clean=False)
    argp = _entry(data, "zz-argp.py")
    assert argp["source"] == "argparse"
    level = [o for o in argp["options"] if o["option_strings"] == ["--level"]][0]
    assert (level["type"], level["default"], level["choices"], level["required"]) == ("int", 3, [1, 2, 3], False)
    assert [p["dest"] for p in argp["positionals"]] == ["target"]
    assert _entry(data, "zz-trap.py")["source"] == "docstring"
    assert not (folder / "RAN-MAIN").exists(), "an argparse program's main() was run"
    assert not (folder / "RAN-IMPORT").exists(), "a hand-parsed program was imported"


def test_cfgb3b_parser_without_build_parser_is_refused(tmp_path):
    """Criterion 3b: a command building an ArgumentParser with no top-level build_parser() exits 1, naming it, and
    nothing is written."""
    sb = _sandbox(tmp_path / "sb")
    (sb / "bridge" / "cursor-bridge" / "zz-bad.py").write_text(PROGRAM_BAD, encoding="utf-8")
    p = _run(sb)
    assert p.returncode == 1, p.stdout + p.stderr
    assert "zz-bad.py" in p.stdout + p.stderr
    assert not (sb / JSON_REL).exists() and not (sb / MD_REL).exists()


# --- criterion 4: no computer path, identical everywhere ----------------------------------------------------------

def test_cfgb3b_output_is_identical_on_two_computers_and_holds_no_path(tmp_path):
    """Criterion 4: two copies in different folders, different homes and current folders, give the same bytes; neither
    file holds either copy's folder, the repository's, a home, the user's folder name, the temporary folder or a
    drive-letter path; the workflow-check defaults read the placeholder."""
    outputs, forbidden = [], [str(ROOT), str(ROOT).replace("\\", "/")]
    for i, sub in enumerate(("one", os.path.join("two", "deeper"))):
        sb = _sandbox(tmp_path / sub)
        home, cwd = tmp_path / ("home%d" % i), tmp_path / ("cwd%d" % i)
        home.mkdir()
        cwd.mkdir()
        env = dict(os.environ, HOME=str(home), USERPROFILE=str(home))
        p = _run(sb, cwd=cwd, env=env)
        assert p.returncode == 0, p.stdout + p.stderr
        outputs.append(((sb / JSON_REL).read_bytes(), (sb / MD_REL).read_bytes()))
        forbidden += [str(sb), str(sb).replace("\\", "/"), str(home), str(cwd)]
    assert outputs[0] == outputs[1]
    forbidden += [tempfile.gettempdir(), tempfile.gettempdir().replace("\\", "/")]
    user = getpass.getuser()
    forbidden += [sep + user + sep for sep in ("/", "\\")]
    for raw in outputs[0]:
        text = raw.decode("utf-8")
        assert b"\r" not in raw
        assert text.endswith("\n")
        for f in forbidden:
            assert f not in text, "a computer path in the reference: %r" % f
        assert not re.search(r"(?<![A-Za-z])[A-Za-z]:[\\/]", text), re.search(r"(?<![A-Za-z])[A-Za-z]:[\\/].{0,40}", text).group(0)
        for home_root in ("/home/", "/Users/"):
            assert home_root not in text
    data = json.loads(outputs[0][0].decode("utf-8"))
    opts = {o["option_strings"][0]: o for o in _entry(data, "workflow-check.py")["options"]}
    assert opts["--open-list"]["default"] == "<bridge folder>/workflow/open-list.md"
    assert opts["--registry"]["default"] == "<bridge folder>/workflow/extension-points.md"


def test_cfgb3b_other_absolute_default_is_refused(tmp_path):
    """Criterion 4: an absolute default outside the program's own folder exits non-zero, names the program and the
    option, and writes nothing."""
    sb = _sandbox(tmp_path / "sb")
    (sb / "bridge" / "cursor-bridge" / "zz-abs.py").write_text(PROGRAM_ABS, encoding="utf-8")
    p = _run(sb, cwd=sb)
    assert p.returncode != 0
    out = p.stdout + p.stderr
    assert "zz-abs.py" in out and "--where" in out
    assert not (sb / JSON_REL).exists() and not (sb / MD_REL).exists()


def test_cfgb3b_json_layout(tmp_path):
    """Requirement 2: one object, sorted keys, indent 2, a final newline; LF; UTF-8."""
    sb = _sandbox(tmp_path / "sb")
    data = _generated(sb)
    text = (sb / JSON_REL).read_text(encoding="utf-8")
    assert text in {json.dumps(data, indent=2, sort_keys=True, ensure_ascii=a) + "\n" for a in (True, False)}
    assert set(data) >= {"commands"}


def test_cfgb3b_markdown_is_rendered_from_the_json(tmp_path):
    """Requirement 3: the Markdown names every command, every option string of an argparse command, every line of a
    docstring command's usage, and the placeholder defaults; LF only."""
    sb = _sandbox(tmp_path / "sb")
    data = _generated(sb)
    raw = (sb / MD_REL).read_bytes()
    assert b"\r" not in raw
    md = raw.decode("utf-8")
    for c in data["commands"]:
        assert c["name"] in md, c["name"]
        if c["source"] == "argparse":
            for a in c["options"] + [o for s in c["subcommands"] for o in s["options"]]:
                for s in a["option_strings"]:
                    assert s in md, (c["name"], s)
        else:
            for line in c["usage"].splitlines():
                if line.strip():
                    assert line.strip() in md, (c["name"], line)
    assert "<bridge folder>/workflow/open-list.md" in md


# --- criteria 5-8: --check ----------------------------------------------------------------------------------------

def _fresh(tmp_path):
    sb = _sandbox(tmp_path / "sb")
    _generated(sb)
    return sb, (sb / JSON_REL).read_bytes(), (sb / MD_REL).read_bytes()


def test_cfgb3b_check_passes_when_both_match_and_writes_nothing(tmp_path):
    """Criterion 5."""
    sb, j, m = _fresh(tmp_path)
    p = _run(sb, "--check")
    assert p.returncode == 0, p.stdout + p.stderr
    assert (sb / JSON_REL).read_bytes() == j and (sb / MD_REL).read_bytes() == m


@pytest.mark.parametrize("stale,other", [(JSON_REL, MD_REL), (MD_REL, JSON_REL)])
def test_cfgb3b_check_names_the_one_stale_file(tmp_path, stale, other):
    """Criterion 6: exit 1 naming only the stale file; nothing is rewritten."""
    sb, _, _ = _fresh(tmp_path)
    target = sb / stale
    changed = target.read_text(encoding="utf-8").replace("plan-check.py", "plan-checks.py", 1)
    assert changed != target.read_text(encoding="utf-8")
    target.write_text(changed, encoding="utf-8", newline="\n")
    p = _run(sb, "--check")
    out = p.stdout + p.stderr
    assert p.returncode == 1
    assert stale in out and other not in out
    assert target.read_text(encoding="utf-8") == changed


@pytest.mark.parametrize("missing", [JSON_REL, MD_REL])
def test_cfgb3b_check_counts_a_missing_file_as_stale(tmp_path, missing):
    """Criterion 6 (Requirement 6: either file differs or is missing)."""
    sb, _, _ = _fresh(tmp_path)
    (sb / missing).unlink()
    p = _run(sb, "--check")
    assert p.returncode == 1 and missing in p.stdout + p.stderr
    assert not (sb / missing).exists()


@pytest.mark.parametrize("args", [("--nope",), ("--check", "extra"), ("extra",)])
def test_cfgb3b_usage_error_exits_2_and_writes_nothing(tmp_path, args):
    """Criterion 7: any other argument is a usage error, with a usage line, and nothing is written."""
    sb = _sandbox(tmp_path / "sb")
    p = _run(sb, *args)
    assert p.returncode == 2, p.stdout + p.stderr
    assert "usage" in (p.stdout + p.stderr).lower()
    assert not (sb / JSON_REL).exists() and not (sb / MD_REL).exists()


def test_cfgb3b_check_accepts_a_crlf_copy(tmp_path):
    """Criterion 8: the Windows runner checks the files out with CRLF; that copy matches."""
    sb, j, m = _fresh(tmp_path)
    (sb / JSON_REL).write_bytes(j.replace(b"\n", b"\r\n"))
    (sb / MD_REL).write_bytes(m.replace(b"\n", b"\r\n"))
    p = _run(sb, "--check")
    assert p.returncode == 0, p.stdout + p.stderr


# --- criterion 9: the extraction ----------------------------------------------------------------------------------

@pytest.mark.parametrize("name", EXTRACTED)
def test_cfgb3b_program_builds_its_parser_in_build_parser(name):
    """Criterion 9: a module-level build_parser() taking no argument, and main() (still `def main():`) calling it."""
    path = BRIDGE / name
    bp = _top_function(path, "build_parser")
    assert bp is not None, name
    assert not (bp.args.args or bp.args.posonlyargs or bp.args.kwonlyargs or bp.args.vararg or bp.args.kwarg), name
    main = _top_function(path, "main")
    assert main is not None and not (main.args.args or main.args.vararg or main.args.kwarg), name
    calls = [n for n in ast.walk(main) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
             and n.func.id == "build_parser"]
    assert calls, "%s: main() does not call build_parser()" % name
    parsers_in_main = [n for n in ast.walk(main) if isinstance(n, ast.Attribute) and n.attr == "ArgumentParser"]
    assert not parsers_in_main, "%s: main() still builds a parser of its own" % name


# --- criterion 10: the committed files are current ----------------------------------------------------------------

def test_cfgb3b_committed_reference_is_current():
    """Criterion 10: the repository's own `--check` passes (the committed docs/cli-reference.json and
    docs/CLI_REFERENCE.md equal a fresh generation); conformance-check.py looks for this file's --check."""
    p = subprocess.run([sys.executable, str(GEN), "--check"], cwd=str(ROOT), capture_output=True, text=True,
                       encoding="utf-8", timeout=120)
    assert p.returncode == 0, p.stdout + p.stderr


# --- criteria 11-13: CI and the pre-commit gate -------------------------------------------------------------------

def _tests_steps():
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]["tests"]["steps"]


def test_cfgb3b_ci_runs_the_check_in_the_tests_job():
    """Criterion 11: the tests job (both operating systems) runs the check right after the manifest step, under a name
    carrying cli-reference; the workflow-check step stays last."""
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "cli-reference" in text
    job = yaml.safe_load(text)["jobs"]["tests"]
    assert job["strategy"]["matrix"]["os"] == ["windows-latest", "ubuntu-latest"]
    steps = job["steps"]
    runs = [s.get("run") for s in steps]
    i = runs.index(CHECK_CMD)
    assert "cli-reference" in steps[i]["name"]
    assert steps[i - 1]["name"] == "the manifest matches the tree"
    assert "workflow-check.py" in steps[-1]["run"] and i == len(steps) - 2
    assert "continue-on-error" not in steps[i] and "if" not in steps[i]


def test_cfgb3b_ci_windowless_step_covers_the_hook_folder():
    """Criterion 13."""
    step = [s for s in _tests_steps() if s.get("name") == "windowless check over the bridge's programs"]
    assert len(step) == 1
    assert step[0]["run"] == "python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks"


def test_cfgb3b_pre_commit_runs_the_check_after_the_windowless_check():
    """Criterion 12 (text): the check follows the windowless check and a non-zero result exits 1."""
    raw = PRE_COMMIT.read_bytes()
    assert b"\r" not in raw
    text = raw.decode("utf-8")
    assert text.startswith("#!/bin/sh")
    w = text.index("windowless-check.py")
    c = text.index(CHECK_CMD)
    assert w < c
    assert "exit 1" in text[c:]


@pytest.mark.skipif(shutil.which("sh") is None, reason="no POSIX sh on this computer")
def test_cfgb3b_pre_commit_blocks_a_stale_reference(tmp_path):
    """Criterion 12 (behaviour): the pre-commit gate run in a copy passes with a current reference and exits 1 with the
    regeneration command named when the reference is stale."""
    sb, _, _ = _fresh(tmp_path)
    (sb / ".githooks").mkdir()
    shutil.copyfile(PRE_COMMIT, sb / ".githooks" / "pre-commit")
    shutil.copytree(ROOT / ".cursor" / "hooks", sb / ".cursor" / "hooks")
    env = dict(os.environ, PATH=os.path.dirname(sys.executable) + os.pathsep + os.environ.get("PATH", ""))
    run = lambda: subprocess.run([shutil.which("sh"), ".githooks/pre-commit"], cwd=str(sb), env=env,
                                 capture_output=True, text=True, encoding="utf-8", timeout=120)
    ok = run()
    assert ok.returncode == 0, ok.stdout + ok.stderr
    (sb / JSON_REL).write_text("{}\n", encoding="utf-8", newline="\n")
    bad = run()
    assert bad.returncode == 1
    assert "python tools/dump-cli.py" in bad.stderr


# --- the generator's own text -------------------------------------------------------------------------------------

def test_cfgb3b_generator_follows_the_program_conventions():
    """Constraints: ASCII-only program text, the shebang, a module docstring holding the usage."""
    raw = GEN.read_bytes()
    assert all(b < 128 for b in raw)
    text = raw.decode("ascii")
    assert text.startswith("#!/usr/bin/env python3")
    doc = ast.get_docstring(ast.parse(text)) or ""
    assert "--check" in doc


# --- round 2 (handoff/CONFIG-B3b-r2.md): the reviewers' findings ----------------------------------------------------
# Review A S1-S3, S5, S6, C1, C2, C4, C5 and the security auditor's advisories 1, 2 and 5 (two converged: S1 = advisory 1,
# S2 = advisory 2). Each refused case also writes nothing.

def _argparse_program(body, doc='"""zz test program."""'):
    """A command with a top-level build_parser(); HERE is its own folder. `body` holds the add_argument lines."""
    return (doc + "\nimport argparse\nimport os\n\nHERE = os.path.dirname(os.path.abspath(__file__))\n\n\n"
            "def build_parser():\n    p = argparse.ArgumentParser(description=\"zz\")\n" + body +
            "    return p\n\n\nif __name__ == \"__main__\":\n    build_parser().parse_args()\n")


PROGRAM_LIST_IN = _argparse_program(
    '    p.add_argument("--files", nargs="*", default=[os.path.join(HERE, "workflow", "open-list.md"), "plain"])\n')
PROGRAM_LIST_OUT = _argparse_program(
    '    p.add_argument("--files", nargs="*", default=["plain", os.path.abspath(os.path.join(HERE, os.pardir, "elsewhere"))])\n')
PROGRAM_HELP_PATH = _argparse_program('    p.add_argument("--x", help="see " + HERE)\n')
PROGRAM_DESC_HOME = _argparse_program('    p.description = os.path.expanduser("~") + " notes"\n')
PROGRAM_NODOC = 'import sys\n\n\ndef main():\n    return 0\n\n\nif __name__ == "__main__":\n    sys.exit(main())\n'


def _refused(tmp_path, name, source, *names):
    """The generator and --check each exit 1 naming `name` (and each of `names`), and write nothing."""
    sb = _sandbox(tmp_path / "sb")
    (sb / "bridge" / "cursor-bridge" / name).write_text(source, encoding="utf-8")
    for args in ((), ("--check",)):
        p = _run(sb, *args, cwd=sb)
        out = p.stdout + p.stderr
        assert p.returncode == 1, (args, out)
        assert "Traceback" not in out, out
        for n in (name,) + names:
            assert n in out, (args, n, out)
        assert not (sb / JSON_REL).exists() and not (sb / MD_REL).exists()


def test_cfgb3b_r2_check_exits_1_when_the_generator_refuses(tmp_path):
    """Review A S5: --check returns the refusal, not 0, for a parser without build_parser() and an outside default."""
    _refused(tmp_path / "bad", "zz-bad.py", PROGRAM_BAD)
    _refused(tmp_path / "abs", "zz-abs.py", PROGRAM_ABS, "--where")


def test_cfgb3b_r2_list_default_under_the_bridge_takes_the_placeholder(tmp_path):
    """S1 / advisory 1: a path inside a list default is judged like a string default."""
    sb = _sandbox(tmp_path / "sb")
    (sb / "bridge" / "cursor-bridge" / "zz-list.py").write_text(PROGRAM_LIST_IN, encoding="utf-8")
    data = _generated(sb)
    files = [o for o in _entry(data, "zz-list.py")["options"] if o["option_strings"] == ["--files"]][0]
    assert files["default"] == ["<bridge folder>/workflow/open-list.md", "plain"]


def test_cfgb3b_r2_list_default_outside_the_bridge_is_refused(tmp_path):
    """S1 / advisory 1."""
    _refused(tmp_path, "zz-list.py", PROGRAM_LIST_OUT, "--files")


@pytest.mark.skipif(sys.platform != "win32", reason="a second drive letter exists only on Windows")
def test_cfgb3b_r2_default_on_another_drive_is_refused_by_name(tmp_path):
    """S2 / advisory 2: os.path.relpath raises ValueError across drives; the refusal names the program and the option."""
    drive = os.path.splitdrive(str(tmp_path))[0].upper()
    other = "E:/elsewhere/x" if drive != "E:" else "C:/elsewhere/x"
    source = _argparse_program('    p.add_argument("--far", default=%r)\n' % other)
    _refused(tmp_path, "zz-far.py", source, "--far")


def test_cfgb3b_r2_help_or_description_holding_a_path_is_refused(tmp_path):
    """Advisory 1 / Requirement 5: any string of the reference holding the repository's folder or the home folder is
    refused, naming the program."""
    _refused(tmp_path / "help", "zz-help.py", PROGRAM_HELP_PATH)
    _refused(tmp_path / "desc", "zz-desc.py", PROGRAM_DESC_HOME)


def test_cfgb3b_r2_command_without_docstring_is_refused(tmp_path):
    """S3: a hand-parsed command with no module docstring exits 1 naming it (no traceback)."""
    _refused(tmp_path, "zz-nodoc.py", PROGRAM_NODOC)


def test_cfgb3b_r2_the_trap_programs_would_leave_their_files(tmp_path):
    """Advisory 5: the precondition of test_cfgb3b_new_programs_are_found_and_none_is_run - run directly, each trap
    program does leave its file, so that test's absence check means something."""
    folder = tmp_path / "direct"
    folder.mkdir()
    for name, source, marker, args in (("zz-trap.py", PROGRAM_TRAP, "RAN-IMPORT", ()),
                                       ("zz-argp.py", PROGRAM_ARGP, "RAN-MAIN", ("t",))):
        (folder / name).write_text(source, encoding="utf-8")
        subprocess.run([sys.executable, str(folder / name), *args], cwd=str(folder), capture_output=True, timeout=60)
        assert (folder / marker).exists(), name


def test_cfgb3b_r2_no_bytecode_is_written(tmp_path):
    """C1 / Requirement 6: neither a run nor --check leaves __pycache__ in the bridge folder (bytecode writing is off
    while the argparse programs are imported), whatever PYTHONDONTWRITEBYTECODE says."""
    sb = _sandbox(tmp_path / "sb")
    env = {k: v for k, v in os.environ.items() if k != "PYTHONDONTWRITEBYTECODE"}
    for args in ((), ("--check",)):
        p = _run(sb, *args, env=env)
        assert p.returncode == 0, p.stdout + p.stderr
        assert not (sb / "bridge" / "cursor-bridge" / "__pycache__").exists(), args


def test_cfgb3b_r2_an_abbreviated_option_is_a_usage_error(tmp_path):
    """C2: --che is not --check (no abbreviation); exit 2, nothing written."""
    sb = _sandbox(tmp_path / "sb")
    p = _run(sb, "--che")
    assert p.returncode == 2, p.stdout + p.stderr
    assert not (sb / JSON_REL).exists() and not (sb / MD_REL).exists()


def _md_regions(md):
    """The Markdown's lines outside fenced blocks, with their indexes."""
    out, fenced = [], False
    for i, line in enumerate(md.split("\n")):
        if line.startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            out.append((i, line))
    return out


def _fenced(text):
    return "```\n" + "\n".join(text.splitlines()) + "\n```"


def test_cfgb3b_r2_markdown_shows_each_action_whole(tmp_path):
    """S6, C4, C5 / Requirement 3: under each command's heading (and each sub-command's), every action has one line
    naming it in backticks (option strings joined by a space, or the dest of a positional) and showing its default in
    JSON (null included), `required: true|false` and each choice in JSON; descriptions and usages are fenced."""
    sb = _sandbox(tmp_path / "sb")
    (sb / "bridge" / "cursor-bridge" / "zz-argp.py").write_text(PROGRAM_ARGP, encoding="utf-8")
    data = _generated(sb)
    md = (sb / MD_REL).read_text(encoding="utf-8")
    lines = _md_regions(md)
    names = [c["name"] for c in data["commands"]]
    heads = [(i, l) for i, l in lines if l.startswith("#")]

    def region(start_name, within=None):
        lo, hi = within or (0, len(md.split("\n")))
        start = next(i for i, l in heads if lo <= i < hi and start_name in l)
        end = next((i for i, l in heads if start < i < hi and any(n in l for n in names if n != start_name)), hi)
        return start, end

    def check(actions, lo, hi, where):
        for a in actions:
            label = "`%s`" % (" ".join(a["option_strings"]) if a["option_strings"] else a["dest"])
            hits = [l for i, l in lines if lo < i < hi and label in l and "required:" in l]
            assert len(hits) == 1, (where, label, hits)
            line = hits[0]
            assert "required: %s" % json.dumps(a["required"]) in line, (where, label)
            assert json.dumps(a["default"]) in line, (where, label)
            for c in a["choices"] or []:
                assert json.dumps(c) in line, (where, label, c)

    for c in data["commands"]:
        lo, hi = region(c["name"])
        if c["source"] == "docstring":
            assert _fenced(c["usage"]) in md, c["name"]
            continue
        if c["description"]:
            assert _fenced(c["description"]) in md, c["name"]
        sub_starts = [next(i for i, l in heads if lo < i < hi and s["name"] in l) for s in c["subcommands"]]
        check(c["positionals"] + c["options"], lo, min(sub_starts + [hi]), c["name"])
        for s in c["subcommands"]:
            s_lo = next(i for i, l in heads if lo < i < hi and s["name"] in l)
            s_hi = next((i for i, l in heads if s_lo < i < hi and any(o["name"] in l for o in c["subcommands"]
                                                                       if o["name"] != s["name"])), hi)
            if s["description"]:
                assert _fenced(s["description"]) in md
            check(s["positionals"] + s["options"], s_lo, s_hi, (c["name"], s["name"]))
    record = [s for s in _entry(data, "evaluate-reports.py")["subcommands"] if s["name"] == "record"][0]
    assert record["positionals"], "evaluate-reports record has positionals to show"


# --- round 3 (handoff/CONFIG-B3b-r3.md): the security re-check's findings ------------------------------------------
# Blocking: the string check read a default through json.dumps, which doubles backslashes, so a home path inside a
# default never matched on Windows; a dict default was never judged. Advisories: case and slash forms of the folders,
# sub-command names, os.PathLike defaults.

HOME_EXPR = 'os.path.join(os.path.expanduser("~"), "Documents")'


def test_cfgb3b_r3_a_path_inside_a_string_default_is_refused(tmp_path):
    """Blocking (security re-check): a default that is not itself absolute but holds the home folder is refused, naming
    the option; the check reads the string, not its JSON text."""
    _refused(tmp_path, "zz-str.py", _argparse_program('    p.add_argument("--out", default="out=" + %s)\n' % HOME_EXPR),
             "--out")


def test_cfgb3b_r3_a_dict_default_is_judged_like_a_list(tmp_path):
    """Blocking: a dict default's values are judged at any depth - a path under the program's folder takes the
    placeholder, any other absolute path is refused naming the option."""
    sb = _sandbox(tmp_path / "sb")
    source = _argparse_program(
        '    p.add_argument("--map", default={"k": os.path.join(HERE, "workflow", "open-list.md"), "n": 1})\n')
    (sb / "bridge" / "cursor-bridge" / "zz-map.py").write_text(source, encoding="utf-8")
    data = _generated(sb)
    opt = [o for o in _entry(data, "zz-map.py")["options"] if o["option_strings"] == ["--map"]][0]
    assert opt["default"] == {"k": "<bridge folder>/workflow/open-list.md", "n": 1}
    _refused(tmp_path / "out", "zz-map.py",
             _argparse_program('    p.add_argument("--map", default={"k": %s})\n' % HOME_EXPR), "--map")


def test_cfgb3b_r3_a_pathlike_default_is_a_path(tmp_path):
    """Advisory: an os.PathLike default (pathlib.Path) is judged as its string - the placeholder under the program's
    folder, a refusal by name elsewhere, never a traceback."""
    sb = _sandbox(tmp_path / "sb")
    source = _argparse_program('    import pathlib\n'
                               '    p.add_argument("--where", default=pathlib.Path(HERE) / "workflow" / "open-list.md")\n')
    (sb / "bridge" / "cursor-bridge" / "zz-pl.py").write_text(source, encoding="utf-8")
    data = _generated(sb)
    opt = [o for o in _entry(data, "zz-pl.py")["options"] if o["option_strings"] == ["--where"]][0]
    assert opt["default"] == "<bridge folder>/workflow/open-list.md"
    _refused(tmp_path / "out", "zz-pl.py",
             _argparse_program('    import pathlib\n    p.add_argument("--where", default=pathlib.Path(%s))\n' % HOME_EXPR),
             "--where")


def test_cfgb3b_r3_the_home_folder_in_forward_slashes_is_refused(tmp_path):
    """Advisory: the home folder written with forward slashes in a help text is refused (the comparison folds the
    separators, as os.path.normcase does on Windows)."""
    _refused(tmp_path, "zz-fs.py", _argparse_program(
        '    p.add_argument("--x", help="see " + os.path.expanduser("~").replace(os.sep, "/"))\n'), "--x")


@pytest.mark.skipif(sys.platform != "win32", reason="paths ignore case only on Windows")
def test_cfgb3b_r3_the_home_folder_in_another_case_is_refused(tmp_path):
    """Advisory: on Windows the home folder in upper case in a help text, and in lower case in a docstring usage, is
    refused."""
    _refused(tmp_path / "help", "zz-up.py", _argparse_program(
        '    p.add_argument("--x", help="see " + os.path.expanduser("~").upper())\n'), "--x")
    usage = '"""zz-low: see %s."""\n' % os.path.expanduser("~").lower().replace("\\", "/")
    _refused(tmp_path / "doc", "zz-low.py", usage + PROGRAM_NODOC)


def test_cfgb3b_r3_a_subcommand_named_by_a_path_is_refused(tmp_path):
    """Advisory: sub-command names, option strings and dests are checked like every other string."""
    _refused(tmp_path, "zz-sub.py", _argparse_program(
        '    sub = p.add_subparsers(dest="cmd")\n    sub.add_parser(%s)\n' % HOME_EXPR))


# Review A's round-2 survivors (S2), each with the input that separates it.

def _option(tmp_path, name, body, option):
    sb = _sandbox(tmp_path / "sb")
    (sb / "bridge" / "cursor-bridge" / name).write_text(_argparse_program(body), encoding="utf-8")
    data = _generated(sb)
    return sb, data, [o for o in _entry(data, name)["options"] if o["option_strings"] == [option]][0]


def test_cfgb3b_r3_the_repository_folder_in_forward_slashes_is_refused(tmp_path):
    """x1: the repository's folder written with forward slashes in a help text."""
    _refused(tmp_path, "zz-rs.py", _argparse_program('    p.add_argument("--x", help="see " + HERE.replace(os.sep, "/"))\n'),
             "--x")


def test_cfgb3b_r3_the_current_folder_is_refused(tmp_path):
    """x2: run from a folder outside the repository and the home folder, a help text holding the current folder."""
    sb = _sandbox(tmp_path / "sb")
    (sb / "bridge" / "cursor-bridge" / "zz-cwd.py").write_text(
        _argparse_program('    p.add_argument("--x", help="from " + os.getcwd())\n'), encoding="utf-8")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    for args in ((), ("--check",)):
        p = _run(sb, *args, cwd=elsewhere)
        out = p.stdout + p.stderr
        assert p.returncode == 1 and "zz-cwd.py" in out and "--x" in out and "Traceback" not in out, (args, out)
    assert not (sb / JSON_REL).exists()


def test_cfgb3b_r3_a_home_at_the_filesystem_root_is_not_a_fragment(tmp_path):
    """x3: with the home folder at the filesystem root, the repository's own reference still generates (a root would
    match every path)."""
    sb = _sandbox(tmp_path / "sb")
    anchor = pathlib.Path(tmp_path).anchor
    env = dict(os.environ, HOME=anchor, USERPROFILE=anchor)
    p = _run(sb, env=env)
    assert p.returncode == 0, p.stdout + p.stderr


def test_cfgb3b_r3_a_choice_holding_a_path_is_refused(tmp_path):
    """x5."""
    _refused(tmp_path, "zz-ch.py", _argparse_program('    p.add_argument("--x", choices=["a", HERE])\n'), "--x")


def test_cfgb3b_r3_a_docstring_holding_the_repository_folder_is_refused(tmp_path):
    """x6: a hand-parsed command whose usage text holds the repository's folder literally."""
    sb_path = tmp_path / "sb"
    usage = '"""zz-doc: installed at %s."""\n' % str(sb_path).replace("\\", "/")
    _refused(tmp_path, "zz-doc.py", usage + PROGRAM_NODOC)


def test_cfgb3b_r3_a_subcommand_description_holding_a_path_is_refused(tmp_path):
    """x7."""
    _refused(tmp_path, "zz-sd.py", _argparse_program(
        '    sub = p.add_subparsers(dest="cmd")\n    sub.add_parser("go", description="in " + HERE)\n'))


def test_cfgb3b_r3_a_name_starting_with_two_dots_is_inside(tmp_path):
    """x8: a file under the program's folder whose name starts with '..' is inside it: the placeholder."""
    _, _, opt = _option(tmp_path, "zz-dd.py", '    p.add_argument("--x", default=os.path.join(HERE, "..foo"))\n', "--x")
    assert opt["default"] == "<bridge folder>/..foo"


def test_cfgb3b_r3_the_parent_folder_itself_is_refused(tmp_path):
    """x9: a default equal to the parent of the program's folder is outside it."""
    _refused(tmp_path, "zz-par.py", _argparse_program('    p.add_argument("--x", default=os.path.dirname(HERE))\n'), "--x")


def test_cfgb3b_r3_tuple_and_nested_list_defaults(tmp_path):
    """x10, x12: a tuple default and a nested list default are judged element by element."""
    _, _, opt = _option(tmp_path / "t", "zz-tu.py",
                        '    p.add_argument("--x", nargs=2, default=(os.path.join(HERE, "a"), "b"))\n', "--x")
    assert opt["default"] == ["<bridge folder>/a", "b"]
    _, _, opt = _option(tmp_path / "n", "zz-ne.py", '    p.add_argument("--x", default=[[os.path.join(HERE, "a")], "b"])\n',
                        "--x")
    assert opt["default"] == [["<bridge folder>/a"], "b"]


@pytest.mark.parametrize("before", [False, True])
def test_cfgb3b_r3_the_bytecode_flag_is_restored(tmp_path, before):
    """x11: build_reference leaves sys.dont_write_bytecode as it found it."""
    sb = _sandbox(tmp_path / "sb")
    gen = _load(sb / "tools" / "dump-cli.py", "flag%d" % before)
    saved = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = before
        gen.build_reference(str(sb))
        assert sys.dont_write_bytecode is before
    finally:
        sys.dont_write_bytecode = saved


def test_cfgb3b_r3_a_subcommand_description_is_fenced(tmp_path):
    """x14: a sub-command's description is shown in a fenced block."""
    sb = _sandbox(tmp_path / "sb")
    (sb / "bridge" / "cursor-bridge" / "zz-sf.py").write_text(_argparse_program(
        '    sub = p.add_subparsers(dest="cmd")\n    sub.add_parser("go", description="zz sub description")\n'),
        encoding="utf-8")
    _generated(sb)
    assert _fenced("zz sub description") in (sb / MD_REL).read_text(encoding="utf-8")


def test_cfgb3b_r3_each_action_is_a_list_item(tmp_path):
    """Review A B2: each action line is a Markdown list item ("- " first) whose fields are separated by "; ", so the
    lines of a section do not run together into one paragraph."""
    sb = _sandbox(tmp_path / "sb")
    data = _generated(sb)
    md = (sb / MD_REL).read_text(encoding="utf-8")
    action_lines = [l for _, l in _md_regions(md) if "required: " in l]
    assert action_lines
    for line in action_lines:
        assert line.startswith("- `"), line
        assert "; default: " in line and "; required: " in line, line


# --- round 4 (handoff/CONFIG-B3b-r4.md): the security re-check's round-3 findings and Review A's -----------------
# Blocking (security re-check): a folder was found only in its one written form; doubled backslashes (a list or JSON
# written into a text), the Git Bash and WSL forms and the form without its drive letter went through. Convergent (the
# supervisor, the security re-check, Review A S1): a dict default whose keys cannot be JSON keys ended in a traceback.
# Advisories: the type field and non-string choices were not checked; a NaN default wrote non-standard JSON. Review A
# S2: parts of Requirement 2 had no test that separates them.

HOME_SPLIT = 'd, rest = os.path.splitdrive(os.path.expanduser("~"))\n'


def test_cfgb3b_r4_a_folder_written_with_doubled_backslashes_is_refused(tmp_path):
    """Blocking: a help text holding a list of paths (Python writes each backslash twice) and a description holding a
    JSON example are refused; the text really holds the doubled form on Windows."""
    if sys.platform == "win32":
        assert "\\\\" in repr([os.path.expanduser("~")]) and "\\\\" in json.dumps(os.path.expanduser("~"))
    _refused(tmp_path / "repr", "zz-rp.py", _argparse_program(
        '    p.add_argument("--x", help="searches %r" % [os.path.expanduser("~")])\n'), "--x")
    _refused(tmp_path / "json", "zz-js.py", _argparse_program(
        '    import json\n    p.description = "example: " + json.dumps({"dir": os.path.expanduser("~")})\n'))


@pytest.mark.parametrize("form", ['"/" + d[:1].lower() + rest.replace(os.sep, "/")',
                                  '"/mnt/" + d[:1].lower() + rest.replace(os.sep, "/")',
                                  "rest"])
def test_cfgb3b_r4_the_home_folder_without_its_drive_is_refused(tmp_path, form):
    """Blocking: the home folder in the Git Bash form (/c/Users/...), the WSL form (/mnt/c/Users/...) and with no drive
    letter (\\Users\\...) is refused, in a help text."""
    _refused(tmp_path, "zz-nd.py", _argparse_program("    " + HOME_SPLIT + '    p.add_argument("--x", help="see " + %s)\n'
                                                     % form), "--x")


def test_cfgb3b_r4_a_folder_written_with_doubled_forward_slashes_is_refused(tmp_path):
    """Blocking: the repository's folder with its separators doubled (a URL-like or escaped form) is refused."""
    _refused(tmp_path, "zz-dfs.py", _argparse_program(
        '    p.add_argument("--x", help="see " + HERE.replace(os.sep, "//"))\n'), "--x")


def test_cfgb3b_r4_a_home_at_the_root_of_a_drive_is_still_not_a_fragment(tmp_path):
    """The folder without its drive is skipped where it is the root: a home at the root of its drive leaves the
    repository's own reference to generate."""
    sb = _sandbox(tmp_path / "sb")
    anchor = pathlib.Path(tmp_path).anchor
    env = dict(os.environ, HOME=anchor, USERPROFILE=anchor)
    p = _run(sb, env=env)
    assert p.returncode == 0, p.stdout + p.stderr
    assert json.loads((sb / JSON_REL).read_text(encoding="utf-8"))["commands"]


@pytest.mark.parametrize("default", ['{("a", "b"): 1}', '{1: "a", "b": 2}', '{1: "a"}', '{pathlib.Path("a"): 1, "a": 2}'])
def test_cfgb3b_r4_a_dict_default_whose_keys_are_not_distinct_strings_is_refused(tmp_path, default):
    """Convergent (the supervisor, the security re-check, Review A S1): a key that is not a string or os.PathLike, or
    two keys that walk to one string, are refused naming the option, never a traceback."""
    _refused(tmp_path, "zz-dk.py", _argparse_program('    import pathlib\n    p.add_argument("--map", default=%s)\n'
                                                     % default), "--map")


def test_cfgb3b_r4_a_pathlike_dict_key_takes_the_placeholder(tmp_path):
    """A dict key that is an os.PathLike under the program's folder becomes the placeholder string."""
    _, _, opt = _option(tmp_path, "zz-pk.py", '    import pathlib\n'
                        '    p.add_argument("--map", default={pathlib.Path(HERE) / "a": 1})\n', "--map")
    assert opt["default"] == {"<bridge folder>/a": 1}


@pytest.mark.parametrize("value", ['float("nan")', 'float("inf")', '[float("-inf")]'])
def test_cfgb3b_r4_a_default_that_is_not_a_json_number_is_refused(tmp_path, value):
    """Review A noted 2: NaN and the infinities are not JSON; a default holding one is refused naming the option."""
    _refused(tmp_path, "zz-nan.py", _argparse_program('    p.add_argument("--x", type=float, default=%s)\n' % value),
             "--x")


def test_cfgb3b_r4_a_type_named_by_a_path_is_refused(tmp_path):
    """Advisory: the type field is checked like the dest."""
    _refused(tmp_path, "zz-ty.py", _argparse_program(
        '    def conv(s):\n        return s\n    conv.__name__ = os.path.expanduser("~")\n'
        '    p.add_argument("--x", type=conv)\n'), "--x")


@pytest.mark.parametrize("choices", ['[("a", os.path.expanduser("~"))]', '["a", pathlib.Path(os.path.expanduser("~"))]'])
def test_cfgb3b_r4_a_choice_that_is_not_a_string_is_walked(tmp_path, choices):
    """Advisory: choices are walked like a default (a tuple holding a path, an os.PathLike), refused naming the option,
    never a traceback."""
    _refused(tmp_path, "zz-cw.py", _argparse_program('    import pathlib\n    p.add_argument("--x", choices=%s)\n'
                                                     % choices), "--x")


def test_cfgb3b_r4_a_choice_under_the_program_folder_takes_the_placeholder(tmp_path):
    """A choice that is an absolute path under the program's folder is written as the placeholder, as a default is."""
    _, _, opt = _option(tmp_path, "zz-cp.py", '    p.add_argument("--x", choices=["a", os.path.join(HERE, "b")])\n', "--x")
    assert opt["choices"] == ["a", "<bridge folder>/b"]


@pytest.mark.parametrize("default", ['{"k": "out=" + %s}' % HOME_EXPR, '{"out=" + %s: 1}' % HOME_EXPR,
                                     '[{"k": {"j": "out=" + %s}}]' % HOME_EXPR])
def test_cfgb3b_r4_a_dict_value_or_key_holding_a_path_is_refused(tmp_path, default):
    """Review A S2 (survivors 1-3): a dict value, a dict key and a value two dicts deep that hold the home folder inside
    a string (not an absolute path) are refused by the string check, naming the option."""
    _refused(tmp_path, "zz-dv.py", _argparse_program('    p.add_argument("--map", default=%s)\n' % default), "--map")


def test_cfgb3b_r4_an_option_string_or_dest_holding_a_path_is_refused(tmp_path):
    """Review A S2 (survivor 4): an option string and a dest holding the home folder are each refused."""
    _refused(tmp_path / "os", "zz-os.py", _argparse_program(
        '    p.add_argument("--x", "--in-" + %s)\n' % HOME_EXPR), "--x")
    _refused(tmp_path / "de", "zz-de.py", _argparse_program(
        '    p.add_argument("--x", dest="d" + %s)\n' % HOME_EXPR), "--x")


def test_cfgb3b_r4_the_repository_folder_is_refused_from_another_folder(tmp_path):
    """Review A S2 (the repository fragment): run from a folder that is neither the repository nor the home folder, a
    help text holding the program's folder is refused by the repository's fragment alone."""
    sb = _sandbox(tmp_path / "sb")
    (sb / "bridge" / "cursor-bridge" / "zz-rf.py").write_text(
        _argparse_program('    p.add_argument("--x", help="in " + HERE)\n'), encoding="utf-8")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    for args in ((), ("--check",)):
        p = _run(sb, *args, cwd=elsewhere)
        out = p.stdout + p.stderr
        assert p.returncode == 1 and "zz-rf.py" in out and "--x" in out and "Traceback" not in out, (args, out)
    assert not (sb / JSON_REL).exists()


@pytest.mark.parametrize("choices", ['["a", "out=" + %s]' % HOME_EXPR, '[("a", "out=" + %s)]' % HOME_EXPR])
def test_cfgb3b_r4_a_choice_holding_a_path_inside_a_string_is_refused(tmp_path, choices):
    """Mutation (y), which round 4's builder found uncaught: a choice that is not an absolute path but holds the home
    folder inside its text, alone or inside a tuple choice, is refused by the string check after the walk."""
    _refused(tmp_path, "zz-cs.py", _argparse_program('    p.add_argument("--x", choices=%s)\n' % choices), "--x")


def test_cfgb3b_r4_a_default_or_choice_that_is_the_program_folder_itself_is_refused(tmp_path):
    """Round 4's builder refuses an absolute path equal to the program's own folder (its relative path would be "."):
    a default and a choice alike; a path under the folder still takes the placeholder (test above)."""
    _refused(tmp_path / "d", "zz-hd.py", _argparse_program('    p.add_argument("--x", default=HERE)\n'), "--x")
    _refused(tmp_path / "c", "zz-hc.py", _argparse_program('    p.add_argument("--x", choices=[HERE])\n'), "--x")
