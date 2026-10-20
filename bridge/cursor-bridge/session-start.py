#!/usr/bin/env python3
"""session-start: a Claude Code SessionStart hook (matchers: compact, resume, fork) that puts
the supervisor's core rules back after a compaction, a resume or a fork (KP-035, R-005).

Why: when a session's context is compacted, Claude Code re-attaches only the first part of
an invoked command (measured: 20,000 of the supervisor's 150,000 characters, 13%), so the
supervisor carried on for hours without its loop, its gate and its standing rules, and the
record shows the rule-breaking that followed.

Claude Code caps every hook's plain stdout at 10,000 characters and, above that, replaces it
with a file path and a 2,000-character preview. The two things this hook prints do not fit
together under that cap on a real project (the 0b review measured 9,841 characters, and the
part that was cut was the pointers), so the bridge registers the hook TWICE for the same
event, each run printing one part under its own cap:

  --part pointers   the project's phase from docs/PROJECT_STATUS.md (the "awaiting" text
                    capped), the phase module file(s) to re-read whole, any sub-files and
                    variant files named on those modules' pointer lines, the conditional
                    workflow files (type, then sub-type, then traits in open-list order) that
                    touch the phase, the conventions that phase relies on, and whether to
                    continue or to wait for the owner; no supervisor.md line ranges;
  --part digest     the digest at the top of ~/.claude/commands/supervisor.md (between the
                    markers <!-- digest:start --> and <!-- digest:end -->), the one text the
                    maintainer keeps as the condensed core.

Pointer-line grammar (module files under workflow/phases/, read as UTF-8 with BOM dropped):
a line outside fenced blocks (opening_fence / closing_fence as workflow-check.py reads them;
an unclosed fence runs to the end of the file) that begins at column 0 with exactly
``Sub-files: `` or ``Variants: ``; after the prefix, one or more paths separated by ``; ``.
Each path, ignoring trailing whitespace on the line, must match
``^[a-z0-9-]+(/[a-z0-9-]+)*\\.md$`` (relative to workflow/phases/). Other paths on the line
are ignored. Sub-files and Variants lines are taken together in file order; a path already
printed is not printed again. Named paths are not checked for existence.

Conditional files: for each ``Workflows: `` line in file order, after dropping an optional
``<part>: `` prefix, skipping ``not yet classified`` and malformed lines, map type, optional
sub-type (``\u2192`` between names), and traits to keys through the installed open list;
candidates are types/<key>.md, then types/<type>/<sub>.md, then traits/<key>.md for traits
sorted by the open list's trait order. A file is named only when it exists under the
installed workflow folder as a regular readable UTF-8 file, is not a link, and touches the
phase (an add/set heading's module key or a replace target matches a phase module key;
headings inside fences do not count).

Failing open: if the installed workflow-check.py cannot be loaded or the open list or registry
cannot be read, no conditional file and no pointer-line file is named; one plain line states
what could not be read (only when a phase module file exists or a classified Workflows line
needed that read). The hook still never blocks.

Without --part both are printed (tests, manual runs). It prints nothing outside a bridge
project (no docs/PROJECT_STATUS.md found from the session's folder, its Workspace, a parent,
or a worktree). It FAILS OPEN on purpose: a session that is not the project's supervisor
(a review or a planning session opened in a project folder) is told to ignore the message,
because a gate on the transcript silenced the hook on two of three live supervisor sessions
(one invoked through the Skill tool, one continuing an earlier transcript; the 0b review's
second pass, S1), and a silent supervisor is the failure this hook exists to prevent. A
forked session is told not to continue the loop (S8). It never blocks (exit 0 always), never
writes anything, and keeps each part under the cap. ASCII-only apart from what it quotes.
"""
import importlib.util
import json
import os
import re
import sys

MAX_OUTPUT = 9800           # per part; Claude Code's cap is 10,000
AWAITING_MAX = 300          # the quoted "Awaiting user on" text; the file is read whole anyway

