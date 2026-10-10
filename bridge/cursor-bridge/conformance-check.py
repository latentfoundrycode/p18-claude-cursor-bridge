#!/usr/bin/env python3
"""conformance-check: does this project's configuration carry the floors the bridge requires?

  python ~/.claude/cursor-bridge/conformance-check.py [<project root or Workspace>] [--screens] [--installable] [--offline] [--quiet]

Why (plan review R4): the bridge added floors over time (the security scanners in the gate,
SHA-pinned actions, the workspace boundary, the records), and nothing compared a project
configured before a floor existed with what the bridge now requires; the video factory ran
its gate with no scanner and actions pinned by tag while the Project Summary said the floor
applied everywhere. This check reads the project's files and reports, per floor, OK, MISSING
or NOTE. It runs at every calibration and every reflection point; each MISSING is a
calibration item, applied as configuration work in the next stage. It never changes anything.

What it checks, with the file it reads (the 0b review corrected several of these):
  - the gate workflows (.github/workflows/*.yml), step by step: a step runs Semgrep,
    OSV-Scanner and Socket; a scanner step guarded by `if:` is MISSING (it is skipped
    silently when its condition is false); Semgrep runs the bridge rules or the Pro engine
    (`semgrep ci`), not public rulesets alone (Cursor-Project-Configuration.md 5c); a scanner
    without a pinned version is a NOTE (rule 14); every `uses:` is pinned by a 40-character
    commit; the runner is Linux (a note otherwise);
  - on GitHub, read-only through `gh` unless --offline: the default branch has a required
    status check (N6), and the repository's visibility (a public repository is a NOTE);
  - the workspace boundary (.cursor/rules/workspace-boundary.mdc, the boundary-check hook in
    .cursor/hooks.json), the windowless check in the hooks (rule 24), and the frozen
    secure-coding rule (.cursor/rules/secure-coding.mdc);
  - a lockfile beside each manifest (package.json, pyproject.toml), and a transitive lock for
    a root requirements.txt (direct pins alone are not a lock; KP-018);
  - the records: docs/PROJECT_STATUS.md, INVENTORY.md, REQUIREMENTS.md, RUN_PARAMETERS.md,
    ROSTER.json, DESIGN.md (a design under other names is a NOTE naming them), and
    docs/diagrams/INDEX.md (missing = a diagram retrofit item);
  - with --screens (or a docs/mockups folder): the design detector in the gate;
  - release A1b: a spending limit recorded for every key, account or provider that can charge
    (the inventory's Resources rows); the inventory's `Development data:` decision; every
    adapter of a listed provider tested against recorded replies (the providers from the
    inventory's chargeable rows, one word each; the adapters among the project's own tracked
    files, naming the provider in a string of code, not a comment; the evidence a cassette or
    fixture file the adapter's test loads, a recording library, or a test that names cassettes
    in a repository that tracks a cassettes folder); `run/` ignored (a NOTE);
  - release A2: project.json at the Workspace root (name, purpose, kind, version, state), its
    keys and its phase against the status file;
  - with --installable (or docs/cli-reference.json present): the CLI reference and a check
    of it, in CI or in the test suite;
  - secrets within the builder's reach: variable NAMES in Workspace/.env, .env.* (not the
    examples) and <folder>/.env that look like account keys or tokens are MISSING; local
    service passwords the tests need (POSTGRES_PASSWORD, MINIO_ROOT_PASSWORD, ...) are a
    NOTE; values are never read or printed (KP-032); the advice is a key file outside the
    Workspace, never the Windows user environment; key-like variable NAMES in the session's
    own environment are a NOTE (the launcher withholds them from builder and reviewer runs);
  - the private memory notes Claude Code keeps for this project (names only; calibration
    step 2b reviews them, rule 41);
  - the recorded bridge version against the installed one (calibration due).
Exit 0 = every floor present; 1 = at least one MISSING; 2 = not a workspace.
ASCII-only on purpose (cp1252 consoles). Never writes.
"""
import glob
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
SECRET_NAME = re.compile(r"(TOKEN|SECRET|KEY|PASSWORD|PASSWD|CREDENTIAL|API_?KEY)", re.I)
LOCAL_SERVICE = re.compile(r"^(POSTGRES|PG|MYSQL|MARIADB|MONGO|REDIS|MINIO|RABBITMQ|CLICKHOUSE|ELASTIC|OPENSEARCH|NEO4J|DB|DATABASE|LOCAL|DEV|TEST)[A-Z0-9_]*(PASSWORD|PASSWD|PASS|SECRET)$", re.I)
ENV_SECRET = re.compile(r"((^|_)TOKENS?(_|$)|(^|_)SECRETS?(_|$)|PASSWORD|PASSWD|PASSPHRASE|CREDENTIAL|API_?KEY|ACCESS_?KEY|PRIVATE_?KEY|_KEYS?$)")  # as bridge_env.SECRET_LIKE
LOCATION_NAME = re.compile(r"_(PATH|DIR|FILE|FOLDER|URL)$")  # where a store is, not a secret
SCANNERS = (("Semgrep", r"\bsemgrep\b"), ("OSV-Scanner", r"osv-scanner"), ("Socket", r"\bsocket\b"))
GH_TIMEOUT = 25


