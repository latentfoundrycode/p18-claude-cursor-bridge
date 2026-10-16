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
one FAIL line was printed. Exit 2 when the check cannot run: a ROOT that is not a folder, a
folder under a root that cannot be listed, a types/ or traits/ path that cannot be examined,
an open list, registry, or status file that does not
exist or cannot be read as UTF-8, a required heading or required column missing, a table with
no separator row, or a table row whose cell count differs from its header. On exit 2 the
program prints ERROR lines and RESULT: not checked, and no traceback. A command-line usage
error also exits 2; the usage line argparse prints stays as it is, argparse's message is
escaped the same way as a printed field, and the last line on standard output is
RESULT: not checked.
"""
import argparse
import os
import re
import stat
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
# A change heading's first word, compared case-insensitively after trailing punctuation is
# stripped (R2-1, R3-4). "at" as the second word is the other way in.
CHANGE_FIRST = frozenset({
    "add", "adds", "added", "adding",
    "set", "sets", "setting",
    "replace", "replaces", "replaced", "replacing",
})
TRAILING_PUNCT = ":;,.-"
# Up to three leading spaces, two hashes, then a space or a tab (R3-6).
HEADING_CANDIDATE = re.compile(r"^ {0,3}##[ \t](.*)$")
# An opening fence: zero to three spaces, then a run of at least three backticks or
# tildes, then the info string (R5-3). A closing fence is matched separately, because
# its run must be at least as long as the opening run and the rest of the line is blank.
FENCE_OPEN = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
FENCE_CLOSE = re.compile(r"^ {0,3}(`{3,}|~{3,})[ \t]*$")
TRAITS_MARK = "; traits: "


def slash(path):
    return path.replace("\\", "/")


def joined(root, rel):
    return slash(root).rstrip("/") + "/" + rel


def file_lines(text):
    """Split file text only at a line feed (R6-2).

    `read_utf8` uses universal newlines, so a carriage return is already a line feed.
    A form feed, vertical tab, file/group/record separator, NEL, U+2028, or U+2029
    stays inside the line. A final line feed does not add an empty line.
    """
    lines = text.split("\n")
    if lines and lines[-1] == "":
        del lines[-1]
    return lines


def read_utf8(path):
    """Return three values (text, shown path, reason).

    text is the file contents and reason is None when the read succeeded. text is None and
    reason is plain language when it did not. A leading UTF-8 byte-order mark is dropped.
    Never a traceback.
    """
    shown = slash(path)
    if not os.path.isfile(path):
        if os.path.exists(path):
            return None, shown, "cannot be read"
        return None, shown, "does not exist"
    try:
        with open(path, encoding="utf-8-sig") as handle:
            return handle.read(), shown, None
    except UnicodeDecodeError:
        return None, shown, "cannot be read as UTF-8"
    except OSError as err:
        return None, shown, "cannot be read (%s)" % (err.strerror or err)


def escape_field(value):
    """Printable characters stay; every other character becomes \\xNN, \\uNNNN, or \\UNNNNNNNN."""
    text = "" if value is None else str(value)
    parts = []
    for char in text:
        if char.isprintable():
            parts.append(char)
            continue
        code = ord(char)
        if code < 256:
            parts.append("\\x%02x" % code)
        elif code <= 0xFFFF:
            parts.append("\\u%04x" % code)
        else:
            parts.append("\\U%08x" % code)
    return "".join(parts)


def is_link(path):
    """A symbolic link, or on Windows a junction or any other reparse point.

    One os.lstat on every Python (R5-2). FileNotFoundError and NotADirectoryError are not a
    link. Any other OSError is a link, so a path the check cannot classify is not walked.
    Otherwise the path is a link when stat.S_ISLNK(st_mode) is true, or, on Windows, when
    st_file_attributes includes stat.FILE_ATTRIBUTE_REPARSE_POINT.
    """
    try:
        st = os.lstat(path)
    except (FileNotFoundError, NotADirectoryError):
        return False
    except OSError:
        return True
    if stat.S_ISLNK(st.st_mode):
        return True
    if os.name == "nt" and st.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
        return True
    return False


def is_separator_cell(cell):
    """Dashes, with an optional colon at either end, and at least one dash."""
    text = cell.strip()
    if text.startswith(":"):
        text = text[1:]
    if text.endswith(":"):
        text = text[:-1]
    return bool(text) and set(text) == {"-"}


def is_separator_row(line, width):
    """The separator has exactly the header's cell count, and every cell is dashes."""
    cells = cells_of(line)
    return len(cells) == width and bool(cells) and all(is_separator_cell(cell) for cell in cells)


