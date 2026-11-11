#!/usr/bin/env python3
"""Write YAML headers on dual-read records from bridge_env prose fallbacks.

  python records-migrate.py [--check] [--base <ref>] [<project root>|<record>...]

Run from a project root. ASCII output apart from path names.
"""
import argparse
import glob
import os
import re
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bridge_env

_STATUS_MAX_CHARS = 12000
_STATUS_MAX_LINES = 120

_DIAGRAM_ROLE_KEYS = tuple(bridge_env.HEADER_SCHEMAS["DiagramIndexRoles"].keys())
_DEVIATION_ROLE_KEYS = tuple(bridge_env.HEADER_SCHEMAS["DeviationsRoles"].keys())


def build_parser():
    ap = argparse.ArgumentParser(description="Write record headers from prose fallbacks.")
    ap.add_argument("--check", action="store_true", help="list what would be written, write nothing")
    ap.add_argument("--base", default="origin/main", help="git ref for merged increment IDs")
    ap.add_argument("paths", nargs="*", help="project root and/or record paths")
    return ap


def _crlf_body(raw):
    return b"\r\n" in raw


def _line_ending(crlf):
    return "\r\n" if crlf else "\n"


def _needs_quote(s):
    if not isinstance(s, str):
        return True
    if s == "":
        return True
    if re.fullmatch(r"[0-9]+", s):
        return True
    if re.fullmatch(r"^-?[0-9]+$", s):
        return True
    if re.search(r"[0-9]", s) and s[0].isdigit():
        return True
    if re.match(r"^-?\d", s):
        return True
    if any(c in s for c in " :/#\t") or any(ord(c) > 126 for c in s):
        return True
    if not bridge_env._PLAIN_WORD_RE.fullmatch(s):
        return True
    if s.lower() in bridge_env._PLAIN_TYPED_WORDS:
        return True
    return False