PHASE_MODULES = {
    "intake": ["intake"],
    "design": ["design"],
    "mockups": ["interface"],
    "interface": ["interface"],
    "planning": ["planning", "run-parameters"],
    "configuration": ["configuration"],
    "configuring": ["configuration"],
    "configure": ["configuration"],
    "building": ["delegation-loop", "reflection", "project-end"],
    "done": ["change-cycle"],
    "changing": ["change-cycle", "delegation-loop", "reflection", "project-end"],
}
PHASE_CONVENTIONS = {
    "building": ["~/.claude/cursor-bridge/Merge-Verification-Policy.md", "~/.claude/cursor-bridge/Known-Pitfalls.md"],
    "changing": ["~/.claude/cursor-bridge/Merge-Verification-Policy.md", "~/.claude/cursor-bridge/Known-Pitfalls.md"],
    "design": ["~/.claude/cursor-bridge/Diagram-Planning-Conventions.md", "~/.claude/cursor-bridge/Glossary.md"],
    "configuration": ["~/.claude/cursor-bridge/Cursor-Project-Configuration.md", "~/.claude/cursor-bridge/Known-Pitfalls.md"],
    "configuring": ["~/.claude/cursor-bridge/Cursor-Project-Configuration.md", "~/.claude/cursor-bridge/Known-Pitfalls.md"],
    "configure": ["~/.claude/cursor-bridge/Cursor-Project-Configuration.md", "~/.claude/cursor-bridge/Known-Pitfalls.md"],
}

WORKFLOW_PREFIX = "~/.claude/cursor-bridge/workflow/"
PHASE_PREFIX = WORKFLOW_PREFIX + "phases/"
POINTER_PATH = re.compile(r"^[a-z0-9-]+(/[a-z0-9-]+)*\.md$")
PROJECT_END_NOTE = "(read at the close of the plan's last stage)"
TRAITS_MARK = "; traits: "
ARROW = "\u2192"


def status_candidates(cwd):
    bases = []
    for start in (cwd, os.environ.get("CLAUDE_PROJECT_DIR") or ""):
        if not start:
            continue
        d = os.path.abspath(start)
        parts = d.replace("\\", "/").split("/")
        if "Worktrees" in parts:
            bases.append(os.path.join("/".join(parts[:parts.index("Worktrees")]), "Workspace"))
        for _ in range(4):
            bases.append(d)
            bases.append(os.path.join(d, "Workspace"))
            parent = os.path.dirname(d)
            if parent == d:
                break
            d = parent
    seen, out = set(), []
    for b in bases:
        if b not in seen:
            seen.add(b)
            out.append(os.path.join(b, "docs", "PROJECT_STATUS.md"))
    return out


def read_status(cwd):
    for p in status_candidates(cwd):
        if os.path.isfile(p):
            with open(p, encoding="utf-8-sig", errors="replace") as f:
                return f.read()
    return None


def field(text, name):
    pat = r"^\s*(?:[-*]\s+)?[*_`]*%s[*_`]*\s*:[*_`]*\s*(.*?)\s*$" % re.escape(name)
    m = re.search(pat, text, re.M | re.I)
    return m.group(1).strip().strip("*_`").strip() if m else None


def installed_version():
    """The release this program belongs to: the digest it sends is that release's, whatever
    the project's status file records (the two differ between an install or a rollback and
    the project's next calibration)."""
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "VERSION"), encoding="utf-8-sig") as f:
            return f.read().strip().split()[0]
    except (OSError, IndexError):
        return "?"


def supervisor_path():
    home = os.path.expanduser("~")
    return os.path.join(home, ".claude", "commands", "supervisor.md")


def bridge_root():
    return os.path.join(os.path.expanduser("~"), ".claude", "cursor-bridge")


def workflow_root():
    return os.path.join(bridge_root(), "workflow")


def read_digest(path):
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        text = f.read()
    a, b = text.find("<!-- digest:start -->"), text.find("<!-- digest:end -->")
    return text[a + len("<!-- digest:start -->"):b].strip() if a >= 0 and b > a else ""


def cap(text, limit, what):
    if len(text) <= limit:
        return text
    return text[:limit - 90] + "\n[%s cut at %d characters by the hook's cap; re-read it in the file]" % (what, limit)


def load_workflow_check():
    """Return (mod, tables, error_line). error_line is None on success."""
    checker = os.path.join(bridge_root(), "workflow-check.py")
    shown = checker.replace("\\", "/")
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec = importlib.util.spec_from_file_location("workflow_check_hook", checker)
        if spec is None or spec.loader is None:
            raise ImportError("no loader")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except (Exception, SystemExit) as err:
        return None, None, "%s: cannot be loaded (%s)" % (shown, type(err).__name__)
    finally:
        sys.dont_write_bytecode = previous
    open_text, open_shown, open_err = mod.read_utf8(mod.DEFAULT_OPEN)
    reg_text, reg_shown, reg_err = mod.read_utf8(mod.DEFAULT_REGISTRY)
    if open_err:
        return mod, None, "%s: %s" % (open_shown, open_err)
    if reg_err:
        return mod, None, "%s: %s" % (reg_shown, reg_err)
    tables, errors = mod.load_tables(open_text, mod.DEFAULT_OPEN, reg_text, mod.DEFAULT_REGISTRY)
    if errors:
        path, reason = errors[0]
        return mod, None, "%s: %s" % (path, reason)
    return mod, tables, None


