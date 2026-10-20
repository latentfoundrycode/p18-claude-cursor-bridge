#!/usr/bin/env python3
"""trace-check: mechanical traceability from a pinned pre-split baseline (R-029).

  python trace-check.py [--repo DIR] [--map]

Compares every passage unit of bridge/commands/supervisor.md at the pinned baseline
commit with the working tree: the core and every *.md under bridge/cursor-bridge/workflow/
except bridge/cursor-bridge/workflow/trace-exceptions.md (the only home left out). Module files under
workflow/phases/, workflow/types/, and workflow/traits/ are checked for undeclared new text. Exceptions are
listed in workflow/trace-exceptions.md. A ~/.claude/... reference must name a path inside bridge/ with no
symbolic link, junction, or other reparse point on the way.

Finding lines, then TRACED and RESULT:
  FAIL (dropped)  a baseline passage is missing everywhere
  FAIL (copy)     a passage appears more often than at baseline (excused sections excluded)
  FAIL (new)      undeclared text in a module file
  FAIL (ref)      a ~/.claude/... reference does not resolve to a path inside bridge/ with no link on the way
  FAIL (cite)     a cited section heading does not resolve in any current home
  NOTE (reword)   a dropped passage excused by a reword entry
  MAP             with --map, each baseline passage and its current home(s)

Exit 0 when no FAIL line was printed. Exit 1 when at least one FAIL was printed.
Exit 2 when the check cannot run: not a git work tree, git unavailable, missing or
invalid trace-baseline.txt, baseline commit absent (a shallow clone is the likely cause),
missing supervisor.md, invalid trace-exceptions.md, a folder under bridge/cursor-bridge/workflow/
that cannot be read, a symbolic link, junction, or other reparse point met on a path the program
reads, a home not readable as UTF-8, or a usage error. Then ERROR lines and RESULT: not checked
are printed, with no traceback.
The check needs the baseline commit's object history.
"""
import argparse
import os
import re
import stat
import subprocess
import sys

GIT_TIMEOUT = 120
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
BASELINE_REL = "bridge/cursor-bridge/workflow/trace-baseline.txt"
EXCEPTIONS_REL = "bridge/cursor-bridge/workflow/trace-exceptions.md"
CORE_REL = "bridge/commands/supervisor.md"
WORKFLOW_PREFIX = "bridge/cursor-bridge/workflow/"
ENTRY_RE = re.compile(
    r"^- (reword|new) ([A-Z][A-Z0-9]*-[0-9]+) (\S+\.md) (.+)$"
)
HEADING_RE = re.compile(r"^ {0,3}(#{1,6}) (.*)$")
FENCE_OPEN_RE = re.compile(r"^(`{3,}|~{3,})")
LIST_ITEM_RE = re.compile(r"^([-*+]|[0-9]+[.)])\s")
REF_RE = re.compile(r"~/\.claude/([^\s`\"'()\[\],;]+)")
EM_DASH = "\u2014"
PLACEHOLDER_CHARS = frozenset("<>*\u2026")
REF_STRIP = ".:"
WIN_DEVICE_NAMES = frozenset(
    ["CON", "PRN", "AUX", "NUL"]
    + ["COM%d" % i for i in range(1, 10)]
    + ["LPT%d" % i for i in range(1, 10)]
)


def slash(path):
    return path.replace("\\", "/")


def escape_field(value):
    text = "" if value is None else str(value)
    parts = []
    for char in text:
        code = ord(char)
        if code < 0x20 or code == 0x7f:
            parts.append("\\x%02x" % code)
        elif code < 128:
            parts.append(char)
        elif code < 256:
            parts.append("\\x%02x" % code)
        elif code <= 0xFFFF:
            parts.append("\\u%04x" % code)
        else:
            parts.append("\\U%08x" % code)
    return "".join(parts)


def excerpt(normal):
    return escape_field(normal[:60])


def deepest_heading(chain):
    if not chain:
        return "-"
    return escape_field(chain[-1][1])


def file_lines(text):
    lines = text.split("\n")
    if lines and lines[-1] == "":
        del lines[-1]
    return lines


def is_thematic_break(stripped):
    if len(stripped) < 3:
        return False
    if stripped == stripped[0] * len(stripped) and stripped[0] in "-*_":
        return True
    return False


def normal_form_paragraph(lines):
    parts = []
    for line in lines:
        parts.append(line.strip())
    joined = " ".join(parts)
    return re.sub(r"\s+", " ", joined).strip()


