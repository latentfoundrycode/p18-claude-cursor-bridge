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


def default_for_json(value, bridge_dir, program_name, option_label):
    if isinstance(value, str) and os.path.isabs(value):
        rel = os.path.relpath(value, bridge_dir)
        if rel.startswith(".."):
            print("dump-cli: %s: absolute default on %s is outside the bridge folder" % (program_name, option_label),
                  file=sys.stderr)
            raise DumpCliError(1)
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


class DumpCliError(Exception):
    def __init__(self, code=1):
        self.code = code


def classify_program(path, name):
    text = open(path, encoding="utf-8").read()
    if has_top_level_build_parser(path):
        return "argparse"
    if "ArgumentParser" in text:
        print("dump-cli: %s uses ArgumentParser but has no top-level build_parser()" % name, file=sys.stderr)
        raise DumpCliError(1)
    return "docstring"


def command_entry(bridge_dir, name):
    path = os.path.join(bridge_dir, name)
    rel_path = "bridge/cursor-bridge/" + name
    kind = classify_program(path, name)
    base = {"name": name, "path": rel_path, "source": kind}
    if kind == "docstring":
        base["usage"] = module_docstring(path)
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
    commands = [command_entry(bridge_dir, name) for name in command_programs(bridge_dir)]
    return {"commands": commands}


def render_markdown(data):
    lines = ["# Bridge command reference", ""]
    for cmd in data["commands"]:
        lines.append("## %s" % cmd["name"])
        lines.append("")
        lines.append("Path: `%s`" % cmd["path"])
        lines.append("")
        if cmd["source"] == "docstring":
            lines.append("```")
            lines.extend(cmd["usage"].splitlines())
            lines.append("```")
            lines.append("")
            continue
        if cmd.get("description"):
            lines.append(cmd["description"])
            lines.append("")
        for section, items in (("Positionals", cmd["positionals"]), ("Options", cmd["options"])):
            if not items:
                continue
            lines.append("### %s" % section)
            lines.append("")
            for a in items:
                opts = " ".join(a["option_strings"]) if a["option_strings"] else a["dest"]
                parts = ["- `%s`" % opts]
                if a["default"] is not None:
                    parts.append("default: `%s`" % json.dumps(a["default"]))
                parts.append("required: %s" % json.dumps(a["required"]))
                if a["choices"] is not None:
                    parts.append("choices: %s" % json.dumps(a["choices"]))
                if a["help"]:
                    parts.append(a["help"])
                lines.append("  - " + "; ".join(parts))
            lines.append("")
        for sub in cmd["subcommands"]:
            lines.append("### Subcommand `%s`" % sub["name"])
            lines.append("")
            if sub.get("description"):
                lines.append(sub["description"])
                lines.append("")
            for section, items in (("Positionals", sub["positionals"]), ("Options", sub["options"])):
                if not items:
                    continue
                lines.append("#### %s" % section)
                lines.append("")
                for a in items:
                    opts = " ".join(a["option_strings"]) if a["option_strings"] else a["dest"]
                    parts = ["- `%s`" % opts]
                    if a["default"] is not None:
                        parts.append("default: `%s`" % json.dumps(a["default"]))
                    parts.append("required: %s" % json.dumps(a["required"]))
                    if a["choices"] is not None:
                        parts.append("choices: %s" % json.dumps(a["choices"]))
                    if a["help"]:
                        parts.append(a["help"])
                    lines.append("  - " + "; ".join(parts))
                lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_outputs(root, data):
    docs = os.path.join(root, "docs")
    os.makedirs(docs, exist_ok=True)
    json_text = json.dumps(data, indent=2, sort_keys=True) + "\n"
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
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="compare committed reference files without writing")
    args, extras = ap.parse_known_args(argv)
    if extras:
        ap.print_usage(file=sys.stderr)
        return 2
    root = repo_root()
    if args.check:
        try:
            data = build_reference(root)
        except DumpCliError as e:
            return e.code
        json_expected = json.dumps(data, indent=2, sort_keys=True) + "\n"
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