def read(path):
    try:
        with open(path, encoding="utf-8-sig", errors="replace") as f:
            return f.read()
    except OSError:
        return None


def resolve_workspace(path):
    """The Workspace folder for a path that may be the project root (where sessions start)
    or the Workspace itself."""
    p = os.path.abspath(path)
    for cand in (p, os.path.join(p, "Workspace")):
        if os.path.isdir(os.path.join(cand, "docs")) or os.path.isdir(os.path.join(cand, ".git")):
            return cand
    return None


def workflow_steps(text):
    """Each step of a workflow as (step text, guarded by if:), by indentation under `steps:`."""
    steps, cur, indent, in_steps = [], [], None, False
    for line in text.splitlines():
        stripped = line.lstrip()
        if re.match(r"^steps:\s*$", stripped):
            in_steps, indent, cur = True, None, []
            continue
        if not in_steps:
            continue
        if stripped and not line.startswith(" ") and not line.startswith("\t"):
            in_steps = False                     # back at the top level (another job key or job)
            if cur:
                steps.append(cur)
            cur = []
            continue
        if stripped.startswith("- "):
            this_indent = len(line) - len(stripped)
            if indent is None:
                indent = this_indent
            if this_indent == indent:
                if cur:
                    steps.append(cur)
                cur = [stripped[2:]]
                continue
            if this_indent < indent:
                in_steps = False
                if cur:
                    steps.append(cur)
                cur = []
                continue
        if cur is not None and (indent is None or (len(line) - len(stripped)) > indent or not stripped):
            cur.append(stripped)
    if cur:
        steps.append(cur)
    out = []
    for s in steps:
        body = "\n".join(s)
        guarded = any(re.match(r"^if:\s*\S", l) for l in s)
        # what the step executes: its run:/uses: lines and the continuation lines of a block scalar
        commands = "\n".join(l for l in s if re.match(r"^(run|uses):", l) or not re.match(r"^[A-Za-z_-]+:", l))
        out.append((body, guarded, commands))
    return out


def gh(args, cwd):
    try:
        p = subprocess.run(["gh"] + args, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=GH_TIMEOUT, creationflags=NO_WINDOW)
    except (OSError, subprocess.TimeoutExpired) as e:
        return None, str(e)[:120]
    if p.returncode != 0:
        return None, (p.stderr.strip() or p.stdout.strip())[:160]
    return p.stdout, None


def git_ignored(ws, rel):
    try:
        p = subprocess.run(["git", "-c", "core.fsmonitor=false", "check-ignore", "-q", rel], cwd=ws, capture_output=True, timeout=GH_TIMEOUT, creationflags=NO_WINDOW)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return p.returncode == 0


def tracked_files(ws):
    """The project's own files (git ls-files), or a walk that skips environments and build output."""
    try:
        p = subprocess.run(["git", "-C", ws, "-c", "core.fsmonitor=false", "ls-files", "-z"], capture_output=True, timeout=60, creationflags=NO_WINDOW)
        if p.returncode == 0:
            return [x.decode("utf-8", "replace") for x in p.stdout.split(b"\0") if x]
    except (OSError, subprocess.TimeoutExpired):
        pass
    out = []
    for dirpath, dirs, names in os.walk(ws):
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules", ".venv", "venv", "venvs", "env", "site-packages", "__pycache__", "dist", "build", "run", "Worktrees")
                   and not os.path.isfile(os.path.join(dirpath, d, "pyvenv.cfg"))]
        for n in names:
            out.append(os.path.relpath(os.path.join(dirpath, n), ws).replace("\\", "/"))
    return out


LIMIT_RECORDED = re.compile(r"\blimit\b[^$\u20ac\u00a3\d\n|]{0,25}([$\u20ac\u00a3]\s*\d|\d+(\.\d+)?\s*(USD|EUR|GBP|CHF)\b)|no spend possible", re.I)   # an amount near "limit", or the words; "not set yet" is not recorded
CANNOT_CHARGE = re.compile(r"\blocal (service|development|postgres|minio|store)\b|throwaway|the product's own|own (per[- ]instance )?token|per[- ]instance|generated per", re.I)
KIND_CANNOT_CHARGE = re.compile(r"\b(store|files?|registration|mcp)\b", re.I)   # a store, model files, a registration: nothing to charge
GENERIC_WORDS = {"api", "key", "keys", "token", "tokens", "secret", "secrets", "account", "access", "id", "user", "password", "pass", "file",
                 "store", "the", "and", "of", "for", "rule", "judge", "repo", "github", "provider", "app", "dev", "test", "local", "root",
                 "url", "host", "endpoint", "login", "credential", "credentials", "model", "models", "files"}
SYNONYMS = {"hf": ("hf", "huggingface"), "gh": ("gh", "github"), "oai": ("oai", "openai"), "gcp": ("gcp", "google")}
EVIDENCE_RX = re.compile(r"\bvcr\b|\brespx\b|responses\.activate|\bnock\b|\bmsw\b|(cassettes?|fixtures?|recorded|recordings|replies|contracts?)[/\\][\w.-]+\.(json|ya?ml|har|txt)\b", re.I)


