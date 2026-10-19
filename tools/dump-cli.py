#!/usr/bin/env python3
"""dump-cli: write the bridge command reference from each program's parser or docstring.

  python tools/dump-cli.py
  python tools/dump-cli.py --check

Writes docs/cli-reference.json and docs/CLI_REFERENCE.md from bridge/cursor-bridge/*.py.
--check regenerates in memory and compares with the committed files (line endings normalised).
"""
import argparse
import ast
import importlib.util
import json
import math
import os
import re
import sys

BRIDGE_PLACEHOLDER = "<bridge folder>/"
JSON_REL = "docs/cli-reference.json"
MD_REL = "docs/CLI_REFERENCE.md"


def repo_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def is_main_block(node):
    if not isinstance(node, ast.If) or not isinstance(node.test, ast.Compare):
        return False
    t = node.test
    sides = [t.left] + list(t.comparators)
    return (len(t.ops) == 1 and isinstance(t.ops[0], ast.Eq)
            and any(isinstance(s, ast.Name) and s.id == "__name__" for s in sides)
            and any(isinstance(s, ast.Constant) and s.value == "__main__" for s in sides))


def command_programs(bridge_dir):
    names = []
    for name in sorted(os.listdir(bridge_dir)):
        if not name.endswith(".py"):
            continue
        path = os.path.join(bridge_dir, name)
        tree = ast.parse(open(path, encoding="utf-8").read(), filename=path)
        if any(is_main_block(n) for n in tree.body):
            names.append(name)
    return names


def has_top_level_build_parser(path):
    tree = ast.parse(open(path, encoding="utf-8").read(), filename=path)
    return any(isinstance(n, ast.FunctionDef) and n.name == "build_parser" for n in tree.body)


def module_docstring(path):
    tree = ast.parse(open(path, encoding="utf-8").read(), filename=path)
    return ast.get_docstring(tree, clean=False)


