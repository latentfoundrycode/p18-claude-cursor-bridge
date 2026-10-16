#!/usr/bin/env python3
"""workflow-check: keep conditional workflows honest against the open list and the extension-point registry (R-014, R-033).

  python workflow-check.py [--open-list FILE] [--registry FILE] [--status FILE]... [ROOT ...]

One program, run at three times: at intake (the project's status file), at every bridge release
(CI, over the bridge's workflow folder and the sample fixtures) and at every calibration (the
installed workflow folder and the project's status file).

ROOT is zero or more workflow folders. Files under ROOT/types/ and ROOT/traits/ are the
conditional workflows; nothing else in a root is read. With no ROOT and no --status, the root
is the workflow folder beside this program. With --status and no ROOT, only the status files
are checked. --open-list defaults to workflow/open-list.md beside this program, and --registry
to workflow/extension-points.md beside this program. --status FILE may be repeated. The same
two tables are used for every root and every status file of one run.

Finding lines, then one RESULT line:
  FAIL (a)        an Add at or Set at names a point key that is not a Key of the registry
  FAIL (b)        a trait file contains a Set at or a Replace heading
  FAIL (c)        a Replace names a module that is missing or whose Replaceable is not yes
  FAIL (d)        a sub-workflow's type folder, type file, or sub-type does not match
  FAIL (e)        a Workflows line's product type, sub-type, or part name is wrong
  FAIL (f)        a Workflows line names a product type or sub-type whose Written is not yes
  FAIL (set)      a Set at names a point whose Changes cell does not contain set
  FAIL (kind)     a delivery-kind heading or intake.delivery-kind value is missing or unlisted
  FAIL (unknown)  a file key or a Workflows name is not in the open list
  FAIL (form)     a file, a change heading, or a Workflows line has the wrong shape
  FLAG (trait)    a trait on a Workflows line is not yet written; flagged, work continues (non-fatal)

Exit 0 when no FAIL line was printed (FLAG lines may have been printed). Exit 1 when at least
one FAIL line was printed. Exit 2 when the check cannot run: a ROOT that is not a folder, an
open list, registry, or status file that does not exist or cannot be read as UTF-8, a required
heading or required column missing, or a table row whose cell count differs from its header.
On exit 2 the program prints ERROR lines and RESULT: not checked, and no traceback.
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OPEN = os.path.join(HERE, "workflow", "open-list.md")
DEFAULT_REGISTRY = os.path.join(HERE, "workflow", "extension-points.md")
DEFAULT_ROOT = os.path.join(HERE, "workflow")

# Requirement 9 names these two points and this list. Every other key is read from the tables.
DELIVERY_KINDS = (
    "installer",
    "install-script",
    "package",
    "web-deployment",
    "store-package",
    "host-installation",
)
DELIVERY_POINT = "project-end.delivery"
DELIVERY_SET = "intake.delivery-kind"
DELIVERY_KIND_SET = set(DELIVERY_KINDS)

ADD_FOR = re.compile(r"^## Add at (\S+) for (\S+)$")
ADD_AT = re.compile(r"^## Add at (\S+)$")
SET_AT = re.compile(r"^## Set at (\S+)$")
REPLACE = re.compile(r"^## Replace (\S+)$")
CHANGE_WORDS = ("Add", "Set", "Replace")
TRAITS_MARK = "; traits: "


def slash(path):
    return path.replace("\\", "/")


def joined(root, rel):
    return slash(root).rstrip("/") + "/" + rel


def read_utf8(path):
    """Return (text, None) or (None, reason). Reason is plain language, never a traceback."""
    shown = slash(path)
    if not os.path.isfile(path):
        if os.path.exists(path):
            return None, shown, "cannot be read"
        return None, shown, "does not exist"
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read(), shown, None
    except UnicodeDecodeError:
        return None, shown, "cannot be read as UTF-8"
    except OSError as err:
        return None, shown, "cannot be read (%s)" % (err.strerror or err)


def cells_of(line):
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def parse_table(text, path, heading, required):
    """The first Markdown table after heading. Returns (rows, error reason or None)."""
    lines = text.splitlines()
    start_heading = None
    for index, line in enumerate(lines):
        if line == heading:
            start_heading = index
            break
    if start_heading is None:
        return None, "missing heading %s" % heading
    start = None
    for index in range(start_heading + 1, len(lines)):
        if lines[index].startswith("|"):
            start = index
            break
        if lines[index].startswith("## "):
            break
    if start is None:
        return None, "no table after %s" % heading
    table = []
    for line in lines[start:]:
        if not line.startswith("|"):
            break
        table.append(line)
    if len(table) < 2:
        return None, "table after %s has no separator row" % heading
    header = cells_of(table[0])
    for column in required:
        if column not in header:
            return None, "missing column %s" % column
    body = []
    for line in table[1:]:
        row = cells_of(line)
        if len(row) != len(header):
            return None, "table row cell count differs from its header"
        body.append(dict(zip(header, row)))
    # The second table line is the separator, not a record.
    return body[1:], None


def index_first(rows, column):
    found = {}
    for row in rows:
        found.setdefault(row[column], row)
    return found


def load_tables(open_text, open_path, reg_text, reg_path):
    """Return (tables, errors). errors are (path, reason)."""
    errors = []
    specs = (
        (open_text, open_path, "## Product types", ("Key", "Name", "Workflow name", "Written")),
        (open_text, open_path, "## Sub-types", ("Key", "Of type", "Sub-workflow name", "Written")),
        (open_text, open_path, "## Traits", ("Key", "Name", "Written")),
        (reg_text, reg_path, "## Phase modules", ("Module", "Replaceable")),
        (reg_text, reg_path, "## Extension points", ("Key", "Changes")),
    )
    parsed = []
    for text, path, heading, required in specs:
        rows, reason = parse_table(text, path, heading, required)
        if reason is not None:
            errors.append((slash(path), reason))
            parsed.append(None)
        else:
            parsed.append(rows)
    if errors:
        return None, errors
    products, subs, traits, modules, points = parsed
    tables = {
        "product_by_key": index_first(products, "Key"),
        "sub_by_key": index_first(subs, "Key"),
        "trait_keys": set(index_first(traits, "Key")),
        "workflow_by_name": index_first(products, "Workflow name"),
        "sub_by_name": index_first(subs, "Sub-workflow name"),
        "trait_by_name": index_first(traits, "Name"),
        "trait_order": {},
        "module_replaceable": index_first(modules, "Module"),
        "point_changes": index_first(points, "Key"),
    }
    order = tables["trait_order"]
    for index, row in enumerate(traits):
        order.setdefault(row["Name"], index)
    return tables, []


def allows_set(cell):
    return "set" in [part.strip() for part in cell.split(",")]


def collect(root, product_keys):
    """Files and the folders Requirement 6 reports, in sorted relative-path order."""
    found = []
    for layer in ("types", "traits"):
        base = os.path.join(root, layer)
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            rel_dir = os.path.relpath(dirpath, root).replace("\\", "/")
            for name in dirnames:
                found.append((rel_dir + "/" + name, True))
            for name in filenames:
                found.append((rel_dir + "/" + name, False))
    unknown_types = set()
    for rel, is_dir in found:
        parts = rel.split("/")
        if is_dir and len(parts) == 2 and parts[0] == "types" and parts[1] not in product_keys:
            unknown_types.add(parts[1])
    items = []
    for rel, is_dir in found:
        parts = rel.split("/")
        if parts[0] == "types" and len(parts) >= 2 and parts[1] in unknown_types:
            if is_dir and len(parts) == 2:
                items.append({"rel": rel, "action": "d-folder", "name": parts[1]})
            continue
        if is_dir:
            if (parts[0] == "traits" and len(parts) >= 2) or (parts[0] == "types" and len(parts) > 2):
                items.append({"rel": rel, "action": "form-path", "name": parts[-1]})
            continue
        if len(parts) == 2 and parts[0] == "types" and parts[1].endswith(".md"):
            items.append({"rel": rel, "action": "type", "key": parts[1][:-3]})
        elif len(parts) == 3 and parts[0] == "types" and parts[2].endswith(".md"):
            items.append({"rel": rel, "action": "sub", "key": parts[2][:-3], "type_key": parts[1]})
        elif len(parts) == 2 and parts[0] == "traits" and parts[1].endswith(".md"):
            items.append({"rel": rel, "action": "trait", "key": parts[1][:-3]})
        else:
            items.append({"rel": rel, "action": "form-path", "name": parts[-1]})
    items.sort(key=lambda item: item["rel"])
    return items


def change_word(line):
    if not line.startswith("## "):
        return None
    words = line[3:].split()
    if not words or words[0] not in CHANGE_WORDS:
        return None
    return words[0]


def parse_heading(line):
    """Return (kind, target, for_kind) or None when the shape is not one of the four forms."""
    match = ADD_FOR.match(line)
    if match:
        return "add", match.group(1), match.group(2)
    match = ADD_AT.match(line)
    if match:
        return "add", match.group(1), None
    match = SET_AT.match(line)
    if match:
        return "set", match.group(1), None
    match = REPLACE.match(line)
    if match:
        return "replace", match.group(1), None
    return None


def heading_spans(text):
    """Change headings outside fences, each with the raw lines of its section."""
    lines = text.splitlines()
    fence = False
    marks = []
    for index, line in enumerate(lines):
        if line.startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        if line.startswith("## "):
            marks.append(index)
    spans = []
    for index in marks:
        line = lines[index]
        if change_word(line) is None:
            continue
        end = len(lines)
        for later in marks:
            if later > index:
                end = later
                break
        spans.append((line, lines[index + 1:end]))
    return spans


def first_nonblank(body):
    for line in body:
        if line.strip():
            return line
    return None


def normalize_kind(line):
    text = line.strip()
    if len(text) >= 2 and text.startswith("`") and text.endswith("`"):
        text = text[1:-1]
    return text


def check_changes(text, layer, tables):
    """Findings (code, name, reason) for one conditional-workflow file."""
    findings = []
    seen_set = set()
    seen_replace = set()
    points = tables["point_changes"]
    modules = tables["module_replaceable"]
    for line, body in heading_spans(text):
        parsed = parse_heading(line)
        if parsed is None:
            findings.append(("form", "-", "change heading is not one of the four forms"))
            continue
        kind, target, for_kind = parsed
        if kind == "set":
            if target in seen_set:
                findings.append(("form", target, "two Set at headings for the same point"))
            seen_set.add(target)
            if first_nonblank(body) is None:
                findings.append(("form", target, "Set at section has no non-blank line"))
        elif kind == "replace":
            if target in seen_replace:
                findings.append(("form", target, "two Replace headings for the same module"))
            seen_replace.add(target)
        if layer == "trait" and kind in ("set", "replace"):
            findings.append(("b", target, "a trait file may only add"))
        if kind in ("add", "set"):
            point = points.get(target)
            if point is None:
                findings.append(("a", target, "point is not in the extension-point registry"))
            elif kind == "set" and not allows_set(point["Changes"]):
                findings.append(("set", target, "point does not accept set"))
            if kind == "add" and target == DELIVERY_POINT:
                if for_kind is None:
                    findings.append(("kind", target, "addition at project-end.delivery does not name a delivery kind"))
                elif for_kind not in DELIVERY_KIND_SET:
                    findings.append(("kind", for_kind, "delivery kind is not in the delivery-kind list"))
            elif kind == "add" and for_kind is not None:
                if for_kind not in DELIVERY_KIND_SET:
                    findings.append(("kind", for_kind, "delivery kind is not in the delivery-kind list"))
                findings.append(("kind", for_kind, "delivery kind is named on a point other than project-end.delivery"))
            elif kind == "set" and target == DELIVERY_SET:
                first = first_nonblank(body)
                value = "-" if first is None else normalize_kind(first)
                if value not in DELIVERY_KIND_SET:
                    findings.append(("kind", value or "-", "Set at intake.delivery-kind is not one delivery kind"))
        elif kind == "replace":
            module = modules.get(target)
            if module is None or module["Replaceable"] != "yes":
                findings.append(("c", target, "module is missing or not replaceable"))
    return findings


def check_sub_identity(root, type_key, sub_key, tables):
    findings = []
    if type_key not in tables["product_by_key"]:
        findings.append(("d", sub_key, "type key is not a product type"))
    type_file = os.path.join(root, "types", type_key + ".md")
    if not os.path.isfile(type_file):
        findings.append(("d", sub_key, "type workflow types/%s.md does not exist" % type_key))
    sub = tables["sub_by_key"].get(sub_key)
    if sub is None or sub["Of type"] != type_key:
        findings.append(("d", sub_key, "not a sub-type of %s" % type_key))
    return findings


def check_item(root, item, tables):
    action = item["action"]
    path = joined(root, item["rel"])
    if action == "d-folder":
        return [("d", path, item["name"], "type folder is not a product type")]
    if action == "form-path":
        return [("form", path, item["name"], "path is not a conditional-workflow file")]
    findings = []
    if action == "type" and item["key"] not in tables["product_by_key"]:
        findings.append(("unknown", path, item["key"], "not a product type key"))
    elif action == "trait" and item["key"] not in tables["trait_keys"]:
        findings.append(("unknown", path, item["key"], "not a trait key"))
    elif action == "sub":
        for code, name, reason in check_sub_identity(root, item["type_key"], item["key"], tables):
            findings.append((code, path, name, reason))
    for code, name, reason in check_changes(item["text"], action, tables):
        findings.append((code, path, name, reason))
    return findings


def split_part(rest):
    """Return (part, body) when rest begins with a part prefix, else (None, rest)."""
    index = rest.find(": ")
    if index <= 0:
        return None, rest
    part = rest[:index]
    if not part or part != part.strip() or ";" in part or "→" in part or ":" in part:
        return None, rest
    return part, rest[index + 2:]


def check_head(head, path, tables, findings):
    segments = [segment.strip() for segment in head.split("→")]
    names_by_seg = [[name.strip() for name in segment.split(",")] for segment in segments]
    types_found = []
    subs_found = []
    traits_in_head = []
    for names in names_by_seg:
        for name in names:
            if name in tables["workflow_by_name"]:
                types_found.append(tables["workflow_by_name"][name])
            elif name in tables["sub_by_name"]:
                subs_found.append(tables["sub_by_name"][name])
            elif name in tables["trait_by_name"]:
                traits_in_head.append(name)
            else:
                findings.append(("unknown", path, name or "-", "name is not in the open list"))
    if len(types_found) != 1:
        findings.append(("e", path, "-", "part must name exactly one product type"))
    if len(subs_found) > 1:
        findings.append(("e", path, "-", "part must name at most one sub-type"))
    of_ok = True
    if len(types_found) == 1 and len(subs_found) == 1:
        if subs_found[0]["Of type"] != types_found[0]["Key"]:
            of_ok = False
            findings.append(("e", path, subs_found[0]["Sub-workflow name"], "sub-type is not of the line's product type"))
    counts_right = len(types_found) == 1 and len(subs_found) <= 1 and of_ok
    if not counts_right:
        return
    if len(subs_found) == 0:
        shape_ok = names_by_seg == [[types_found[0]["Workflow name"]]] and not traits_in_head
    else:
        shape_ok = (
            names_by_seg == [[types_found[0]["Workflow name"]], [subs_found[0]["Sub-workflow name"]]]
            and not traits_in_head
        )
    if not shape_ok:
        findings.append(("form", path, "-", "Workflows head is not the product type, then at most its sub-type"))
    if types_found[0]["Written"] != "yes":
        findings.append(("f", path, types_found[0]["Workflow name"], "product type is not written"))
    if subs_found and subs_found[0]["Written"] != "yes":
        findings.append(("f", path, subs_found[0]["Sub-workflow name"], "sub-type is not written"))


def check_traits(text, path, tables, findings):
    if text.strip() == "none":
        return
    if text.strip() == "":
        findings.append(("form", path, "-", "traits list is empty"))
        return
    last = None
    seen = set()
    for name in [part.strip() for part in text.split(",")]:
        trait = tables["trait_by_name"].get(name)
        if not name or trait is None:
            findings.append(("unknown", path, name or "-", "not a trait name"))
            continue
        if name in seen:
            findings.append(("form", path, name, "trait repeated"))
        else:
            index = tables["trait_order"][name]
            if last is not None and index < last:
                findings.append(("form", path, name, "traits are not in the open list's order"))
            if last is None or index > last:
                last = index
            seen.add(name)
        if trait["Written"] != "yes":
            findings.append((
                "FLAG", path, name,
                "trait not yet written; flagged, work continues (non-fatal)",
            ))


def check_status(path, text, tables):
    shown = slash(path)
    lines = [line for line in text.splitlines() if line.startswith("Workflows: ")]
    if not lines:
        return [("form", shown, "-", "status file has no Workflows line")]
    multi = len(lines) > 1
    findings = []
    seen_parts = {}
    for line in lines:
        rest = line[len("Workflows: "):]
        part, body = split_part(rest)
        if multi:
            if part is None:
                findings.append(("form", shown, "-", "a Workflows line in a multi-part file has no part prefix"))
                continue
            seen_parts[part] = seen_parts.get(part, 0) + 1
            if seen_parts[part] == 2:
                findings.append(("e", shown, part, "two Workflows lines name the same part"))
        elif part is not None:
            findings.append(("form", shown, part, "the only Workflows line must not carry a part prefix"))
            continue
        else:
            body = rest
        if body == "not yet classified":
            continue
        if body.count(TRAITS_MARK) != 1:
            findings.append(("form", shown, "-", "Workflows line must contain '; traits: ' exactly once"))
            continue
        head, traits = body.split(TRAITS_MARK, 1)
        check_head(head, shown, tables, findings)
        check_traits(traits, shown, tables, findings)
    return findings


def print_findings(findings):
    problems = 0
    for code, path, name, reason in findings:
        if code == "FLAG":
            print("FLAG (trait) %s: %s - %s" % (path, name, reason))
        else:
            print("FAIL (%s) %s: %s - %s" % (code, path, name, reason))
            problems += 1
    if problems == 0:
        print("RESULT: OK")
        return 0
    print("RESULT: %d problem(s)" % problems)
    return 1


def build_parser():
    parser = argparse.ArgumentParser(
        prog="workflow-check.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--open-list", default=DEFAULT_OPEN, metavar="FILE")
    parser.add_argument("--registry", default=DEFAULT_REGISTRY, metavar="FILE")
    parser.add_argument("--status", action="append", default=[], metavar="FILE")
    parser.add_argument("roots", nargs="*", metavar="ROOT")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    errors = []
    open_text, open_shown, open_err = read_utf8(args.open_list)
    if open_err:
        errors.append((open_shown, open_err))
    reg_text, reg_shown, reg_err = read_utf8(args.registry)
    if reg_err:
        errors.append((reg_shown, reg_err))
    roots = list(args.roots)
    statuses = list(args.status)
    if not roots and not statuses:
        roots = [DEFAULT_ROOT]
    tables = None
    if open_text is not None and reg_text is not None:
        tables, parse_errors = load_tables(open_text, args.open_list, reg_text, args.registry)
        errors.extend(parse_errors)
    root_items = []
    for root in roots:
        if not os.path.isdir(root):
            errors.append((slash(root), "not a folder"))
            continue
        if tables is None:
            continue
        items = collect(root, set(tables["product_by_key"]))
        for item in items:
            if item["action"] in ("d-folder", "form-path"):
                continue
            full = os.path.join(root, *item["rel"].split("/"))
            text, shown, err = read_utf8(full)
            if err:
                errors.append((joined(root, item["rel"]), err))
            else:
                item["text"] = text
        root_items.append((root, items))
    status_texts = []
    for status in statuses:
        text, shown, err = read_utf8(status)
        if err:
            errors.append((shown, err))
        else:
            status_texts.append((status, text))
    if errors:
        for path, reason in errors:
            print("ERROR: %s: %s" % (path, reason))
        print("RESULT: not checked")
        return 2
    findings = []
    for root, items in root_items:
        for item in items:
            findings.extend(check_item(root, item, tables))
    for status, text in status_texts:
        findings.extend(check_status(status, text, tables))
    return print_findings(findings)


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="backslashreplace")
    sys.exit(main())
