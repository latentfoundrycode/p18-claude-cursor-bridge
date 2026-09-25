#!/usr/bin/env python3
"""inventory-check: is the project's current-state record current, bounded, and complete?

  python inventory-check.py [--inventory docs/INVENTORY.md] [--status docs/PROJECT_STATUS.md]
                            [--changes docs/CHANGES.md] [--max-lines 120] [--max-chars 12000]

Run from the Workspace root. Deterministic; reads only. Checks:

 1. STATUS TOO LONG   docs/PROJECT_STATUS.md exceeds its cap. It is current state, rewritten
                      in place; history lives in CHANGES.md and git.
 2. SHAPE             docs/INVENTORY.md has the four sections - Features, Resources, Decisions,
                      Deferred - each with its table header, and no data row has an empty cell.
 3. NOT ABSORBED      every docs/CHANGES.md entry newer than the inventory's
                      "Reflected through:" heading is listed (the inventory has not absorbed it).
                      CHANGES.md is newest-first; if its headings start with ISO dates in
                      ascending order, oldest-first is detected and handled.
 4. UNLISTED          an environment variable the tracked code reads, a key in a committed
                      .env example, or a repository secret a CI workflow uses, that the
                      Resources table does not name. OS / CI / toolchain variables are ignored.
 5. SECRET VALUE      a Resources cell holds something that looks like a secret value. The
                      inventory names secrets and says where they live; it never holds one.

Notes (never fail): a Resources name that no code reads (fine for an account or a tool; stale
otherwise). Exit 0 = OK, 1 = at least one failure. ASCII output only.
"""
import argparse
import os
import re
import subprocess
import sys

SECTIONS = {
    "Features":  ["Feature", "What it does", "Where", "Tests", "Since"],
    "Resources": ["Name", "Kind", "Where it lives", "Used by", "Provided"],
    "Decisions": ["Decision", "Reason", "Settled", "Revisit only if"],
    "Deferred":  ["Item", "Why deferred", "Since", "Owner decision needed"],
}

CODE_EXT = {".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".ps1", ".psm1", ".cs",
            ".rs", ".go", ".java", ".kt", ".rb", ".php", ".vue", ".svelte"}
ENV_PATTERNS = [
    r"""(?:getenv|environ\.get|environ\.setdefault|env\.get|os\.LookupEnv|os\.Getenv|GetEnvironmentVariable|env::var(?:_os)?|System\.getenv|ENV\.fetch)\s*\(\s*[@$]?["']([A-Za-z_][A-Za-z0-9_]{2,})["']""",
    r"""environ\s*\[\s*["']([A-Za-z_][A-Za-z0-9_]{2,})["']\s*\]""",
    r"""ENV\s*\[\s*["']([A-Za-z_][A-Za-z0-9_]{2,})["']\s*\]""",
    r"""process\.env\.([A-Za-z_][A-Za-z0-9_]{2,})""",
    r"""process\.env\s*\[\s*["']([A-Za-z_][A-Za-z0-9_]{2,})["']\s*\]""",
    r"""import\.meta\.env\.([A-Za-z_][A-Za-z0-9_]{2,})""",
    r"""\$env:([A-Za-z_][A-Za-z0-9_]{2,})""",
]
ENV_RX = [re.compile(p) for p in ENV_PATTERNS]
SECRET_RX = re.compile(r"\$\{\{\s*secrets\.([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")
DOTENV_RX = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=", re.M)
EXAMPLE_ENV = re.compile(r"(^|/)\.env\.(example|sample|template|dist)$|(^|/)env\.example$", re.I)

IGNORED = {
    "PATH", "PATHEXT", "HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "PROGRAMDATA",
    "PROGRAMFILES", "PROGRAMFILES(X86)", "SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "COMSPEC",
    "TEMP", "TMP", "TMPDIR", "PWD", "OLDPWD", "USER", "USERNAME", "LOGNAME", "SHELL", "TERM",
    "LANG", "LANGUAGE", "LC_ALL", "LC_CTYPE", "OS", "HOSTNAME", "COMPUTERNAME", "CI",
    "NO_COLOR", "FORCE_COLOR", "COLUMNS", "LINES", "NODE_ENV", "VIRTUAL_ENV", "CONDA_PREFIX",
    "PYTHONPATH", "PYTHONHOME", "PYTHONIOENCODING", "PYTHONUTF8", "PYTHONDONTWRITEBYTECODE",
    "PYTHONUNBUFFERED", "PYTEST_CURRENT_TEST", "XDG_CONFIG_HOME", "XDG_DATA_HOME",
    "XDG_CACHE_HOME", "XDG_RUNTIME_DIR", "XDG_STATE_HOME", "GITHUB_TOKEN", "EDITOR", "VISUAL", "PAGER",
    "NUMBER_OF_PROCESSORS", "PROCESSOR_ARCHITECTURE",
}
IGNORED_PREFIXES = ("GITHUB_", "RUNNER_", "ACTIONS_", "npm_", "NPM_CONFIG_", "PIP_", "UV_",
                    "CURSOR_", "CLAUDE_", "ANTHROPIC_LOG")