def load_bridge_module(path, tag):
    spec = importlib.util.spec_from_file_location(
        "dump_cli_%s_%s" % (tag, os.path.splitext(os.path.basename(path))[0].replace("-", "_")),
        path,
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def jsonable(value):
    return json.loads(json.dumps(value))


class DumpCliError(Exception):
    def __init__(self, code=1):
        self.code = code


def refuse_outside_default(program_name, option_label):
    print("dump-cli: %s: absolute default on %s is outside the bridge folder" % (program_name, option_label),
          file=sys.stderr)
    raise DumpCliError(1)


def refuse_bad_default(program_name, option_label):
    print("dump-cli: %s: default on %s is not JSON-serializable" % (program_name, option_label), file=sys.stderr)
    raise DumpCliError(1)


def path_canonical(text):
    s = os.path.normcase(text)
    return re.sub(r"[\\/]+", "/", s)


def action_label(action):
    option_strings = action["option_strings"] if isinstance(action, dict) else action.option_strings
    if option_strings:
        return option_strings[0]
    return action["dest"] if isinstance(action, dict) else action.dest


def absolute_default_to_placeholder(value, bridge_dir, program_name, option_label):
    try:
        rel = os.path.relpath(value, bridge_dir)
    except ValueError:
        refuse_outside_default(program_name, option_label)
    if rel in (".", "") or rel == os.pardir or rel.startswith(os.pardir + os.sep):
        refuse_outside_default(program_name, option_label)
    return BRIDGE_PLACEHOLDER + rel.replace(os.sep, "/")


def default_for_json(value, bridge_dir, program_name, option_label):
    if isinstance(value, (list, tuple)):
        return [default_for_json(v, bridge_dir, program_name, option_label) for v in value]
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            wk = default_for_json(k, bridge_dir, program_name, option_label)
            if not isinstance(wk, str):
                refuse_bad_default(program_name, option_label)
            if wk in out:
                refuse_bad_default(program_name, option_label)
            out[wk] = default_for_json(v, bridge_dir, program_name, option_label)
        return out
    if isinstance(value, os.PathLike):
        return default_for_json(os.fspath(value), bridge_dir, program_name, option_label)
    if isinstance(value, str):
        if os.path.isabs(value):
            return absolute_default_to_placeholder(value, bridge_dir, program_name, option_label)
        return value
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            refuse_bad_default(program_name, option_label)
        return value
    refuse_bad_default(program_name, option_label)


def action_entry(action, bridge_dir, program_name):
    label = action_label(action)
    default = default_for_json(action.default, bridge_dir, program_name, label)
    choices = (default_for_json(list(action.choices), bridge_dir, program_name, label)
               if action.choices is not None else None)
    return {
        "option_strings": list(action.option_strings),
        "dest": action.dest,
        "nargs": jsonable(action.nargs),
        "type": getattr(action.type, "__name__", None) if action.type is not None else None,
        "default": default,
        "required": action.required,
        "choices": choices,
        "help": action.help,
    }


def parser_entry(parser, bridge_dir, program_name):
    positionals, options, subcommands = [], [], []
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for name, sub in action.choices.items():
                part = parser_entry(sub, bridge_dir, program_name)
                subcommands.append({
                    "name": name,
                    "description": sub.description,
                    "positionals": part["positionals"],
                    "options": part["options"],
                })
            continue
        (options if action.option_strings else positionals).append(
            action_entry(action, bridge_dir, program_name))
    return {
        "description": parser.description,
        "positionals": positionals,
        "options": options,
        "subcommands": subcommands,
    }


def classify_program(path, name):
    text = open(path, encoding="utf-8").read()
    if has_top_level_build_parser(path):
        return "argparse"
    if "ArgumentParser" in text:
        print("dump-cli: %s uses ArgumentParser but has no top-level build_parser()" % name, file=sys.stderr)
        raise DumpCliError(1)
    return "docstring"


def is_filesystem_root(path):
    path = os.path.abspath(path)
    drive, tail = os.path.splitdrive(path)
    if drive:
        return tail in ("\\", "/") or tail == ""
    return path == os.sep


def forbidden_path_fragments(root):
    repo = os.path.abspath(root)
    fragments = []
    seen = set()
    for path in (repo, os.path.expanduser("~"), os.getcwd()):
        path = os.path.abspath(path)
        if is_filesystem_root(path):
            continue
        for piece in (path, os.path.splitdrive(path)[1]):
            if not piece:
                continue
            canon = path_canonical(piece)
            if canon == "/" or canon in seen:
                continue
            seen.add(canon)
            fragments.append(canon)
    return fragments


def check_string_for_paths(text, program_name, option_label, fragments):
    if not isinstance(text, str):
        return
    ntext = path_canonical(text)
    for frag in fragments:
        if frag and frag in ntext:
            if option_label is not None:
                print("dump-cli: %s: reference text on %s contains a computer path" % (program_name, option_label),
                      file=sys.stderr)
            else:
                print("dump-cli: %s: reference text contains a computer path" % program_name, file=sys.stderr)
            raise DumpCliError(1)


def check_default_strings(value, program_name, option_label, fragments):
    if isinstance(value, (list, tuple)):
        for item in value:
            check_default_strings(item, program_name, option_label, fragments)
    elif isinstance(value, dict):
        for key, item in value.items():
            check_default_strings(key, program_name, option_label, fragments)
            check_default_strings(item, program_name, option_label, fragments)
    elif isinstance(value, str):
        check_string_for_paths(value, program_name, option_label, fragments)


def check_action_strings(action, program_name, fragments):
    label = action_label(action)
    for s in action["option_strings"]:
        check_string_for_paths(s, program_name, label, fragments)
    check_string_for_paths(action["dest"], program_name, label, fragments)
    check_string_for_paths(action.get("type"), program_name, label, fragments)
    check_string_for_paths(action.get("help"), program_name, label, fragments)
    check_default_strings(action["choices"], program_name, label, fragments)
    check_default_strings(action["default"], program_name, label, fragments)


def validate_reference_strings(data, root):
    fragments = forbidden_path_fragments(root)
    for cmd in data["commands"]:
        name = cmd["name"]
        if cmd["source"] == "docstring":
            check_string_for_paths(cmd.get("usage"), name, None, fragments)
            continue
        check_string_for_paths(cmd.get("description"), name, None, fragments)
        for sub in cmd["subcommands"]:
            check_string_for_paths(sub["name"], name, None, fragments)
            check_string_for_paths(sub.get("description"), name, None, fragments)
            for a in sub["positionals"] + sub["options"]:
                check_action_strings(a, name, fragments)
        for a in cmd["positionals"] + cmd["options"]:
            check_action_strings(a, name, fragments)


def command_entry(bridge_dir, name):
    path = os.path.join(bridge_dir, name)
    rel_path = "bridge/cursor-bridge/" + name
    kind = classify_program(path, name)
    base = {"name": name, "path": rel_path, "source": kind}
    if kind == "docstring":
        usage = module_docstring(path)
        if usage is None:
            print("dump-cli: %s: no module docstring" % name, file=sys.stderr)
            raise DumpCliError(1)
        base["usage"] = usage
        return base
    mod = load_bridge_module(path, "cmd")
    parsed = parser_entry(mod.build_parser(), bridge_dir, name)
    base["description"] = parsed["description"]
    base["positionals"] = parsed["positionals"]
    base["options"] = parsed["options"]
    base["subcommands"] = parsed["subcommands"]
    return base


def build_reference(root):
    bridge_dir = os.path.join(root, "bridge", "cursor-bridge")
    previous_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        commands = [command_entry(bridge_dir, name) for name in command_programs(bridge_dir)]
    finally:
        sys.dont_write_bytecode = previous_bytecode
    data = {"commands": commands}
    validate_reference_strings(data, root)
    return data


def reference_json_text(data):
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def append_fenced(lines, text):
    lines.append("```")
    lines.extend(text.splitlines())
    lines.append("```")
    lines.append("")


def render_action_line(action):
    label = "`%s`" % (" ".join(action["option_strings"]) if action["option_strings"] else action["dest"])
    parts = [label, "default: %s" % json.dumps(action["default"]), "required: %s" % json.dumps(action["required"])]
    if action["choices"] is not None:
        parts.append("choices: %s" % json.dumps(action["choices"]))
    if action["help"]:
        parts.append(action["help"])
    return "- " + "; ".join(parts)


def render_actions_section(lines, heading, level, items):
    if not items:
        return
    lines.append("%s %s" % ("#" * level, heading))
    lines.append("")
    for a in items:
        lines.append(render_action_line(a))
    lines.append("")


def render_markdown(data):
    lines = ["# Bridge command reference", ""]
    for cmd in data["commands"]:
        lines.append("## %s" % cmd["name"])
        lines.append("")
        lines.append("Path: `%s`" % cmd["path"])
        lines.append("")
        if cmd["source"] == "docstring":
            append_fenced(lines, cmd["usage"])
            continue
        if cmd.get("description"):
            append_fenced(lines, cmd["description"])
        render_actions_section(lines, "Positionals", 3, cmd["positionals"])
        render_actions_section(lines, "Options", 3, cmd["options"])
        for sub in cmd["subcommands"]:
            lines.append("### Subcommand `%s`" % sub["name"])
            lines.append("")
            if sub.get("description"):
                append_fenced(lines, sub["description"])
            render_actions_section(lines, "Positionals", 4, sub["positionals"])
            render_actions_section(lines, "Options", 4, sub["options"])
    return "\n".join(lines).rstrip() + "\n"


def write_outputs(root, data):
    docs = os.path.join(root, "docs")
    os.makedirs(docs, exist_ok=True)
    json_text = reference_json_text(data)
    md_text = render_markdown(data)
    json_path = os.path.join(docs, "cli-reference.json")
    md_path = os.path.join(docs, "CLI_REFERENCE.md")
    with open(json_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json_text)
    with open(md_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(md_text)
    return json_text, md_text


def normalise(text):
    return text.replace("\r\n", "\n").replace("\r", "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], allow_abbrev=False)
    ap.add_argument("--check", action="store_true", help="compare committed reference files without writing")
    args = ap.parse_args(argv)
    root = repo_root()
    if args.check:
        try:
            data = build_reference(root)
        except DumpCliError as e:
            return e.code
        json_expected = reference_json_text(data)
        md_expected = render_markdown(data)
        failures = []
        for rel, expected in ((JSON_REL, json_expected), (MD_REL, md_expected)):
            path = os.path.join(root, rel)
            if not os.path.isfile(path):
                failures.append(rel)
                continue
            committed = open(path, encoding="utf-8").read()
            if normalise(committed) != normalise(expected):
                failures.append(rel)
        for rel in failures:
            print(rel)
        return 1 if failures else 0
    try:
        data = build_reference(root)
    except DumpCliError as e:
        return e.code
    write_outputs(root, data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