def normal_form_fence(lines):
    return "\n".join(line.rstrip() for line in lines)


def parse_units(text):
    """Return (units, headings_outside_fences).

    units: list of dicts normal_form, chain, raw_lines.
    headings_outside_fences: list of heading texts in file order.
    """
    lines = file_lines(text)
    units = []
    headings_out = []
    chain = []
    in_fence = False
    fence_char = None
    fence_min = 0
    fence_lines = []
    current_para = None
    table_lines = None

    def end_unit():
        nonlocal current_para, table_lines
        if table_lines is not None:
            units.append({
                "normal": normal_form_paragraph(table_lines),
                "chain": list(chain),
                "kind": "table",
            })
            table_lines = None
        elif current_para is not None:
            if current_para["fence"]:
                units.append({
                    "normal": normal_form_fence(current_para["lines"]),
                    "chain": list(chain),
                    "kind": "fence",
                })
            else:
                units.append({
                    "normal": normal_form_paragraph(current_para["lines"]),
                    "chain": list(chain),
                    "kind": "para",
                })
            current_para = None

    for line in lines:
        stripped = line.strip()
        content = line.lstrip()

        if in_fence:
            fence_lines.append(line)
            if FENCE_OPEN_RE.match(stripped):
                run = FENCE_OPEN_RE.match(stripped).group(1)
                if run[0] == fence_char and len(run) >= fence_min:
                    in_fence = False
                    current_para = {"fence": True, "lines": fence_lines}
                    end_unit()
                    fence_lines = []
            continue

        if content.startswith("```") or content.startswith("~~~"):
            run_m = FENCE_OPEN_RE.match(stripped)
            if run_m:
                end_unit()
                in_fence = True
                fence_char = run_m.group(1)[0]
                fence_min = len(run_m.group(1))
                fence_lines = [line]
                continue

        hm = HEADING_RE.match(line)
        if hm:
            end_unit()
            level = len(hm.group(1))
            title = hm.group(2).strip()
            while chain and chain[-1][0] >= level:
                chain.pop()
            chain.append((level, title))
            headings_out.append(title)
            continue

        if stripped == "":
            end_unit()
            continue

        if is_thematic_break(stripped):
            end_unit()
            continue

        if stripped.startswith("|"):
            if table_lines is None:
                end_unit()
                table_lines = [line]
            else:
                table_lines.append(line)
            continue

        if table_lines is not None:
            end_unit()

        if LIST_ITEM_RE.match(stripped):
            end_unit()
            current_para = {"fence": False, "lines": [line]}
            continue

        if current_para is None:
            current_para = {"fence": False, "lines": [line]}
        else:
            current_para["lines"].append(line)

    if in_fence:
        current_para = {"fence": True, "lines": fence_lines}
    end_unit()
    return units, headings_out


def in_section(chain, heading_text):
    for _level, text in chain:
        if text == heading_text:
            return True
    return False