def chargeable_rows(sections, words):
    """The inventory's Resources rows that can charge the owner: a key, account, provider or API
    that is not a local service's login, the product's own token, a test-only value, a store,
    model files, a registration, a setting or the record of a limit. [(cells, name)]"""
    rows = []
    for cells in sections.get("Resources", []):
        if len(cells) < 2 or not re.search(r"secret|account|api|provider|external|key|token", cells[1], re.I) or re.search(r"test-only|setting", cells[1], re.I):
            continue
        name = cells[0].strip("`* ")
        if re.search(r"\blimit\b", name, re.I):
            continue                                       # the row IS the limit, not a key
        idents = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", name)
        if any(LOCAL_SERVICE.match(i) or i.split("_")[0].lower() in words for i in idents):
            continue                                       # every name in the cell is looked at
        if KIND_CANNOT_CHARGE.search(name + " " + cells[1]) or CANNOT_CHARGE.search(" ".join(cells)):
            continue
        rows.append((cells, name))
    return rows


def provider_words(rows):
    """{word: row name}: one word per chargeable row, the one that identifies its adapter: the
    first segment of a key's name (SOCKET of SOCKET_CLI_API_TOKEN), else the provider's own
    name (OpenRouter of "OpenRouter (rule judge)")."""
    found = {}
    for cells, name in rows:
        key = re.match(r"[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+", name)
        if key:
            w = key.group(0).split("_")[0].lower()
        else:
            ws = [x.lower() for x in re.findall(r"[A-Za-z][A-Za-z0-9]*", name) if x.lower() not in GENERIC_WORDS]
            w = ws[0] if ws else ""
        if len(w) >= 2 and w not in GENERIC_WORDS:
            found.setdefault(w, name[:40])
    return found


def code_strings(text):
    """The source without its docstrings and comments, lowercased: where a host or a key name
    would be written."""
    text = re.sub(r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'', "", text)
    text = re.sub(r"/\*[\s\S]*?\*/", "", text)
    text = re.sub(r"(^|[ \t])(#|//)[^\n]*", "", text, flags=re.M)
    return text.lower()


def names_provider(text, providers):
    """The providers a source file names, as a whole word, in a string literal of its code (a
    host, a key name, a service name); never in a docstring or a comment."""
    low = code_strings(text)
    hits = []
    for w in providers:
        for alt in SYNONYMS.get(w, (w,)):
            if re.search(r"""["'`][^"'`\n]*(?<![a-z0-9])%s(?![a-z0-9])""" % re.escape(alt), low):
                hits.append(w)
                break
    return hits


def status_field(ws, name):
    """`<name>: value` from docs/PROJECT_STATUS.md, in any of its markdown spellings."""
    text = read(os.path.join(ws, "docs", "PROJECT_STATUS.md")) or ""
    m = re.search(r"^[\s*_-]*%s[*_]*\s*:[*_\s`]*([^`\n]+)" % re.escape(name), text, re.M | re.I)
    return m.group(1).strip() if m else None


def project_words(ws):
    """Words of the project's own name (the folder above Workspace), to tell the product's
    own tokens (REANGLE_API_TOKEN) from account keys."""
    return set(w for w in re.findall(r"[a-z]{4,}", os.path.basename(os.path.dirname(ws)).lower()) if w not in ("prototype", "project", "workspace"))


def memory_dirs(ws):
    """Claude Code's memory folders for the project root and the Workspace (names only)."""
    home = os.path.expanduser("~")
    out = []
    for folder in (os.path.dirname(ws), ws):
        encoded = re.sub(r"[:\\/]", "-", folder)
        d = os.path.join(home, ".claude", "projects", encoded, "memory")
        if os.path.isdir(d):
            notes = sorted(n for n in os.listdir(d) if n.endswith(".md") and n != "MEMORY.md")
            out.append((d, notes))
    return out