def cells_of(line):
    """Strip the line, drop one leading `|` and one trailing `|`, then split on `|`.

    A row such as `| a | b ||` keeps the empty last cell, and `|| a | b |` keeps the
    empty first cell (R6-1). The same rule applies to the header and the separator.
    """
    text = line.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|"):
        text = text[:-1]
    return [cell.strip() for cell in text.split("|")]


def parse_table(text, path, heading, required):
    """The first Markdown table after heading. Returns (rows, error reason or None)."""
    lines = file_lines(text)
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
    if not is_separator_row(table[1], len(header)):
        return None, "table after %s has no separator row" % heading
    for column in required:
        if column not in header:
            return None, "missing column %s" % column
    body = []
    for line in table[2:]:
        row = cells_of(line)
        if len(row) != len(header):
            return None, "table row cell count differs from its header"
        body.append(dict(zip(header, row)))
    return body, None


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
    """Files and the folders Requirement 6 reports, plus links and listing errors.

    Returns (items, errors). A symbolic link or junction is recorded and not opened or
    entered. errors are (path, reason) for a layer path that cannot be examined or a folder
    that cannot be listed.
    """
    found = []
    errors = []

    def onerror(err):
        filename = getattr(err, "filename", None) or root
        reason = getattr(err, "strerror", None) or "cannot be listed"
        errors.append((slash(str(filename)), reason))

    for layer in ("types", "traits"):
        base = os.path.join(root, layer)
        # Nothing at this path: do not walk it and do not report it. lstat succeeds for a
        # dangling link or junction, so those still reach the link test (R5-1, R3-3).
        try:
            os.lstat(base)
        except (FileNotFoundError, NotADirectoryError):
            continue
        except OSError as err:
            errors.append((slash(base), err.strerror or "cannot be examined"))
            continue
        # Test the link before testing whether the path is a folder, so a dangling link
        # is reported and never walked.
        if is_link(base):
            found.append((layer, "link"))
            continue
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base, followlinks=False, onerror=onerror):
            rel_dir = os.path.relpath(dirpath, root).replace("\\", "/")
            kept = []
            for name in dirnames:
                rel = rel_dir + "/" + name
                if is_link(os.path.join(dirpath, name)):
                    found.append((rel, "link"))
                else:
                    found.append((rel, "dir"))
                    kept.append(name)
            dirnames[:] = kept
            for name in filenames:
                rel = rel_dir + "/" + name
                if is_link(os.path.join(dirpath, name)):
                    found.append((rel, "link"))
                else:
                    found.append((rel, "file"))
    unknown_types = set()
    for rel, kind in found:
        parts = rel.split("/")
        if kind == "dir" and len(parts) == 2 and parts[0] == "types" and parts[1] not in product_keys:
            unknown_types.add(parts[1])
    items = []
    for rel, kind in found:
        parts = rel.split("/")
        if parts[0] == "types" and len(parts) >= 2 and parts[1] in unknown_types:
            if kind == "link":
                items.append({"rel": rel, "action": "form-path", "name": parts[-1]})
            elif kind == "dir" and len(parts) == 2:
                items.append({"rel": rel, "action": "d-folder", "name": parts[1]})
            continue
        if kind == "link":
            items.append({"rel": rel, "action": "form-path", "name": parts[-1]})
            continue
        if kind == "dir":
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
    return items, errors


