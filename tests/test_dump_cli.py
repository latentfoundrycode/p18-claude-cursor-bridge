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
ARGPARSE = EXTRACTED + ("workflow-check.py",)
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