def main():
    argv = sys.argv[1:]
    quiet = "--quiet" in argv
    screens = "--screens" in argv
    installable = "--installable" in argv
    offline = "--offline" in argv
    positional = [a for a in argv if not a.startswith("--")]
    ws = resolve_workspace(positional[0] if positional else os.getcwd())
    if ws is None:
        print("conformance-check: %s is not a project workspace or root (no docs/ and no .git/ here or in Workspace/)" % os.path.abspath(positional[0] if positional else os.getcwd()))
        return 2
    results = []                                   # (verdict, floor, detail)

    def add(verdict, floor, detail=""):
        results.append((verdict, floor, detail))

    # --- the gate workflows, step by step
    workflows = sorted(glob.glob(os.path.join(ws, ".github", "workflows", "*.yml")) + glob.glob(os.path.join(ws, ".github", "workflows", "*.yaml")))
    wf_text = "\n".join(read(p) or "" for p in workflows)
    steps = []
    for p in workflows:
        steps.extend(workflow_steps(read(p) or ""))
    if not workflows:
        add("MISSING", "CI gate", "no workflow under .github/workflows/; the merge gate needs a required check")
    else:
        for name, pattern in SCANNERS:
            hits = [(cmds, guarded) for body, guarded, cmds in steps if re.search(pattern, cmds, re.I)]
            if not hits:
                add("MISSING", "%s in the gate" % name, "the security floor (N8) rides the required CI check")
                continue
            if all(g for _, g in hits):
                add("MISSING", "%s in the gate" % name, "the step is guarded by `if:` and skipped silently when its condition is false; make it unconditional (the token is a repository secret)")
                continue
            add("OK", "%s in the gate" % name)
            # the version may sit in the step that installs the scanner rather than the one that runs it
            scanner_lines = [l for l in wf_text.splitlines() if re.search(pattern, l, re.I)]
            if not any(re.search(r"(==\s*\d|@v?\d|@[0-9a-f]{40}|version:\s*['\"]?\d|/v?\d+\.\d+(\.\d+)?/)", l) for l in scanner_lines):
                add("NOTE", "%s version pinned" % name, "no version where the step installs or runs it; pin it (rule 14: never auto-adopt a tool update)")
            if any(re.search(r"\bif\s+\[\[?\s*-[nz]\s+\"?\$\{?[A-Z0-9_]*(TOKEN|KEY|SECRET)", body) for body, _ in hits):
                add("NOTE", "%s step guards itself" % name, "its script skips the scan when the token variable is empty; true only while the repository secret exists")
        sem = [cmds for body, _, cmds in steps if re.search(r"\bsemgrep\b", cmds, re.I)]
        if sem:
            if any(re.search(r"semgrep(==\S+)?\s+ci\b", b) or "bridge-rules" in b or re.search(r"--config\s+\.semgrep", b) for b in sem):
                add("OK", "Semgrep bridge rules or Pro engine")
            else:
                add("MISSING", "Semgrep bridge rules or Pro engine", "Semgrep runs public rulesets only; the floor is `.semgrep/bridge-rules.yml` or `semgrep ci` (Cursor-Project-Configuration.md 5c, KP-001)")
        unpinned = sorted(set(m.group(1) for m in re.finditer(r"uses:\s*([^\s#]+@[^\s#]+)", wf_text) if not re.search(r"@[0-9a-f]{40}$", m.group(1))))
        if unpinned:
            add("MISSING", "CI actions pinned by commit", "pinned by tag only: " + ", ".join(unpinned[:6]) + (" ..." if len(unpinned) > 6 else ""))
        else:
            add("OK", "CI actions pinned by commit")
        if re.search(r"runs-on:\s*windows", wf_text, re.I):
            add("NOTE", "Runner OS", "a Windows runner counts double against the Actions allowance; the floor runs on Linux unless the build needs Windows")
        if screens or os.path.isdir(os.path.join(ws, "docs", "mockups")):
            if re.search(r"impeccable", wf_text, re.I):
                add("OK", "Design detector in the gate")
            else:
                add("MISSING", "Design detector in the gate", "the project has screens (N7); `npx impeccable@<pinned> detect` belongs in the gate")

    # --- the repository on GitHub (read-only)
    if offline:
        add("NOTE", "Required check on the default branch", "not checked (--offline)")
    else:
        out, err = gh(["repo", "view", "--json", "nameWithOwner,visibility,defaultBranchRef"], ws)
        if out is None:
            add("NOTE", "Required check on the default branch", "cannot verify through gh (%s)" % (err or "no output"))
        else:
            try:
                info = json.loads(out)
                nwo = info["nameWithOwner"]
                branch = (info.get("defaultBranchRef") or {}).get("name") or "main"
                if str(info.get("visibility", "")).lower() == "public":
                    add("NOTE", "Repository visibility", "%s is public: the diffs, briefs and records are readable by anyone (plan review R4)" % nwo)
                checks, err2 = gh(["api", "repos/%s/branches/%s/protection/required_status_checks" % (nwo, branch)], ws)
                if checks is None:
                    add("MISSING", "Required check on the default branch", "no branch protection with a required status check on %s (%s); N6 needs the gate job required" % (branch, (err2 or "")[:80]))
                else:
                    contexts = json.loads(checks).get("contexts") or [c.get("context") for c in json.loads(checks).get("checks") or []]
                    if contexts:
                        add("OK", "Required check on the default branch (%s)" % ", ".join(str(c) for c in contexts[:4]))
                    else:
                        add("MISSING", "Required check on the default branch", "branch protection exists but requires no status check; N6 needs the gate job required")
            except (ValueError, KeyError, TypeError) as e:
                add("NOTE", "Required check on the default branch", "cannot read gh's answer (%s)" % e)

    # --- the builder's configuration
    for floor, rel, detail in (
        ("Workspace boundary rule", os.path.join(".cursor", "rules", "workspace-boundary.mdc"), "the builder's always-on boundary rule (rule 22)"),
        ("Secure-coding rule", os.path.join(".cursor", "rules", "secure-coding.mdc"), "the frozen ASVS-derived rule the builder self-applies (N8)"),
    ):
        add("OK" if os.path.isfile(os.path.join(ws, rel)) else "MISSING", floor, "" if os.path.isfile(os.path.join(ws, rel)) else detail)
    hooks = read(os.path.join(ws, ".cursor", "hooks.json")) or ""
    add("OK" if "boundary-check" in hooks else "MISSING", "Boundary-check hook", "" if "boundary-check" in hooks else ".cursor/hooks.json does not run boundary-check (rule 22)")
    windowless = "windowless-check" in hooks or os.path.isfile(os.path.join(ws, ".cursor", "hooks", "windowless-check.py"))
    add("OK" if windowless else "MISSING", "Windowless check", "" if windowless else "no windowless-check in the hooks; rule 24 puts it in the pre-commit gate")

    # --- lockfiles
    if os.path.isfile(os.path.join(ws, "package.json")):
        locks = [n for n in ("package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb") if os.path.isfile(os.path.join(ws, n))]
        add("OK" if locks else "MISSING", "Lockfile for package.json", "" if locks else "no lockfile; the gate installs from the lock (KP-018)")
    subdirs = [d for d in sorted(os.listdir(ws)) if os.path.isdir(os.path.join(ws, d)) and not d.startswith(".")]
    for sub in subdirs:
        if os.path.isfile(os.path.join(ws, sub, "package.json")):
            locks = [n for n in ("package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb") if os.path.isfile(os.path.join(ws, sub, n))]
            add("OK" if locks else "MISSING", "Lockfile for %s/package.json" % sub, "" if locks else "no lockfile beside the manifest (KP-018)")
    root_req = read(os.path.join(ws, "requirements.txt"))
    editable = set()
    if root_req is not None:
        for line in root_req.splitlines():
            m = re.match(r"^\s*-e\s+\.?/?([A-Za-z0-9_.-]+)", line)
            if m:
                editable.add(m.group(1))
    transitive_locks = [n for n in ("uv.lock", "poetry.lock", "pdm.lock", "requirements.lock") if os.path.isfile(os.path.join(ws, n))]
    transitive_locks += [os.path.basename(p) for p in glob.glob(os.path.join(ws, "requirements*.txt")) if "--hash=" in (read(p) or "")]
    for root_dir in [ws] + [os.path.join(ws, d) for d in subdirs]:
        if os.path.isfile(os.path.join(root_dir, "pyproject.toml")):
            label = "Lockfile for %spyproject.toml" % ("" if root_dir == ws else os.path.basename(root_dir) + "/")
            if root_dir != ws and os.path.basename(root_dir) in editable:
                continue                           # installed editable from the root requirements: the root's lock covers it
            locks = [n for n in ("uv.lock", "poetry.lock", "pdm.lock", "requirements.lock") if os.path.isfile(os.path.join(root_dir, n))]
            locks += [os.path.basename(p) for p in glob.glob(os.path.join(root_dir, "requirements*.txt")) if "--hash=" in (read(p) or "")]
            if not locks and root_dir == ws and transitive_locks:
                locks = transitive_locks
            add("OK" if locks else "MISSING", label, "" if locks else "no transitive lock beside the manifest (uv.lock, poetry.lock, pdm.lock, or hashed requirements; KP-018)")
    if root_req is not None and not os.path.isfile(os.path.join(ws, "pyproject.toml")):
        direct = [l for l in root_req.splitlines() if l.strip() and not l.strip().startswith(("#", "-"))]
        if transitive_locks:
            add("OK", "Transitive lock for requirements.txt")
        else:
            add("MISSING", "Transitive lock for requirements.txt", "requirements.txt pins %d direct dependenc%s and no transitive ones; the gate needs a full lock (uv.lock, or `pip-compile --generate-hashes`; KP-018)" % (len(direct), "y" if len(direct) == 1 else "ies"))

    # --- the records
    for rel, detail in (
        ("docs/PROJECT_STATUS.md", "the bounded status file (rule 41)"),
        ("docs/INVENTORY.md", "the inventory (rule 41)"),
        ("docs/REQUIREMENTS.md", "the requirements register (rule 44)"),
        ("docs/RUN_PARAMETERS.md", "the run parameters (rule 29)"),
        ("docs/ROSTER.json", "the model roster (rule 38)"),
        ("project.json", "the project file: name, purpose, kind (private | commercial), version, state (the owner's requirement of 2026-10-10, release A2; calibration writes it from the status file)"),
    ):
        ok = os.path.isfile(os.path.join(ws, rel))
        if ok and os.path.isdir(os.path.join(ws, ".git")) and git_ignored(ws, rel):
            add("MISSING", rel, "exists but is gitignored: the records are versioned, a reviewer's change to an ignored record leaves no trace and no history (0b review, S3)")
            continue
        add("OK" if ok else "MISSING", rel, "" if ok else detail)
    if os.path.isfile(os.path.join(ws, "project.json")):
        try:
            pj = json.loads(read(os.path.join(ws, "project.json")) or "")
        except ValueError:
            pj = None
        if not isinstance(pj, dict) or not all(k in pj for k in ("name", "purpose", "kind", "version", "state")):
            add("NOTE", "project.json keys", "the project file is not an object with name, purpose, kind, version and state")
        elif pj.get("kind") not in ("private", "commercial"):
            add("NOTE", "project.json kind", "kind is %r; private or commercial" % pj.get("kind"))
        else:
            st = pj.get("state") if isinstance(pj.get("state"), dict) else {}
            phase = str(st.get("phase") or "").lower()
            status_phase = str(status_field(ws, "Phase") or "").lower()
            stale = []
            if status_phase and not status_phase.startswith(phase.split()[0] if phase else "\0"):
                stale.append("its phase (%s) is not the status file's (%s)" % (phase or "none", status_phase))
            inst = (read(os.path.join(HERE, "VERSION")) or "").strip()
            if inst and str(st.get("bridge") or "") != inst:
                stale.append("its bridge version (%s) is not the installed one (%s)" % (st.get("bridge") or "none", inst))
            if not re.match(r"^\d{4}-\d\d-\d\d$", str(st.get("updated") or "")):
                stale.append("its updated date is missing or not YYYY-MM-DD")
            if stale:
                add("NOTE", "project.json state", "; ".join(stale) + ": bring it up to date at this reflection point")
    if os.path.isfile(os.path.join(ws, "docs", "DESIGN.md")):
        add("OK", "docs/DESIGN.md")
    else:
        others = sorted(n for n in (os.listdir(os.path.join(ws, "docs")) if os.path.isdir(os.path.join(ws, "docs")) else []) if n.lower().endswith(".md") and re.search(r"design|architecture", n, re.I))
        if others:
            add("NOTE", "docs/DESIGN.md", "the design exists under other names (%s); the diagram retrofit (plan 8.7) gives it the fixed name or a DESIGN.md that points at them" % ", ".join(others[:5]))
        else:
            add("MISSING", "docs/DESIGN.md", "the design document (rule 45)")
    if os.path.isfile(os.path.join(ws, "docs", "diagrams", "INDEX.md")):
        add("OK", "docs/diagrams/INDEX.md")
    else:
        add("MISSING", "docs/diagrams/INDEX.md", "no diagram index: a diagram retrofit item (restructuring plan 8.7), scheduled at the next natural pause")

    # --- installable software
    if installable or os.path.isfile(os.path.join(ws, "docs", "cli-reference.json")):
        has_ref = os.path.isfile(os.path.join(ws, "docs", "cli-reference.json"))
        add("OK" if has_ref else "MISSING", "docs/cli-reference.json", "" if has_ref else "the generated command reference (rule 32)")
        checked = bool(re.search(r"cli-reference", wf_text))
        where, reads_only = "CI", []
        if not checked:
            for tests_dir in glob.glob(os.path.join(ws, "tests")) + glob.glob(os.path.join(ws, "*", "tests")):
                for p in sorted(glob.glob(os.path.join(tests_dir, "**", "*.py"), recursive=True)):
                    text = read(p) or ""
                    if "cli-reference.json" not in text:
                        continue
                    relp = os.path.relpath(p, ws).replace("\\", "/")
                    # a check regenerates the reference and compares; a test that merely reads the file is not one
                    if re.search(r"assert[^\n]*==|assertEqual|--exit-code|--check|\bcompare", text):
                        checked, where = True, relp
                        break
                    reads_only.append(relp)
                if checked:
                    break
        if checked:
            add("OK", "CLI reference checked (%s)" % where)
        elif reads_only:
            add("MISSING", "CLI reference checked", "%s reads docs/cli-reference.json but nothing compares it with the generator's output (rule 32)" % ", ".join(reads_only[:3]))
        else:
            add("MISSING", "CLI reference checked", "nothing keeps docs/cli-reference.json current: no CI step and no test names it (rule 32)")

    # --- secrets within the builder's reach (names only)
    # Claude Code settings of the project: cursor-agent imports their hooks and plugins, and
    # under Git Bash every builder command is then refused (KP-038)
    claude_dirs = [("MISSING", os.path.join(ws, ".claude"))]
    if os.path.basename(os.path.normpath(ws)).lower() == "workspace":
        claude_dirs.append(("NOTE", os.path.join(os.path.dirname(os.path.normpath(ws)), ".claude")))   # read only when a builder's workspace is the root
    for verdict, d in claude_dirs:
        imported = []
        for name in ("settings.json", "settings.local.json"):
            path = os.path.join(d, name)
            if not os.path.isfile(path):
                continue
            rel = os.path.relpath(path, ws).replace("\\", "/")
            try:
                data = json.loads(read(path))
            except ValueError:
                imported.append("%s (not valid JSON)" % rel)
                continue
            keys = []
            if isinstance(data, dict):
                if data.get("hooks"):
                    keys.append("hooks")
                plugins = data.get("enabledPlugins")
                if isinstance(plugins, dict) and any(plugins.values()):
                    keys.append("enabledPlugins")
            if keys:
                imported.append("%s (%s)" % (rel, ", ".join(keys)))
        if imported:
            add(verdict, "No Claude Code hooks in the project's .claude", "cursor-agent imports them, and under Git Bash every builder and reviewer command is then refused while the run reports success (KP-038): " + "; ".join(imported))

    env_files = [os.path.join(ws, ".env")]
    env_files += [p for p in glob.glob(os.path.join(ws, ".env.*")) if not re.search(r"\.(example|template|sample|dist)$", p, re.I)]
    env_files += [os.path.join(ws, d, ".env") for d in subdirs]
    accounts, locals_, own = [], [], []
    words = project_words(ws)
    for env_path in env_files:
        env_text = read(env_path)
        if env_text is None:
            continue
        rel = os.path.relpath(env_path, ws).replace("\\", "/")
        for line in env_text.splitlines():
            m = re.match(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=", line)
            if not m or not SECRET_NAME.search(m.group(1)):
                continue
            name = m.group(1)
            shown = "%s (%s)" % (name, rel) if rel != ".env" else name
            if LOCAL_SERVICE.match(name):
                locals_.append(shown)
            elif name.split("_")[0].lower() in words:
                own.append(shown)
            else:
                accounts.append(shown)
    if any(os.path.isfile(p) for p in env_files):
        if accounts:
            add("MISSING", "Keys out of the builder's reach", "account keys or tokens within the builder's reach: %s (KP-032): move them to a key file OUTSIDE the Workspace (for example under %%APPDATA%%\\<product>\\) or the product's encrypted store; NOT into the Windows user environment, which hands them to every program the owner starts" % ", ".join(accounts))
        else:
            add("OK", "Keys out of the builder's reach")
        if locals_:
            add("NOTE", "Local service passwords in .env", "%s: passwords of local development services the tests need; keep them non-production, they are not account secrets" % ", ".join(locals_))
        if own:
            add("NOTE", "The product's own tokens in .env", "%s: named after the project, so taken as the product's own per-instance tokens, not an external account; say so in the inventory if that is wrong" % ", ".join(own))

    # --- the inventory's tables, by section (release A1b floors)
    inv = read(os.path.join(ws, "docs", "INVENTORY.md")) or ""
    sections, current = {}, None
    for line in inv.splitlines():
        m = re.match(r"^##\s+(\w+)", line)
        if m:
            current = m.group(1)
            continue
        if current and line.lstrip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if cells and not set("".join(cells)) <= set("-: ") and not (cells[0].lower() in ("name", "decision", "feature", "item")):
                sections.setdefault(current, []).append(cells)
    if inv:
        # a spending limit at every provider, API or account that can charge: its Resources row says so
        unlimited = []
        for cells, name in chargeable_rows(sections, words):
            if LIMIT_RECORDED.search(" ".join(cells)):
                continue
            unlimited.append(name[:40])
        if unlimited:
            add("MISSING", "Spending limit recorded", "%d key(s) or account(s) without a spending limit in the Resources row (`limit $20/month, set <date>`, or `no spend possible`): %s%s; the configuration phase asks the owner to set one at each provider (supervisor Phase 5)" % (
                len(unlimited), ", ".join(unlimited[:6]), " and %d more" % (len(unlimited) - 6) if len(unlimited) > 6 else ""))
        else:
            add("OK", "Spending limit recorded")
        # development data kept apart from live data: a Decisions row says how
        if any(cells and re.match(r"^[\s*_`]*development data", cells[0], re.I) for cells in sections.get("Decisions", [])):
            add("OK", "Development data kept apart")
        else:
            add("MISSING", "Development data kept apart", "no Decisions row `Development data: ...` saying where the live data lives and how a development build is kept from it (rule 55; the design states it, every brief carries it); a product that has live data gets one increment that makes its development build refuse the installed data")

    # --- every adapter of a listed provider is tested against recorded replies (rule 37; A1b item 5):
    #     the providers come from the inventory's chargeable rows, the adapters from the project's own
    #     tracked files that name one in a string (a host, a key name), the evidence from each
    #     adapter's own tests: a cassette or fixture file loaded, or vcr/respx/responses.activate/nock/msw
    providers = provider_words(chargeable_rows(sections, words))
    files = tracked_files(ws) if providers else []
    client_rx = re.compile(r"^\s*(?:from|import)\s+(requests|httpx2?|aiohttp|urllib3|urllib\.request|http\.client|openai|anthropic|modal|replicate|stripe|boto3|botocore|google\.cloud|azure|huggingface_hub|supabase|twilio|sendgrid|slack_sdk)\b", re.M)
    js_client_rx = re.compile(r"""\bfetch\(\s*[`"'](?:https?:)?//(?!localhost|127\.0\.0\.1|0\.0\.0\.0)|\baxios\b""")
    adapters, tests = {}, []
    for rel in files:
        n = os.path.basename(rel)
        is_test = bool(re.search(r"(^|/)(tests?|__tests__|spec)(/|$)", rel)) or n.startswith("test_") or bool(re.search(r"[._](test|spec)\.(py|js|ts|mjs|tsx)$", n))
        if n.endswith(".py"):
            text = read(os.path.join(ws, rel)) or ""
            if is_test:
                tests.append(text)
            elif client_rx.search(text) and names_provider(text, providers):
                adapters[os.path.splitext(n)[0]] = rel
        elif n.endswith((".js", ".ts", ".mjs", ".tsx")) and not n.endswith(".d.ts"):
            text = read(os.path.join(ws, rel)) or ""
            if is_test:
                tests.append(text)
            elif js_client_rx.search(text) and names_provider(text, providers):
                adapters[re.sub(r"\.(js|ts|mjs|tsx)$", "", n)] = rel
    if adapters:
        recordings = any(re.search(r"(^|/)(cassettes?|recorded|recordings)/", rel, re.I) for rel in files)
        loose_rx = re.compile(r"cassette|recorded|replay", re.I)   # enough when the repository tracks recordings
        without = []
        for name in sorted(adapters):
            name_rx = re.compile(r"\b%s\b" % re.escape(name))
            if not any(name_rx.search(t) and (EVIDENCE_RX.search(t) or (recordings and loose_rx.search(t))) for t in tests):
                without.append(name)
        if without:
            add("MISSING", "Adapters tested against recorded replies", "%d adapter(s) of a listed provider without a test that names them and replays recorded replies, that is a cassette or fixture file the test loads, or vcr, respx, responses.activate, nock or msw in that test; a mock transport fed by hand is an invented reply (rule 37; A1b item 5): %s%s" % (
                len(without), ", ".join(without[:6]), " and %d more" % (len(without) - 6) if len(without) > 6 else ""))
        else:
            add("OK", "Adapters tested against recorded replies")

    # --- the supervisor's working files and the review files live under run/, which must be ignored (rule 54)
    gi = read(os.path.join(ws, ".gitignore")) or ""
    if not any(re.match(r"^/?run/?(\s|$)", line.strip()) for line in gi.splitlines()):
        add("NOTE", "run/ ignored", "no `run/` line in .gitignore: the supervisor's working files (`run/supervisor/`, rule 54) and the review files would count as changes, and `review-guard.py verify` cleans untracked files")

    # --- no secret through an environment variable the owner sets (the inventory says how each arrives)
    by_env = []
    for line in inv.splitlines():
        if not line.lstrip().startswith("|") or not re.search(r"env(ironment)? var", line, re.I) or re.search(r"test-only", line, re.I):
            continue
        for name in re.findall(r"\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b", line.split("|")[1] if line.count("|") > 2 else line):
            if ENV_SECRET.search(name) and not LOCATION_NAME.search(name) and name not in by_env:
                by_env.append(name)
    if inv:
        if by_env:
            add("MISSING", "No secret through an environment variable", "the inventory says the owner supplies %s through an environment variable; every program started in that environment inherits it: the product reads it from a key file outside the Workspace or the operating system's credential store instead, and no run sheet asks the owner to set a secret as a variable (KP-032)" % ", ".join(by_env[:8]))
        else:
            add("OK", "No secret through an environment variable")

    # --- account keys in this session's own environment (names only)
    env_keys = sorted(k for k in os.environ if ENV_SECRET.search(k.upper()) and not k.upper().startswith(("CURSOR_", "GIT_CONFIG_KEY_")))
    if env_keys:
        add("NOTE", "Account keys in the session's environment", "%s: every program the owner starts inherits these; the launcher withholds them from builder and reviewer runs (since 2026.10.04e), and a key file outside the Workspace is the better home" % (", ".join(env_keys[:8]) + (" ..." if len(env_keys) > 8 else "")))

    # --- private memory notes (names only)
    for d, notes in memory_dirs(ws):
        if notes:
            add("NOTE", "Private memory notes", "%d note(s) in %s: %s; calibration step 2b reviews them (rule 41: a note never holds a rule or project state)" % (len(notes), d, ", ".join(notes[:8]) + (" ..." if len(notes) > 8 else "")))

    # --- the bridge version
    status = read(os.path.join(ws, "docs", "PROJECT_STATUS.md")) or ""
    m = re.search(r"^\s*(?:[-*]\s+)?[*_`]*Bridge version[*_`]*\s*:[*_`]*\s*([0-9.]+[a-z]?)", status, re.M | re.I)
    installed = (read(os.path.join(HERE, "VERSION")) or "").strip()
    if m and installed:
        if m.group(1) == installed:
            add("OK", "Calibrated to the installed bridge (%s)" % installed)
        else:
            add("MISSING", "Calibrated to the installed bridge", "the status file says %s, the installed bridge is %s: run /calibrate-bridge" % (m.group(1), installed))

    missing = [r for r in results if r[0] == "MISSING"]
    print("conformance-check: %s" % ws)
    for verdict, floor, detail in results:
        if quiet and verdict == "OK":
            continue
        print("  %-8s %s%s" % (verdict, floor, ("  - " + detail) if detail else ""))
    print("conformance-check: %d OK, %d MISSING, %d NOTE" % (
        sum(1 for r in results if r[0] == "OK"), len(missing), sum(1 for r in results if r[0] == "NOTE")))
    if missing:
        print("RESULT: %d floor(s) missing - each is a calibration item, applied as configuration work in the next stage" % len(missing))
        return 1
    print("RESULT: CONFORMANT")
    return 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):      # never crash on a character the console lacks
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(errors="backslashreplace")
    sys.exit(main())