def is_change_heading(line):
    """True when the line is a change heading, including a misspelt or punctuated one.

    A heading candidate has up to three leading spaces, then ## and a space or tab (R3-6).
    Trailing punctuation in `:;,.-` is stripped from the first word before it is compared
    with the change words (R3-4).
    """
    match = HEADING_CANDIDATE.match(line)
    if match is None:
        return False
    words = match.group(1).split()
    if not words:
        return False
    first = words[0]
    while first and first[-1] in TRAILING_PUNCT:
        first = first[:-1]
    if first.casefold() in CHANGE_FIRST:
        return True
    return len(words) >= 2 and words[1].casefold() == "at"


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


def opening_fence(line):
    """Return (marker, length) for an opening fence, or None.

    Zero to three spaces, then at least three backticks or at least three tildes, then the
    info string. A backtick run whose info string contains a backtick is not a fence (R5-3).
    """
    match = FENCE_OPEN.match(line)
    if match is None:
        return None
    marker, info = match.group(1), match.group(2)
    if marker[0] == "`" and "`" in info:
        return None
    return marker[0], len(marker)


def closing_fence(line, char, length):
    """True when the line closes a fence opened with char for length characters.

    Zero to three spaces, then a run of that character at least as long as the opening run,
    then only spaces or tabs (R5-3). A shorter run, the other character, or text after the
    run is content.
    """
    match = FENCE_CLOSE.match(line)
    if match is None:
        return False
    marker = match.group(1)
    return marker[0] == char and len(marker) >= length


def heading_spans(text):
    """Change headings outside fences, each with the raw lines of its section.

    A heading candidate matches ^ {0,3}##[ \\t]. Fences are read as CommonMark reads them
    (R5-3): the closing run is the opening character and at least as long, with nothing
    after it but spaces or tabs. Each section ends at the next candidate's index, so the
    walk is linear in the file. The second value is True when a fence is still open at the
    end of the file (R3-6).
    """
    lines = file_lines(text)
    fence = None
    marks = []
    for index, line in enumerate(lines):
        if fence is None:
            opened = opening_fence(line)
            if opened is not None:
                fence = opened
                continue
        elif closing_fence(line, fence[0], fence[1]):
            fence = None
            continue
        else:
            continue
        if HEADING_CANDIDATE.match(line):
            marks.append(index)
    spans = []
    last = len(marks) - 1
    total = len(lines)
    for position, index in enumerate(marks):
        line = lines[index]
        if not is_change_heading(line):
            continue
        end = marks[position + 1] if position < last else total
        spans.append((line, lines[index + 1:end]))
    return spans, fence is not None


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
    spans, unclosed = heading_spans(text)
    if unclosed:
        findings.append(("form", "-", "fenced code block is still open at the end of the file"))
    for line, body in spans:
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


def prefix_of(rest, multi):
    """Return (part or None, body, bad).

    bad is the part text (or '-') when the prefix rule fails and the line stops there.
    The prefix is looked for only in the head, the text before the first traits marker.
    """
    mark_at = rest.find(TRAITS_MARK)
    if mark_at == -1:
        head = rest
        tail = ""
    else:
        head = rest[:mark_at]
        tail = rest[mark_at:]
    if ": " not in head:
        if multi:
            return None, None, "-"
        return None, rest, None
    cut = head.find(": ")
    part = head[:cut]
    invalid = part == "" or part != part.strip() or ";" in part or "→" in part or ":" in part
    if (not multi) or invalid:
        return None, None, part or "-"
    return part, head[cut + 2:] + tail, None