SECRET_VALUE_RX = [
    re.compile(p) for p in (
        r"\bsk-[A-Za-z0-9_\-]{16,}", r"\bsk_live_[A-Za-z0-9]{10,}", r"\bghp_[A-Za-z0-9]{20,}",
        r"\bgithub_pat_[A-Za-z0-9_]{20,}", r"\bxox[abprs]-[A-Za-z0-9\-]{10,}",
        r"\bAKIA[0-9A-Z]{16}\b", r"\bAIza[0-9A-Za-z_\-]{30,}", r"\bhf_[A-Za-z0-9]{20,}",
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    )
]
LONG_TOKEN = re.compile(r"(?<![A-Za-z0-9_/\\.\-])([A-Za-z0-9_\-]{32,})(?![A-Za-z0-9_/\\.\-])")


def read(path):
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        return f.read()


def looks_secret(cell):
    if any(rx.search(cell) for rx in SECRET_VALUE_RX):
        return True
    for m in LONG_TOKEN.finditer(cell):
        tok = m.group(1)
        if re.fullmatch(r"[A-Z0-9_]+", tok):          # an ENV_VAR_NAME, however long
            continue
        if re.search(r"[0-9]", tok) and re.search(r"[A-Za-z]", tok):
            return True
    return False


def parse_tables(text):
    """Return {section: (header_cells or None, [row_cells...])} for the four sections."""
    out = {}
    current = None
    for line in text.splitlines():
        h = re.match(r"^##\s+(.+?)\s*$", line)
        if h:
            current = h.group(1).strip()
            if current in SECTIONS:
                out[current] = [None, []]
            continue
        if current not in SECTIONS or not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        if out[current][0] is None:
            out[current][0] = cells
        else:
            out[current][1].append(cells)
    return out


def changes_headings(text):
    heads = [m.group(1).strip() for m in re.finditer(r"^##\s+(.+?)\s*$", text, re.M)]
    dates = [re.match(r"(\d{4}-\d{2}-\d{2})", h) for h in heads]
    if len(heads) >= 2 and dates[0] and dates[-1] and dates[0].group(1) < dates[-1].group(1):
        heads = list(reversed(heads))          # oldest-first log: normalise to newest-first
    return heads


def tracked_files():
    p = subprocess.run(["git", "ls-files", "-z"], capture_output=True)
    if p.returncode != 0:
        return None
    return [f for f in p.stdout.decode("utf-8", "replace").split("\0") if f]


def env_reads(files):
    found = {}
    for f in files:
        norm = f.replace("\\", "/")
        if norm.startswith((".claude/", ".cursor/")) or "/node_modules/" in norm:
            continue
        ext = os.path.splitext(norm)[1].lower()
        is_wf = norm.startswith(".github/workflows/") and ext in (".yml", ".yaml")
        is_example = bool(EXAMPLE_ENV.search(norm))
        if not (ext in CODE_EXT or is_wf or is_example):
            continue
        try:
            text = read(f)
        except OSError:
            continue
        hits = []
        if is_example:
            hits = [(m.group(1), m.start()) for m in DOTENV_RX.finditer(text)]
        elif is_wf:
            hits = [(m.group(1), m.start()) for m in SECRET_RX.finditer(text)]
        else:
            for rx in ENV_RX:
                hits += [(m.group(1), m.start()) for m in rx.finditer(text)]
        for name, pos in hits:
            if name in IGNORED or name.upper() in IGNORED or name.startswith(IGNORED_PREFIXES):
                continue
            if name not in found:
                found[name] = "%s:%d" % (norm, text.count("\n", 0, pos) + 1)
    return found