def _escape_string(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _format_scalar(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, str):
        if value == "":
            return '""'
        if _needs_quote(value):
            return '"%s"' % _escape_string(value)
        return value
    raise TypeError(value)


def _flow_item_ok(value):
    if value is None or isinstance(value, bool):
        return True
    if isinstance(value, int) and not isinstance(value, bool):
        return True
    if isinstance(value, str):
        if value == "":
            return True
        if "\n" in value or '"' in value and _needs_quote(value):
            return False
        return True
    return False


def _use_flow_list(items):
    return items is not None and all(_flow_item_ok(x) for x in items)


def _format_flow_list(items):
    parts = [_format_scalar(x) for x in items]
    return "[%s]" % ", ".join(parts)


def _dump_lines(mapping, schema_name, indent=0):
    table = bridge_env.HEADER_SCHEMAS[schema_name]
    lines = []
    pad = " " * indent
    for key in table:
        if key not in mapping:
            continue
        value = mapping[key]
        spec = table[key]
        prefix = pad + key + ":"
        if spec.startswith("list of "):
            inner = spec[len("list of "):]
            if inner in bridge_env.HEADER_SCHEMAS:
                if not value:
                    lines.append(prefix + " []")
                else:
                    lines.append(prefix)
                    lines.extend(_dump_list_of_mappings(value, inner, indent + 2))
            elif _use_flow_list(value or []):
                lines.append(prefix + " " + _format_flow_list(value or []))
            else:
                lines.append(prefix)
                for item in value or []:
                    lines.append(pad + "  - " + _format_scalar(item))
        elif spec in bridge_env.HEADER_SCHEMAS:
            lines.append(prefix)
            if isinstance(value, dict):
                lines.extend(_dump_lines(value, spec, indent + 2))
        else:
            lines.append(prefix + " " + _format_scalar(value))
    return lines


def _dump_list_of_mappings(items, schema_name, indent):
    lines = []
    table = bridge_env.HEADER_SCHEMAS[schema_name]
    keys = list(table.keys())
    pad = " " * indent
    for item in items:
        if not isinstance(item, dict):
            continue
        first = keys[0]
        rest = keys[1:]
        val0 = item.get(first)
        spec0 = table[first]
        if spec0 in bridge_env.HEADER_SCHEMAS and isinstance(val0, dict):
            lines.append(pad + "- " + first + ":")
            lines.extend(_dump_lines(val0, spec0, indent + 4))
        elif spec0.startswith("list of "):
            lines.append(pad + "- " + first + ": " + _format_flow_list(val0 or []))
        else:
            lines.append(pad + "- " + first + ": " + _format_scalar(val0))
        for key in rest:
            spec = table[key]
            val = item.get(key)
            col = " " * (indent + 2)
            if spec.startswith("list of "):
                inner = spec[len("list of "):]
                if inner in bridge_env.HEADER_SCHEMAS:
                    if not val:
                        lines.append(col + key + ": []")
                    else:
                        lines.append(col + key + ":")
                        lines.extend(_dump_list_of_mappings(val, inner, indent + 4))
                elif _use_flow_list(val or []):
                    lines.append(col + key + ": " + _format_flow_list(val or []))
                else:
                    lines.append(col + key + ":")
                    for x in val or []:
                        lines.append(col + "  - " + _format_scalar(x))
            elif spec in bridge_env.HEADER_SCHEMAS:
                lines.append(col + key + ":")
                if isinstance(val, dict):
                    lines.extend(_dump_lines(val, spec, indent + 4))
            else:
                lines.append(col + key + ": " + _format_scalar(val))
    return lines


def _serialize_header(header, kind):
    lines = _dump_lines(header, kind, 0)
    return lines


def record_kind(rel):
    norm = rel.replace("\\", "/")
    base = os.path.basename(norm)
    if norm == "docs/PROJECT_STATUS.md":
        return "project-status"
    if base.startswith("BUILD_PLAN") and base.endswith(".md") and norm.startswith("docs/"):
        rest = norm[len("docs/"):]
        if "/" in rest:
            return None
        return "build-plan"
    if norm.startswith("handoff/") and "/" not in norm[len("handoff/"):]:
        if bridge_env.HANDOFF_REPORT_NAME.search(base):
            return None
        stem = base[:-3] if base.endswith(".md") else base
        if bridge_env.HANDOFF_RESOLUTION.match(stem):
            return None
        if not base.endswith(".md"):
            return None
        return "brief"
    if norm == "docs/INVENTORY.md":
        return "inventory"
    if norm == "docs/REQUIREMENTS.md":
        return "requirements"
    if norm == "docs/diagrams/INDEX.md":
        return "diagram-index"
    if norm == "docs/diagrams/DEVIATIONS.md":
        return "deviations"
    if norm == "docs/RUN_PARAMETERS.md":
        return "run-parameters"
    return None


def enumerate_records(root):
    out = []
    fixed = [
        "docs/PROJECT_STATUS.md",
    ]
    for rel in fixed:
        if os.path.isfile(os.path.join(root, *rel.split("/"))):
            out.append((rel, False))
    for path in sorted(glob.glob(os.path.join(root, "docs", "BUILD_PLAN*.md"))):
        out.append((os.path.relpath(path, root).replace("\\", "/"), False))
    handoff = os.path.join(root, "handoff")
    if os.path.isdir(handoff):
        for name in sorted(os.listdir(handoff)):
            if not name.endswith(".md"):
                continue
            rel = "handoff/" + name
            if record_kind(rel):
                out.append((rel, False))
    for rel in ("docs/INVENTORY.md", "docs/REQUIREMENTS.md",
                "docs/diagrams/INDEX.md", "docs/diagrams/DEVIATIONS.md", "docs/RUN_PARAMETERS.md"):
        if os.path.isfile(os.path.join(root, *rel.split("/"))):
            out.append((rel, False))
    return out


def _plan_needs_merged(text):
    try:
        body = bridge_env.plan_body(text)
    except bridge_env.HeaderError:
        body = text
    walk = bridge_env.walk_plan_prose_body(body)
    for st in walk["stages"]:
        for inc in st["increments"]:
            fields = inc.get("fields") or {}
            if "scope" not in fields and "kind" not in fields:
                return True
    return False


def _plan_unbalanced_id(text):
    try:
        body = bridge_env.plan_body(text)
    except bridge_env.HeaderError:
        body = text
    walk = bridge_env.walk_plan_prose_body(body)
    for st in walk["stages"]:
        for inc in st["increments"]:
            raw = (inc.get("fields") or {}).get("scope")
            if bridge_env.plan_scope_paren_unbalanced(raw):
                return inc["id"]
    return None


def _compose_plan_header(text, merged):
    fb = bridge_env.plan_prose_fallback(text, merged)
    stages_out = []
    for st in fb.get("stages") or []:
        incs_out = []
        for inc in st.get("increments") or []:
            fields = inc.get("fields") or {}
            iid = inc.get("id")
            merged_set = merged if merged is not None else set()
            incs_out.append({
                "id": iid,
                "title": inc.get("title"),
                "kind": bridge_env._kind_norm(fields.get("kind") if "kind" in fields else None),
                "parent": bridge_env._plan_field_value("parent", fields),
                "depends_on": bridge_env._plan_field_value("depends_on", fields),
                "parallel": bridge_env._plan_field_value("parallel", fields),
                "diagrams": bridge_env._plan_field_value("diagrams", fields),
                "scope": bridge_env._plan_field_value("scope", fields),
                "satisfies": bridge_env._plan_field_value("satisfies", fields),
                "deferred": bridge_env._plan_field_value("deferred", fields),
                "historic": bridge_env._derived_historic(fields, iid, merged_set),
            })
        stages_out.append({
            "name": st.get("name"),
            "demonstration": bool(bridge_env._demonstration_present(st.get("demonstration"))),
            "increments": incs_out,
        })
    return {"record": "build-plan", "header": 1, "stages": stages_out}


def _compose_brief_header(text, brief_name):
    parsed = bridge_env.parse_review_name(brief_name)
    if not parsed:
        return None, "the name cannot be read by the grammar"
    bid, rnd = parsed
    _paths, refusal, _unread = bridge_env.parse_scope(text)
    if refusal is not None:
        return None, refusal
    fb = bridge_env.brief_prose_fallback(text, brief_name)
    mu = fb.get("merge_unit")
    if isinstance(mu, tuple):
        mu = list(mu)
    return {
        "record": "brief",
        "header": 1,
        "id": bid,
        "round": rnd,
        "satisfies": list(fb.get("satisfies") or []),
        "scope": list(fb.get("scope") or []),
        "merge_unit": mu,
        "blocking_class": fb.get("blocking_class"),
    }, None


def _compose_status_header(text):
    fb = bridge_env.status_fallback(text)
    return {
        "record": "project-status",
        "header": 1,
        "phase": fb.get("phase"),
        "workflows": fb.get("workflows") or [],
        "awaiting_user_on": fb.get("awaiting_user_on"),
        "bridge_version": fb.get("bridge_version"),
        "stage": fb.get("stage"),
        "open_issues": fb.get("open_issues") or [],
    }


def _compose_inventory_header(text):
    fb = bridge_env.inventory_fallback(text)
    sections = fb.get("sections") or {}
    for key in ("features", "resources", "decisions", "deferred"):
        if key not in sections or not sections[key]:
            return None, "missing inventory section %s" % key
    tables = {}
    for key in ("features", "resources", "decisions", "deferred"):
        cols = list(sections[key])
        if not cols:
            return None, "inventory table %s has no header row" % key
        tables[key] = {"columns": cols, "key": cols[0]}
    refl = fb.get("reflected_through")
    return {
        "record": "inventory",
        "header": 1,
        "reflected_through": refl,
        "development_data": fb.get("development_data") or "",
        "tables": tables,
    }, None


def _compose_register_header(text):
    row = list(bridge_env.register_fallback(text).get("header_row") or [])
    if len(row) < 5:
        return None, "requirements table has too few columns"
    return {
        "record": "requirements",
        "header": 1,
        "columns": row,
        "roles": {"id": row[0], "status": row[3], "evidence": row[4]},
        "statuses": list(bridge_env._REQ_STATUSES),
    }, None


def _compose_index_header(text):
    row = list(bridge_env.diagram_index_fallback(text).get("header_row") or [])
    if len(row) < len(_DIAGRAM_ROLE_KEYS):
        return None, "diagram index table has too few columns"
    roles = {rk: row[i] for i, rk in enumerate(_DIAGRAM_ROLE_KEYS)}
    return {
        "record": "diagram-index",
        "header": 1,
        "columns": row,
        "roles": roles,
    }, None


def _compose_deviations_header(text):
    row = list(bridge_env.deviations_fallback(text).get("header_row") or [])
    if len(row) < len(_DEVIATION_ROLE_KEYS):
        return None, "deviations table has too few columns"
    roles = {rk: row[i] for i, rk in enumerate(_DEVIATION_ROLE_KEYS)}
    return {
        "record": "deviations",
        "header": 1,
        "columns": row,
        "roles": roles,
    }, None


def _compose_run_parameters_header(text):
    fb = bridge_env.run_parameters_fallback(text)
    out = {"record": "run-parameters", "header": 1}
    for key in bridge_env.HEADER_SCHEMAS["run-parameters"]:
        if key in ("record", "header"):
            continue
        out[key] = fb.get(key)
    return out


def compose_header(kind, text, rel, merged):
    if kind == "project-status":
        return _compose_status_header(text), None
    if kind == "build-plan":
        bad = _plan_unbalanced_id(text)
        if bad:
            return None, "unbalanced parenthesis in %s's Scope" % bad
        if _plan_needs_merged(text):
            if merged is None:
                return None, "merged_set_unreadable"
            return _compose_plan_header(text, merged), None
        return _compose_plan_header(text, set()), None
    if kind == "brief":
        brief_name = os.path.splitext(os.path.basename(rel.replace("\\", "/")))[0]
        return _compose_brief_header(text, brief_name)
    if kind == "inventory":
        return _compose_inventory_header(text)
    if kind == "requirements":
        return _compose_register_header(text)
    if kind == "diagram-index":
        return _compose_index_header(text)
    if kind == "deviations":
        return _compose_deviations_header(text)
    if kind == "run-parameters":
        return _compose_run_parameters_header(text), None
    return None, "unknown kind"


def fallback_for(kind, text, rel, merged):
    if kind == "brief":
        brief_name = os.path.splitext(os.path.basename(rel.replace("\\", "/")))[0]
        return bridge_env.brief_prose_fallback(text, brief_name)
    if kind == "build-plan":
        return bridge_env.plan_prose_fallback(text, merged)
    if kind == "project-status":
        return bridge_env.status_fallback(text)
    if kind == "inventory":
        return bridge_env.inventory_fallback(text)
    if kind == "requirements":
        return bridge_env.register_fallback(text)
    if kind == "diagram-index":
        return bridge_env.diagram_index_fallback(text)
    if kind == "deviations":
        return bridge_env.deviations_fallback(text)
    if kind == "run-parameters":
        return bridge_env.run_parameters_fallback(text)
    return {}


def _status_cap_text(new_file):
    text = bridge_env.decode_record_bytes(new_file)
    return len(text), len(text.splitlines())


def _validate_read_back(kind, new_bytes, text, rel, merged):
    decoded = bridge_env.decode_record_bytes(new_bytes)
    try:
        header, body = bridge_env.read_header(decoded)
    except bridge_env.HeaderError as err:
        return "read_header: %s" % err
    if header is None:
        return "read_header found no header"
    findings = bridge_env.check_header(kind, header)
    if findings:
        return "check_header: " + "; ".join(findings)
    fb = fallback_for(kind, text, rel, merged)
    disagree = bridge_env.header_agrees(kind, header, fb)
    if disagree:
        return "header_agrees: " + ", ".join(disagree)
    return None


def _write_record(path, shown, kind, header, raw_body, check_mode, crlf, original_text, rel, merged):
    le = _line_ending(crlf)
    header_lines = _serialize_header(header, kind)
    new_body = le.join(["---"] + header_lines + ["---"]) + le
    bom_prefix = b""
    body_bytes = raw_body
    if raw_body.startswith(b"\xef\xbb\xbf"):
        bom_prefix = b"\xef\xbb\xbf"
        body_bytes = raw_body[3:]
    new_file = bom_prefix + new_body.encode("utf-8") + body_bytes

    if kind == "project-status":
        nchars, nlines = _status_cap_text(new_file)
        if nchars > _STATUS_MAX_CHARS:
            print("cannot write %s: %d characters with the header, over the older cap; trim the body first" % (
                shown, nchars))
            return "cannot_write", 0
        if nlines > _STATUS_MAX_LINES:
            print("cannot write %s: %d lines with the header, over the older cap; trim the body first" % (
                shown, nlines))
            return "cannot_write", 0

    if check_mode:
        err = _validate_read_back(kind, new_file, original_text, rel, merged)
        if err:
            print("records-migrate: %s: in-memory check failed: %s" % (shown, err))
            return "fail", 3
        print("would write %s" % shown)
        return "would_write", 0

    folder = os.path.dirname(os.path.abspath(path))
    tmp = os.path.join(folder, ".records-migrate-%s.tmp" % uuid.uuid4().hex)
    try:
        with open(tmp, "xb") as f:
            f.write(new_file)
    except OSError as exc:
        print("records-migrate: %s: temporary write failed: %s" % (shown, exc))
        try:
            os.remove(tmp)
        except OSError:
            pass
        return "fail", 3
    try:
        with open(tmp, "rb") as f:
            on_disk = f.read()
    except OSError as exc:
        print("records-migrate: %s: temporary read failed: %s" % (shown, exc))
        try:
            os.remove(tmp)
        except OSError:
            pass
        return "fail", 3
    err = _validate_read_back(kind, on_disk, original_text, rel, merged)
    if err:
        print("records-migrate: %s: read-back failed: %s" % (shown, err))
        try:
            os.remove(tmp)
        except OSError:
            pass
        return "fail", 3
    try:
        os.replace(tmp, path)
    except OSError as exc:
        print("records-migrate: %s: replace failed: %s" % (shown, exc))
        try:
            os.remove(tmp)
        except OSError:
            pass
        return "fail", 3
    print("wrote %s" % shown)
    return "wrote", 0


def _handle_headed(path, shown, kind, raw, check_mode):
    text = bridge_env.decode_record_bytes(raw)
    try:
        header, _body = bridge_env.read_header(text)
    except bridge_env.HeaderError as err:
        print("HEADER MALFORMED: %s: %s" % (shown, err))
        return "malformed", 2
    if header is None:
        return None, 0
    findings = bridge_env.check_header(kind, header)
    if findings:
        print("HEADER MALFORMED: %s: %s" % (shown, "; ".join(findings)))
        return "malformed", 2
    print("has a header %s" % shown)
    return "has_header", 0


def main(argv):
    args = build_parser().parse_args(argv)
    if args.base.startswith("-"):
        print("records-migrate: refusing --base %s (a base must not begin with '-')" % args.base)
        return 2

    dirs = [p for p in args.paths if os.path.isdir(p)]
    files = [p for p in args.paths if not os.path.isdir(p)]
    if len(dirs) > 1:
        print("records-migrate: only one project root may be given")
        return 2
    if dirs and files:
        print("records-migrate: give a project root or record paths, not both")
        return 2

    cwd = os.getcwd()
    if dirs:
        root = os.path.abspath(dirs[0])
    else:
        root = cwd

    work = []
    if files:
        for fp in files:
            work.append((fp, True, fp))
    else:
        for rel, _ in enumerate_records(root):
            work.append((rel, False, os.path.join(root, *rel.split("/"))))

    merged_cache = {}
    check_mode = args.check
    exit_code = 0
    had_cannot_write = False
    had_would_or_write = False

    for shown_arg, explicit, abspath in work:
        abspath = os.path.normpath(abspath if os.path.isabs(abspath) else os.path.join(cwd, abspath))
        if explicit:
            shown = shown_arg
            try:
                rel = os.path.relpath(abspath, root).replace("\\", "/")
            except ValueError as exc:
                print("cannot read %s: %s" % (shown, exc))
                continue
        else:
            rel = shown_arg
            shown = rel

        if os.path.islink(abspath):
            print("cannot read %s: a symbolic link" % shown)
            continue

        if not os.path.isfile(abspath):
            if not os.path.exists(abspath):
                reason = "no such file"
            else:
                reason = "not a file"
            print("cannot read %s: %s" % (shown, reason))
            continue

        kind = record_kind(rel)
        if kind is None:
            print("cannot read %s: not a record kind" % shown)
            continue

        try:
            with open(abspath, "rb") as f:
                raw = f.read()
        except OSError as exc:
            print("cannot read %s: %s" % (shown, exc))
            continue

        text = bridge_env.decode_record_bytes(raw)
        try:
            header, _body = bridge_env.read_header(text)
        except bridge_env.HeaderError as err:
            print("HEADER MALFORMED: %s: %s" % (shown, err))
            return 2
        if header is not None:
            findings = bridge_env.check_header(kind, header)
            if findings:
                print("HEADER MALFORMED: %s: %s" % (shown, "; ".join(findings)))
                return 2
            print("has a header %s" % shown)
            continue

        crlf = _crlf_body(raw)

        merged = None
        if kind == "build-plan":
            bad = _plan_unbalanced_id(text)
            if bad:
                print("cannot read %s: unbalanced parenthesis in %s's Scope" % (shown, bad))
                continue
            merged_key = root
            if _plan_needs_merged(text):
                if merged_key not in merged_cache:
                    merged_cache[merged_key] = bridge_env.squash_merged_ids(
                        root, bridge_env.PLAN_ID_PATTERN, ref=args.base)
                merged = merged_cache[merged_key]
                if merged is None:
                    print("cannot read %s: merged set unreadable (git ref %s)" % (shown, args.base))
                    continue

        header, err = compose_header(kind, text, rel, merged)
        if err == "merged_set_unreadable":
            print("cannot read %s: merged set unreadable (git ref %s)" % (shown, args.base))
            continue
        if header is None:
            print("cannot read %s: %s" % (shown, err))
            continue

        plan_merged = merged if kind == "build-plan" else None
        if kind == "build-plan" and not _plan_needs_merged(text):
            plan_merged = None

        result, code = _write_record(
            abspath, shown, kind, header, raw, check_mode, crlf, text, rel, plan_merged)
        if code == 3:
            return 3
        if result == "cannot_write":
            had_cannot_write = True
        elif result in ("would_write", "wrote"):
            had_would_or_write = True

    if check_mode:
        return 1 if (had_would_or_write or had_cannot_write) else 0
    if had_cannot_write:
        return 1
    return exit_code


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(errors="backslashreplace")
    sys.exit(main(sys.argv[1:]))
