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
import os
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


def default_for_json(value, bridge_dir, program_name, option_label):
    if isinstance(value, (list, tuple)):
        return [default_for_json(v, bridge_dir, program_name, option_label) for v in value]
    if isinstance(value, str) and os.path.isabs(value):
        try:
            rel = os.path.relpath(value, bridge_dir)
        except ValueError:
            refuse_outside_default(program_name, option_label)
        if rel == os.pardir or rel.startswith(os.pardir + os.sep):
            refuse_outside_default(program_name, option_label)
        return BRIDGE_PLACEHOLDER + rel.replace(os.sep, "/")
    return jsonable(value)


def action_entry(action, bridge_dir, program_name):
    label = action.option_strings[0] if action.option_strings else action.dest
    default = default_for_json(action.default, bridge_dir, program_name, label)
    return {
        "option_strings": list(action.option_strings),
        "dest": action.dest,
        "nargs": jsonable(action.nargs),
        "type": getattr(action.type, "__name__", None) if action.type is not None else None,
        "default": default,
        "required": action.required,
        "choices": jsonable(list(action.choices)) if action.choices is not None else None,
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
    for path in (repo, os.path.expanduser("~"), os.getcwd()):
        path = os.path.abspath(path)
        if is_filesystem_root(path):
            continue
        fragments.append(path)
        if path == repo:
            fragments.append(path.replace(os.sep, "/"))
    return fragments


def check_string_for_paths(text, program_name, option_label, fragments):
    if not isinstance(text, str):
        return
    for frag in fragments:
        if frag and frag in text:
            if option_label is not None:
                print("dump-cli: %s: reference text on %s contains a computer path" % (program_name, option_label),
                      file=sys.stderr)
            else:
                print("dump-cli: %s: reference text contains a computer path" % program_name, file=sys.stderr)
            raise DumpCliError(1)


def validate_reference_strings(data, root):
    fragments = forbidden_path_fragments(root)
    for cmd in data["commands"]:
        name = cmd["name"]
        if cmd["source"] == "docstring":
            check_string_for_paths(cmd.get("usage"), name, None, fragments)
            continue
        check_string_for_paths(cmd.get("description"), name, None, fragments)
        for sub in cmd["subcommands"]:
            check_string_for_paths(sub.get("description"), name, None, fragments)
            for a in sub["positionals"] + sub["options"]:
                label = a["option_strings"][0] if a["option_strings"] else a["dest"]
                check_string_for_paths(a.get("help"), name, label, fragments)
                if a["choices"] is not None:
                    for choice in a["choices"]:
                        check_string_for_paths(choice, name, label, fragments)
                check_string_for_paths(json.dumps(a["default"]), name, label, fragments)
        for a in cmd["positionals"] + cmd["options"]:
            label = a["option_strings"][0] if a["option_strings"] else a["dest"]
            check_string_for_paths(a.get("help"), name, label, fragments)
            if a["choices"] is not None:
                for choice in a["choices"]:
                    check_string_for_paths(choice, name, label, fragments)
            check_string_for_paths(json.dumps(a["default"]), name, label, fragments)


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
    return " ".join(parts)


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
        for section, items in (("Positionals", cmd["positionals"]), ("Options", cmd["options"])):
            if not items:
                continue
            lines.append("### %s" % section)
            lines.append("")
            for a in items:
                lines.append(render_action_line(a))
            lines.append("")
        for sub in cmd["subcommands"]:
            lines.append("### Subcommand `%s`" % sub["name"])
            lines.append("")
            if sub.get("description"):
                append_fenced(lines, sub["description"])
            for section, items in (("Positionals", sub["positionals"]), ("Options", sub["options"])):
                if not items:
                    continue
                lines.append("#### %s" % section)
                lines.append("")
                for a in items:
                    lines.append(render_action_line(a))
                lines.append("")
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