def check_head(head, path, tables, findings):
    segments = [segment.strip() for segment in head.split("→")]
    names_by_seg = [[name.strip() for name in segment.split(",")] for segment in segments]
    types_found = []
    subs_found = []
    traits_in_head = []
    for names in names_by_seg:
        for name in names:
            if name == "":
                findings.append(("form", path, "-", "empty name in the Workflows head"))
                continue
            if name in tables["workflow_by_name"]:
                types_found.append(tables["workflow_by_name"][name])
            elif name in tables["sub_by_name"]:
                subs_found.append(tables["sub_by_name"][name])
            elif name in tables["trait_by_name"]:
                traits_in_head.append(name)
            else:
                findings.append(("unknown", path, name, "name is not in the open list"))
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
    """Traits text is `none` or names joined by exactly `, `. It is not stripped."""
    if text == "none":
        return
    last = None
    seen = set()
    for name in text.split(", "):
        if name == "" or name != name.strip() or "," in name:
            findings.append(("form", path, name or "-", "traits are not joined by a comma and one space"))
            continue
        trait = tables["trait_by_name"].get(name)
        if trait is None:
            findings.append(("unknown", path, name, "not a trait name"))
            continue
        if name in seen:
            findings.append(("form", path, name, "trait repeated"))
            continue
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
    lines = [line for line in file_lines(text) if line.startswith("Workflows: ")]
    if not lines:
        return [("form", shown, "-", "status file has no Workflows line")]
    multi = len(lines) > 1
    findings = []
    seen_parts = {}
    for line in lines:
        rest = line[len("Workflows: "):]
        part, body, bad = prefix_of(rest, multi)
        if bad is not None:
            findings.append(("form", shown, bad, "Workflows line breaks the part-prefix rule"))
            continue
        if part is not None:
            seen_parts[part] = seen_parts.get(part, 0) + 1
            if seen_parts[part] == 2:
                findings.append(("e", shown, part, "two Workflows lines name the same part"))
        if body == "not yet classified":
            continue
        if body.count(TRAITS_MARK) != 1:
            findings.append(("form", shown, "-", "Workflows line must contain '; traits: ' exactly once"))
            continue
        head, traits = body.split(TRAITS_MARK, 1)
        check_head(head, shown, tables, findings)
        check_traits(traits, shown, tables, findings)
    return findings


def check_placement(path, text):
    """Where the Workflows lines stand beside Phase (R-015).

    A Workflows line starts with exactly `Workflows: `. The Phase line is the first
    line that starts with exactly `Phase: `. Text is split only at a line feed, as
    file_lines does. No Workflows line: no finding (a missing line belongs to
    check_status). Workflows lines and no Phase line: one finding, `status file has
    no Phase line`. Otherwise, with the Phase line at index p and k Workflows lines
    in the file, the lines at indexes p+1 through p+k must all be Workflows lines.
    When they are, no finding. When they are not, one finding: `Workflows lines do
    not stand together right after the Phase line`.
    """
    shown = slash(path)
    lines = file_lines(text)
    workflows = [index for index, line in enumerate(lines) if line.startswith("Workflows: ")]
    if not workflows:
        return []
    phase = None
    for index, line in enumerate(lines):
        if line.startswith("Phase: "):
            phase = index
            break
    if phase is None:
        return [("place", shown, "-", "status file has no Phase line")]
    k = len(workflows)
    run = lines[phase + 1:phase + 1 + k]
    if len(run) == k and all(line.startswith("Workflows: ") for line in run):
        return []
    return [("place", shown, "-", "Workflows lines do not stand together right after the Phase line")]


def print_findings(findings):
    problems = 0
    for code, path, name, reason in findings:
        path = escape_field(path)
        name = escape_field(name)
        reason = escape_field(reason)
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


class CheckArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        sys.stderr.write("%s: error: %s\n" % (self.prog, escape_field(message)))
        print("RESULT: not checked")
        sys.stdout.flush()
        self.exit(2)


def build_parser():
    parser = CheckArgumentParser(
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
        items, walk_errors = collect(root, set(tables["product_by_key"]))
        errors.extend(walk_errors)
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
            print("ERROR: %s: %s" % (escape_field(path), escape_field(reason)))
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