def git_run(root, args):
    try:
        proc = subprocess.run(
            ["git", "-C", root, *args],
            capture_output=True,
            stdin=subprocess.DEVNULL,
            timeout=GIT_TIMEOUT,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except subprocess.TimeoutExpired:
        return None, "timed out after %d s" % GIT_TIMEOUT
    except OSError as err:
        return None, "cannot be started (%s)" % err
    return proc, None


def decode_git_bytes(data):
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    return data.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")


def is_path_link(path):
    if os.path.islink(path):
        return True
    if hasattr(os.path, "isjunction") and os.path.isjunction(path):
        return True
    try:
        st = os.lstat(path)
    except OSError:
        return False
    attrs = getattr(st, "st_file_attributes", None)
    if attrs is not None and (attrs & stat.FILE_ATTRIBUTE_REPARSE_POINT):
        return True
    return False


def first_link_on_rel_path(root, rel):
    """Return the repo-relative path of the first link along rel from root, or None."""
    parts = [p for p in slash(rel).split("/") if p]
    current = root
    for part in parts:
        current = os.path.join(current, part)
        try:
            os.lstat(current)
        except OSError:
            return None
        if is_path_link(current):
            return slash(os.path.relpath(current, root))
    return None


def segment_refused(seg):
    if seg == "" or seg == "." or seg == "..":
        return True
    if "\\" in seg or ":" in seg:
        return True
    if seg.endswith(".") and seg != "...":
        return True
    if seg.split(".", 1)[0].upper() in WIN_DEVICE_NAMES:
        return True
    return False


def read_utf8_path(path):
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


def collect_md_paths(root, under_workflow, walk_errors):
    found = []

    def onerror(err):
        walk_errors.append((
            slash(err.filename),
            "cannot be read (%s)" % (err.strerror or err),
        ))

    for dirpath, dirnames, filenames in os.walk(under_workflow, onerror=onerror):
        keep = []
        for name in dirnames:
            full = os.path.join(dirpath, name)
            if is_path_link(full):
                walk_errors.append((
                    slash(os.path.relpath(full, root)),
                    "is a link",
                ))
                return found
            keep.append(name)
        dirnames[:] = keep
        for name in filenames:
            if not name.endswith(".md"):
                continue
            full = os.path.join(dirpath, name)
            if is_path_link(full):
                walk_errors.append((
                    slash(os.path.relpath(full, root)),
                    "is a link",
                ))
                return found
            rel = slash(os.path.relpath(full, root))
            if rel == EXCEPTIONS_REL:
                continue
            found.append(rel)
    found.sort()
    return found


def is_module_path(rel):
    rest = rel[len(WORKFLOW_PREFIX):] if rel.startswith(WORKFLOW_PREFIX) else ""
    for prefix in ("phases/", "types/", "traits/"):
        if rest.startswith(prefix):
            return True
    return False


def valid_exception_file(rel):
    if rel == CORE_REL:
        return True
    if rel.startswith(WORKFLOW_PREFIX) and rel.endswith(".md"):
        return True
    return False


def parse_exceptions(text, errors):
    entries = []
    lines = file_lines(text)
    entries_idx = None
    for idx, line in enumerate(lines):
        if line == "## Entries":
            entries_idx = idx
            break
    if entries_idx is None:
        errors.append((EXCEPTIONS_REL, "no ## Entries line (requirement 6)"))
        return None
    for idx in range(entries_idx + 1, len(lines)):
        line = lines[idx]
        line_no = idx + 1
        if line.strip() == "":
            continue
        m = ENTRY_RE.match(line)
        if not m:
            errors.append((
                EXCEPTIONS_REL,
                "line %d: malformed entry (requirement 6)" % line_no,
            ))
            return None
        kind, inc_id, file_rel, heading = m.group(1), m.group(2), m.group(3), m.group(4)
        if not valid_exception_file(file_rel) or not heading.strip():
            errors.append((
                EXCEPTIONS_REL,
                "line %d: malformed entry (requirement 6)" % line_no,
            ))
            return None
        entries.append({
            "kind": kind,
            "id": inc_id,
            "file": file_rel,
            "heading": heading.strip(),
        })
    return entries


def build_excuse_index(entries):
    """Return (excused_current, reword_baseline)."""
    excused_current = []
    reword_baseline = []
    for ent in entries:
        excused_current.append((ent["file"], ent["heading"]))
        if ent["kind"] == "reword":
            reword_baseline.append((ent["file"], ent["heading"], ent["id"]))
    return excused_current, reword_baseline


def unit_excused(path, unit, excused_current):
    for file_rel, heading in excused_current:
        if file_rel == path and in_section(unit["chain"], heading):
            return True
    return False


def bridge_contains(root, bridge_path):
    bridge_root = os.path.join(root, "bridge")
    try:
        real_target = os.path.realpath(bridge_path)
        real_bridge = os.path.realpath(bridge_root)
    except OSError:
        return False
    try:
        return os.path.commonpath([real_target, real_bridge]) == real_bridge
    except ValueError:
        return False


def resolve_ref(rest, root):
    rest = rest.rstrip(REF_STRIP)
    if rest.endswith("/"):
        rest = rest[:-1]
    bridge_root = os.path.join(root, "bridge")
    if rest == "":
        if first_link_on_rel_path(root, "bridge"):
            return False
        try:
            os.lstat(bridge_root)
            return True
        except OSError:
            return False
    segments = rest.split("/")
    for seg in segments:
        if segment_refused(seg):
            return False
    resolved = []
    for seg in segments:
        if seg == "..." or any(c in PLACEHOLDER_CHARS for c in seg):
            break
        resolved.append(seg)
    bridge_rel = "bridge" if not resolved else "bridge/" + "/".join(resolved)
    if first_link_on_rel_path(root, bridge_rel):
        return False
    current = bridge_root
    for seg in resolved:
        current = os.path.join(current, seg)
        try:
            os.lstat(current)
        except OSError:
            return False
    if not bridge_contains(root, current):
        return False
    return True


def find_refs_in_file(rel, text, root, findings_ref):
    lines = file_lines(text)
    for no, line in enumerate(lines, 1):
        for m in REF_RE.finditer(line):
            rest = m.group(1).rstrip(REF_STRIP)
            if not resolve_ref(rest, root):
                findings_ref.append((rel, no, "~/.claude/" + rest))


def citation_strings(normal):
    out = []
    pos = 0
    while pos < len(normal):
        m = re.search(r'\b(see|per|under) "', normal[pos:], re.IGNORECASE)
        if not m:
            break
        start = pos + m.end()
        end = normal.find('"', start)
        if end < 0:
            break
        if end == start:
            pos = end + 1
            continue
        quotes = [normal[start:end]]
        chain_pos = end + 1
        while True:
            chain_m = re.match(r' \u2192 "([^"]+)"', normal[chain_pos:])
            if not chain_m:
                break
            quotes.append(chain_m.group(1))
            chain_pos += chain_m.end()
        out.append(quotes)
        pos = chain_pos
    return out


def heading_resolves(title, all_headings):
    for h in all_headings:
        if h == title or h.startswith(title + " " + EM_DASH + " "):
            return True
    return False


def check_citations(rel, units, all_headings, findings_cite):
    for unit in units:
        for quote_chain in citation_strings(unit["normal"]):
            for q in quote_chain:
                if not heading_resolves(q, all_headings):
                    findings_cite.append((rel, deepest_heading(unit["chain"]), q))


def load_baseline_file(root, sha, rel, errors):
    proc, err = git_run(root, ["show", "%s:%s" % (sha, rel)])
    if proc is None:
        return None, err
    if proc.returncode != 0:
        errors.append((rel, "missing at baseline commit"))
        return None, None
    try:
        return decode_git_bytes(proc.stdout), None
    except UnicodeDecodeError:
        errors.append((rel, "cannot be read as UTF-8 at baseline"))
        return None, None


class CheckArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        if sys.stderr is not None:
            sys.stderr.write("%s: error: %s\n" % (self.prog, message))
        print("ERROR: usage: %s" % escape_field(message))
        print("RESULT: not checked")
        if sys.stdout is not None:
            sys.stdout.flush()
        self.exit(2)


def build_parser():
    parser = CheckArgumentParser(
        prog="trace-check.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--repo", default=None, metavar="DIR")
    parser.add_argument("--map", action="store_true")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.repo is not None:
        root = os.path.abspath(args.repo)
    else:
        here = os.path.abspath(__file__)
        root = os.path.dirname(os.path.dirname(os.path.dirname(here)))

    errors = []

    proc, err = git_run(root, ["rev-parse", "--is-inside-work-tree"])
    if proc is None:
        print("ERROR: git rev-parse: %s" % escape_field(err))
        print("RESULT: not checked")
        return 2
    if proc.returncode != 0 or proc.stdout.decode("ascii", "replace").strip() != "true":
        errors.append((slash(root), "not a git work tree"))

    link_rel = first_link_on_rel_path(root, BASELINE_REL)
    if link_rel:
        print("ERROR: %s: is a link" % escape_field(link_rel))
        print("RESULT: not checked")
        return 2

    baseline_path = os.path.join(root, BASELINE_REL)
    bl_text, bl_shown, bl_err = read_utf8_path(baseline_path)
    if bl_err:
        errors.append((bl_shown, bl_err if bl_err != "does not exist" else "missing"))
    else:
        bl_lines = file_lines(bl_text)
        if len(bl_lines) != 1 or not SHA_RE.match(bl_lines[0]):
            errors.append((bl_shown, "not a single 40-character lowercase commit id"))

    sha = bl_lines[0] if bl_text and not errors else None

    if sha and not errors:
        proc, err = git_run(root, ["cat-file", "-e", "%s^{commit}" % sha])
        if proc is None:
            print("ERROR: git cat-file: %s" % escape_field(err))
            print("RESULT: not checked")
            return 2
        if proc.returncode != 0:
            errors.append((
                sha,
                "baseline commit is absent from this repository; a shallow clone is the likely cause",
            ))

    link_rel = first_link_on_rel_path(root, EXCEPTIONS_REL)
    if link_rel:
        print("ERROR: %s: is a link" % escape_field(link_rel))
        print("RESULT: not checked")
        return 2

    exc_path = os.path.join(root, EXCEPTIONS_REL)
    exc_text, exc_shown, exc_err = read_utf8_path(exc_path)
    if exc_err:
        errors.append((exc_shown, exc_err if exc_err != "does not exist" else "missing"))
    entries = None
    if exc_text is not None and not errors:
        entries = parse_exceptions(exc_text, errors)

    link_rel = first_link_on_rel_path(root, CORE_REL)
    if link_rel:
        print("ERROR: %s: is a link" % escape_field(link_rel))
        print("RESULT: not checked")
        return 2

    core_path = os.path.join(root, CORE_REL)
    core_text, core_shown, core_err = read_utf8_path(core_path)
    if core_err:
        errors.append((core_shown, core_err))

    if errors:
        for path, reason in errors:
            print("ERROR: %s: %s" % (escape_field(path), escape_field(reason)))
        print("RESULT: not checked")
        return 2

    excused_current, reword_baseline = build_excuse_index(entries or [])

    baseline_workflow_paths = []
    proc, err = git_run(root, [
        "ls-tree", "-r", "-z", "--name-only", sha, "--", WORKFLOW_PREFIX,
    ])
    if proc is None:
        print("ERROR: git ls-tree: %s" % escape_field(err))
        print("RESULT: not checked")
        return 2
    if proc.returncode != 0:
        print("ERROR: git ls-tree: command failed")
        print("RESULT: not checked")
        return 2
    raw = proc.stdout
    for part in raw.split(b"\0"):
        if not part:
            continue
        try:
            rel = part.decode("utf-8")
        except UnicodeDecodeError:
            print("ERROR: %s: cannot be read as UTF-8" % escape_field(part.decode("latin-1")))
            print("RESULT: not checked")
            return 2
        if rel.endswith(".md") and rel != EXCEPTIONS_REL:
            baseline_workflow_paths.append(rel)
    baseline_workflow_paths.sort()

    baseline_homes = [CORE_REL] + baseline_workflow_paths
    workflow_rel = WORKFLOW_PREFIX.rstrip("/")
    link_rel = first_link_on_rel_path(root, workflow_rel)
    if link_rel:
        print("ERROR: %s: is a link" % escape_field(link_rel))
        print("RESULT: not checked")
        return 2

    current_workflow = os.path.join(root, workflow_rel)
    walk_errors = []
    current_workflow_paths = (
        collect_md_paths(root, current_workflow, walk_errors)
        if os.path.isdir(current_workflow)
        else []
    )
    if walk_errors:
        path, reason = walk_errors[0]
        print("ERROR: %s: %s" % (escape_field(path), escape_field(reason)))
        print("RESULT: not checked")
        return 2
    current_homes = [CORE_REL] + current_workflow_paths

    baseline_units_by_norm = {}
    baseline_supervisor_traced = []

    for rel in baseline_homes:
        text, git_err = load_baseline_file(root, sha, rel, errors)
        if git_err is not None:
            print("ERROR: git show: %s" % escape_field(git_err))
            print("RESULT: not checked")
            return 2
        if text is None:
            continue
        units, _heads = parse_units(text)
        for u in units:
            nf = u["normal"]
            baseline_units_by_norm[nf] = baseline_units_by_norm.get(nf, 0) + 1
            if rel == CORE_REL:
                baseline_supervisor_traced.append({
                    "normal": nf,
                    "chain": u["chain"],
                    "baseline_heading": deepest_heading(u["chain"]),
                })

    if errors:
        for path, reason in errors:
            print("ERROR: %s: %s" % (escape_field(path), escape_field(reason)))
        print("RESULT: not checked")
        return 2

    current_file_units = {}
    headings_by_file = {}
    findings_ref = []

    for rel in current_homes:
        full = os.path.join(root, rel.replace("/", os.sep))
        text, shown, err = read_utf8_path(full)
        if err:
            print("ERROR: %s: %s" % (escape_field(shown), escape_field(err)))
            print("RESULT: not checked")
            return 2
        units, heads = parse_units(text)
        current_file_units[rel] = units
        headings_by_file[rel] = heads
        find_refs_in_file(rel, text, root, findings_ref)

    all_headings = []
    for rel in current_homes:
        all_headings.extend(headings_by_file[rel])

    findings_cite = []
    for rel in current_homes:
        check_citations(rel, current_file_units[rel], all_headings, findings_cite)

    current_counts_all = {}
    current_paths_all = {}
    current_counts_c = {}
    current_paths_for_norm = {}
    for rel, units in current_file_units.items():
        for u in units:
            nf = u["normal"]
            current_counts_all[nf] = current_counts_all.get(nf, 0) + 1
            if rel not in current_paths_all.get(nf, []):
                current_paths_all.setdefault(nf, []).append(rel)
            if not unit_excused(rel, u, excused_current):
                current_counts_c[nf] = current_counts_c.get(nf, 0) + 1
                if rel not in current_paths_for_norm.get(nf, []):
                    current_paths_for_norm.setdefault(nf, []).append(rel)

    fails_dropped = []
    fails_copy = []
    fails_new = []
    fails_ref = []
    fails_cite = []
    notes = []
    seen_norm_finding = set()
    dropped_count = 0
    excused_count = 0

    def reword_excuses_drop(traced):
        chain = traced["chain"]
        for file_rel, heading, inc_id in reword_baseline:
            if file_rel != CORE_REL:
                continue
            if in_section(chain, heading):
                return inc_id
        return None

    for traced in baseline_supervisor_traced:
        nf = traced["normal"]
        b = baseline_units_by_norm.get(nf, 0)
        c_all = current_counts_all.get(nf, 0)
        c = current_counts_c.get(nf, 0)
        bh = traced["baseline_heading"]

        if nf in seen_norm_finding:
            continue

        if c_all == 0:
            rid = reword_excuses_drop(traced)
            if rid:
                notes.append(
                    "NOTE (reword %s) %s: %s - %s"
                    % (rid, CORE_REL, bh, excerpt(nf))
                )
                excused_count += 1
                seen_norm_finding.add(nf)
            else:
                fails_dropped.append(
                    "FAIL (dropped) %s: %s - %s" % (CORE_REL, bh, excerpt(nf))
                )
                dropped_count += 1
                seen_norm_finding.add(nf)
        elif c > b:
            paths = sorted(current_paths_for_norm.get(nf, []))
            fails_copy.append(
                "FAIL (copy) %s: %s - %s"
                % (", ".join(escape_field(p) for p in paths), bh, excerpt(nf))
            )
            seen_norm_finding.add(nf)

    module_files = sorted(
        rel for rel in current_workflow_paths if is_module_path(rel)
    )
    baseline_set = set(baseline_units_by_norm.keys())

    for rel in module_files:
        for u in current_file_units.get(rel, []):
            if unit_excused(rel, u, excused_current):
                continue
            nf = u["normal"]
            if nf not in baseline_set:
                h = deepest_heading(u["chain"])
                fails_new.append(
                    "FAIL (new) %s: %s - %s" % (escape_field(rel), h, excerpt(nf))
                )

    for rel, line_no, ref in findings_ref:
        fails_ref.append(
            "FAIL (ref) %s:%d: %s" % (escape_field(rel), line_no, escape_field(ref))
        )

    for rel, h, q in findings_cite:
        fails_cite.append(
            'FAIL (cite) %s: %s - "%s"' % (escape_field(rel), h, escape_field(q))
        )

    fails = fails_dropped + fails_copy + fails_new + fails_ref + fails_cite

    if args.map:
        for traced in baseline_supervisor_traced:
            nf = traced["normal"]
            paths = sorted(current_paths_all.get(nf, []))
            home = ", ".join(escape_field(p) for p in paths) if paths else "-"
            print(
                "MAP %s: %s - %s"
                % (home, traced["baseline_heading"], excerpt(nf))
            )

    for line in fails:
        print(line)
    for line in notes:
        print(line)

    k_super = 0
    k_workflow = 0
    for traced in baseline_supervisor_traced:
        nf = traced["normal"]
        if any(u["normal"] == nf for u in current_file_units.get(CORE_REL, [])):
            k_super += 1
        if any(
            u["normal"] == nf
            for r in current_workflow_paths
            for u in current_file_units.get(r, [])
        ):
            k_workflow += 1
    n_traced = len(baseline_supervisor_traced)
    print(
        "TRACED: %d passages of baseline %s; %d in supervisor.md, %d under workflow/, %d dropped, %d excused"
        % (
            n_traced,
            sha[:7],
            k_super,
            k_workflow,
            dropped_count,
            excused_count,
        )
    )
    if fails:
        print("RESULT: %d problem(s)" % len(fails))
        return 1
    print("RESULT: OK")
    return 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="backslashreplace")
    sys.exit(main())