def phase_module_installed(key):
    return os.path.join(workflow_root(), "phases", key + ".md")


def parse_workflows_tail(tail):
    """Parse one Workflows line body (after 'Workflows: '). Return None or (type_name, sub_name, trait_names)."""
    if TRAITS_MARK not in tail:
        return None
    head, traits_text = tail.split(TRAITS_MARK, 1)
    if TRAITS_MARK in traits_text:
        return None
    head = head.strip()
    if ": " in head:
        head = head.split(": ", 1)[1].strip()
    if head == "not yet classified":
        return None
    sub_name = None
    if ARROW in head:
        type_name, sub_name = head.split(ARROW, 1)
        type_name, sub_name = type_name.strip(), sub_name.strip()
    else:
        type_name = head.strip()
    traits_text = traits_text.strip()
    if traits_text == "none":
        traits = []
    else:
        traits = [t.strip() for t in traits_text.split(", ")]
    return type_name, sub_name, traits


def workflows_lines_parsed(status):
    out = []
    for line in status.split("\n"):
        if not line.startswith("Workflows: "):
            continue
        parsed = parse_workflows_tail(line[len("Workflows: "):])
        if parsed is not None:
            out.append(parsed)
    return out


def needs_workflow_read(module_keys, status):
    if workflows_lines_parsed(status):
        return True
    for key in module_keys:
        if os.path.isfile(phase_module_installed(key)):
            return True
    return False


def pointer_paths_from_module(text, wc):
    """Valid relative paths from Sub-files:/Variants: lines, in file order."""
    lines = wc.file_lines(text)
    paths, seen = [], set()
    fence = None
    for line in lines:
        if fence is None:
            opened = wc.opening_fence(line)
            if opened is not None:
                fence = opened
                continue
        elif wc.closing_fence(line, fence[0], fence[1]):
            fence = None
            continue
        else:
            continue
        for prefix in ("Sub-files: ", "Variants: "):
            if line.startswith(prefix):
                rest = line[len(prefix):].rstrip()
                for part in rest.split("; "):
                    p = part.rstrip()
                    if POINTER_PATH.match(p) and p not in seen:
                        seen.add(p)
                        paths.append(p)
    return paths


def module_keys_from_heading(wc, heading_line):
    parsed = wc.parse_heading(heading_line)
    if parsed is None:
        return None
    kind, target, _for = parsed
    if kind == "replace":
        return target
    if "." in target:
        return target.split(".", 1)[0]
    return target


def file_touches_phase(wc, text, module_keys):
    spans, _unclosed = wc.heading_spans(text)
    module_set = set(module_keys)
    for heading_line, _body in spans:
        mod = module_keys_from_heading(wc, heading_line)
        if mod is not None and mod in module_set:
            return True
    return False


def conditional_candidates(wc, tables, type_name, sub_name, trait_names):
    """Relative paths under workflow/ in type, sub-type, trait order."""
    paths = []
    row = tables["workflow_by_name"].get(type_name)
    if not row:
        return paths
    type_key = row["Key"]
    paths.append("types/%s.md" % type_key)
    if sub_name:
        sub_row = tables["sub_by_name"].get(sub_name)
        if sub_row:
            paths.append("types/%s/%s.md" % (type_key, sub_row["Key"]))
    trait_keys = []
    for name in trait_names:
        trow = tables["trait_by_name"].get(name)
        if trow:
            trait_keys.append((tables["trait_order"].get(name, 999999), trow["Key"]))
    trait_keys.sort(key=lambda pair: pair[0])
    for _, tkey in trait_keys:
        paths.append("traits/%s.md" % tkey)
    return paths


def collect_conditional_files(wc, tables, module_keys, status, already):
    named = []
    root = workflow_root()
    for type_name, sub_name, trait_names in workflows_lines_parsed(status):
        for rel in conditional_candidates(wc, tables, type_name, sub_name, trait_names):
            if rel in already:
                continue
            path = os.path.join(root, *rel.split("/"))
            if not os.path.isfile(path) or wc.is_link(path):
                continue
            text, _shown, err = wc.read_utf8(path)
            if err:
                continue
            if not file_touches_phase(wc, text, module_keys):
                continue
            already.add(rel)
            named.append(WORKFLOW_PREFIX + rel)
    return named