def main():
    ap = argparse.ArgumentParser(description="Check the project's current-state record.")
    ap.add_argument("--inventory", default="docs/INVENTORY.md")
    ap.add_argument("--status", default="docs/PROJECT_STATUS.md")
    ap.add_argument("--changes", default="docs/CHANGES.md")
    ap.add_argument("--max-lines", type=int, default=120)
    ap.add_argument("--max-chars", type=int, default=12000)
    a = ap.parse_args()
    fails, notes = [], []

    # 1. status cap
    if os.path.exists(a.status):
        st = read(a.status)
        n_lines, n_chars = len(st.splitlines()), len(st)
        if n_lines > a.max_lines or n_chars > a.max_chars:
            fails.append("STATUS TOO LONG: %s is %d lines / %d chars (cap %d / %d). Rewrite it as "
                         "current state; move product facts to the inventory and history to "
                         "docs/archive/." % (a.status, n_lines, n_chars, a.max_lines, a.max_chars))
        else:
            notes.append("status: %d lines / %d chars (cap %d / %d)" % (n_lines, n_chars, a.max_lines, a.max_chars))
    else:
        notes.append("status: %s not found (skipped)" % a.status)

    # 2. shape
    if not os.path.exists(a.inventory):
        fails.append("MISSING: %s does not exist" % a.inventory)
        inv_text, tables = "", {}
    else:
        inv_text = read(a.inventory)
        tables = parse_tables(inv_text)
        for sec, cols in SECTIONS.items():
            if sec not in tables:
                fails.append("SHAPE: section '## %s' missing" % sec)
                continue
            header, rows = tables[sec]
            if header is None:
                fails.append("SHAPE: '## %s' has no table header (%s)" % (sec, " | ".join(cols)))
                continue
            if len(header) != len(cols):
                fails.append("SHAPE: '## %s' header has %d columns, expected %d (%s)"
                             % (sec, len(header), len(cols), " | ".join(cols)))
            for i, r in enumerate(rows, 1):
                if len(r) != len(header) or any(not c for c in r):
                    fails.append("SHAPE: '## %s' row %d has an empty or missing cell: %s"
                                 % (sec, i, " | ".join(r)[:120]))

    # 3. absorbed change-log entries
    m = re.search(r"^Reflected through:\s*(.+?)\s*$", inv_text, re.M)
    if inv_text and not m:
        fails.append("SHAPE: no 'Reflected through:' line")
    if m and os.path.exists(a.changes):
        marker = m.group(1).strip().strip("`")
        heads = changes_headings(read(a.changes))
        if marker.lower() == "none":
            pending = heads
        elif marker in heads:
            pending = heads[:heads.index(marker)]
        else:
            pending = None
            fails.append("NOT ABSORBED: 'Reflected through: %s' matches no heading in %s"
                         % (marker[:80], a.changes))
        if pending:
            fails.append("NOT ABSORBED: %d change-log entr%s newer than the inventory:"
                         % (len(pending), "y" if len(pending) == 1 else "ies"))
            for h in pending[:15]:
                fails.append("    ## " + h[:110])
            if len(pending) > 15:
                fails.append("    ... and %d more" % (len(pending) - 15))
    elif m:
        notes.append("changes: %s not found (absorption not checked)" % a.changes)

    # 4 + 5. resources
    listed = set()
    for r in (tables.get("Resources") or [None, []])[1]:
        if r:
            listed.update(re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", r[0]))
            for c in r:
                if looks_secret(c):
                    fails.append("SECRET VALUE: a Resources cell looks like a secret value (row '%s'). "
                                 "Name the secret and where it lives; never the value." % r[0][:40])
                    break
    files = tracked_files()
    if files is None:
        notes.append("resources: not a git repository (reads not scanned)")
    else:
        reads = env_reads(files)
        for name in sorted(reads):
            if name not in listed:
                fails.append("UNLISTED: %s (read at %s) is not in Resources" % (name, reads[name]))
        unread = sorted(n for n in listed if re.fullmatch(r"[A-Z][A-Z0-9_]{2,}", n) and n not in reads)
        if unread:
            notes.append("resources listed but read by no tracked code (fine for accounts/tools): "
                         + ", ".join(unread[:12]))

    for n in notes:
        print("note: " + n)
    for f in fails:
        print(f)
    print("RESULT: %s" % ("OK" if not fails else "%d problem(s)" % sum(1 for f in fails if not f.startswith("    "))))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