def pointers_part(status, source):
    phase_raw = (field(status, "Phase") or "").strip()
    phase = phase_raw.split()[0].lower() if phase_raw else ""
    awaiting = (field(status, "Awaiting user on") or "nothing").strip()
    if len(awaiting) > AWAITING_MAX:
        awaiting = awaiting[:AWAITING_MAX] + "... (read it whole in docs/PROJECT_STATUS.md)"
    version = installed_version()
    recorded = re.search(r"[0-9]{4}\.[0-9]{2}\.[0-9]{2}[a-z]?", field(status, "Bridge version") or "")
    recorded = recorded.group(0) if recorded else ""
    if recorded and version != "?" and recorded != version:
        version += "; the status file records %s, so this project is not calibrated to the installed bridge: say so in your next report; /calibrate-bridge is started by the owner, or by the maintainer session's message (rule 57)" % recorded
    waiting = awaiting.lower() not in ("nothing", "none", "", "-")
    out = ["CLAUDE-CURSOR BRIDGE: this folder belongs to a bridge project (bridge %s) and this message is for its supervisor session. "
           "If you are not the project's supervisor (you were not asked to act as supervisor here), ignore this message and the digest. "
           "The context was just %s, and a compaction keeps only the first part of your instructions; the core digest is re-injected beside this message." % (version, source),
           "",
           "PROJECT STATE: Phase: %s. Awaiting user on: %s." % (phase_raw or "unknown", awaiting)]
    module_keys = PHASE_MODULES.get(phase)
    printed_paths = set()
    read_error = None
    wc, tables = None, None
    if module_keys is not None and needs_workflow_read(module_keys, status):
        wc, tables, read_error = load_workflow_check()
    if module_keys:
        out.append("BEFORE YOUR NEXT ACTION, re-read these files whole with the Read tool:")
        for key in module_keys:
            line = "  - %s%s.md" % (PHASE_PREFIX, key)
            if key == "project-end" and phase in ("building", "changing"):
                line += " " + PROJECT_END_NOTE
            out.append(line)
            printed_paths.add(PHASE_PREFIX + key + ".md")
            if read_error is None and wc is not None:
                mod_path = phase_module_installed(key)
                if os.path.isfile(mod_path):
                    text, _shown, err = wc.read_utf8(mod_path)
                    if err is None:
                        for rel in pointer_paths_from_module(text, wc):
                            shown = PHASE_PREFIX + rel
                            if shown not in printed_paths:
                                printed_paths.add(shown)
                                out.append("  - %s" % shown)
        if read_error is not None:
            out.append(read_error)
        if read_error is None and wc is not None and tables is not None:
            for path in collect_conditional_files(wc, tables, module_keys, status, printed_paths):
                out.append("  - %s" % path)
    elif phase:
        out.append("BEFORE YOUR NEXT ACTION, re-read the procedure for phase '%s' (not in the hook's map: see ## The phase modules in ~/.claude/commands/supervisor.md)." % phase_raw)
    for conv in PHASE_CONVENTIONS.get(phase, []):
        out.append("  - and %s, whole" % conv)
    out.append("Then read docs/PROJECT_STATUS.md and docs/INVENTORY.md whole (rule 41).")
    if source == "forked from another session":
        out.append("This session is a COPY; the original may still be the supervisor. Do not continue the loop unless the owner says this session is the supervisor now.")
    elif waiting:
        out.append("The status file says you are WAITING FOR THE OWNER on: %s. Do not continue the loop; wait for their word, and clear the line when they give it." % awaiting)
    else:
        out.append("Continue from where the status file says the work is.")
    return "\n".join(out)


def digest_part(digest, version):
    head = "CLAUDE-CURSOR BRIDGE core digest (bridge %s) - the condensed core of ~/.claude/commands/supervisor.md; the full text governs:" % version
    return head + "\n\n" + (digest if digest else "(no digest found in supervisor.md; re-read the whole file)")


def main():
    argv = sys.argv[1:]
    part = "all"
    if "--part" in argv:
        i = argv.index("--part")
        part = argv[i + 1] if i + 1 < len(argv) else "all"
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}
    if not isinstance(data, dict):
        data = {}
    cwd = data.get("cwd") or os.getcwd()
    status = read_status(cwd)
    if status is None:
        return 0
    sv = supervisor_path()
    if not os.path.isfile(sv):
        return 0
    source = {"compact": "compacted", "resume": "resumed", "fork": "forked from another session"}.get(data.get("source"), "compacted or resumed")
    digest = read_digest(sv)
    version = installed_version()
    parts = []
    if part in ("pointers", "all"):
        parts.append(cap(pointers_part(status, source), MAX_OUTPUT, "the section pointers"))
    if part in ("digest", "all"):
        parts.append(cap(digest_part(digest, version), MAX_OUTPUT, "the digest"))
    sys.stdout.write("\n\n".join(parts) + "\n")
    return 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):      # Claude Code reads the hook's output as UTF-8
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8", errors="backslashreplace")
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
