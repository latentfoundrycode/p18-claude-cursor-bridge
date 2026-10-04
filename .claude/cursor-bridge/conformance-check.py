#!/usr/bin/env python3
"""conformance-check: does this project's configuration carry the floors the bridge requires?

  python ~/.claude/cursor-bridge/conformance-check.py [<workspace>] [--screens] [--installable] [--quiet]

Why (plan review R4): the bridge added floors over time (the security scanners in the gate,
SHA-pinned actions, the workspace boundary, the records), and nothing compared a project
configured before a floor existed with what the bridge now requires; the video factory ran
its gate with no scanner and actions pinned by tag while the Project Summary said the floor
applied everywhere. This check reads the project's files and reports, per floor, OK, MISSING
or NOTE. It runs at every calibration and every reflection point; each MISSING is a
calibration item, applied as configuration work in the next stage. It never changes anything.

What it checks, with the file it reads:
  - the gate workflow (.github/workflows/*.yml): a job runs Semgrep, OSV-Scanner and Socket;
    every `uses:` is pinned by a 40-character commit; the runner is Linux (a note otherwise);
  - the workspace boundary (.cursor/rules/workspace-boundary.mdc, the boundary-check hook in
    .cursor/hooks.json) and the frozen secure-coding rule (.cursor/rules/secure-coding.mdc);
  - a lockfile beside each manifest (package.json, pyproject.toml);
  - the records: docs/PROJECT_STATUS.md, INVENTORY.md, REQUIREMENTS.md, RUN_PARAMETERS.md,
    ROSTER.json, DESIGN.md, and docs/diagrams/INDEX.md (missing = a diagram retrofit item);
  - with --screens (or a docs/mockups folder): the design detector in the gate;
  - with --installable (or docs/cli-reference.json present): the CLI reference and its check;
  - secrets within the builder's reach: variable NAMES in Workspace/.env that look like keys
    or tokens (values are never read or printed; KP-032);
  - the recorded bridge version against the installed one (calibration due).
Exit 0 = every floor present; 1 = at least one MISSING; 2 = not a workspace.
ASCII-only on purpose (cp1252 consoles). Never writes.
"""
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SECRET_NAME = re.compile(r"(TOKEN|SECRET|KEY|PASSWORD|PASSWD|CREDENTIAL|API_?KEY)", re.I)


def read(path):
    try:
        with open(path, encoding="utf-8-sig", errors="replace") as f:
            return f.read()
    except OSError:
        return None


def main():
    argv = sys.argv[1:]
    quiet = "--quiet" in argv
    screens = "--screens" in argv
    installable = "--installable" in argv
    positional = [a for a in argv if not a.startswith("--")]
    ws = os.path.abspath(positional[0]) if positional else os.getcwd()
    if not os.path.isdir(os.path.join(ws, "docs")) and not os.path.isdir(os.path.join(ws, ".git")):
        print("conformance-check: %s is not a project workspace (no docs/ and no .git/)" % ws)
        return 2
    results = []                                   # (verdict, floor, detail)

    def add(verdict, floor, detail=""):
        results.append((verdict, floor, detail))

    # --- the gate workflow
    workflows = sorted(glob.glob(os.path.join(ws, ".github", "workflows", "*.yml")) + glob.glob(os.path.join(ws, ".github", "workflows", "*.yaml")))
    wf_text = "\n".join(read(p) or "" for p in workflows)
    if not workflows:
        add("MISSING", "CI gate", "no workflow under .github/workflows/; the merge gate needs a required check")
    else:
        for name, pattern in (("Semgrep in the gate", r"\bsemgrep\b"), ("OSV-Scanner in the gate", r"osv-scanner"), ("Socket in the gate", r"\bsocket\b")):
            if re.search(pattern, wf_text, re.I):
                add("OK", name)
            else:
                add("MISSING", name, "the security floor (N8) rides the required CI check")
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

    # --- the builder's configuration
    for floor, rel, detail in (
        ("Workspace boundary rule", os.path.join(".cursor", "rules", "workspace-boundary.mdc"), "the builder's always-on boundary rule (rule 22)"),
        ("Secure-coding rule", os.path.join(".cursor", "rules", "secure-coding.mdc"), "the frozen ASVS-derived rule the builder self-applies (N8)"),
    ):
        add("OK" if os.path.isfile(os.path.join(ws, rel)) else "MISSING", floor, "" if os.path.isfile(os.path.join(ws, rel)) else detail)
    hooks = read(os.path.join(ws, ".cursor", "hooks.json")) or ""
    add("OK" if "boundary-check" in hooks else "MISSING", "Boundary-check hook", "" if "boundary-check" in hooks else ".cursor/hooks.json does not run boundary-check (rule 22)")
    add("OK" if "windowless-check" in hooks or os.path.isfile(os.path.join(ws, ".cursor", "hooks", "windowless-check.py")) else "NOTE",
        "Windowless check", "" if ("windowless-check" in hooks or os.path.isfile(os.path.join(ws, ".cursor", "hooks", "windowless-check.py"))) else "no windowless-check in the hooks (rule 24)")

    # --- lockfiles
    if os.path.isfile(os.path.join(ws, "package.json")):
        locks = [n for n in ("package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb") if os.path.isfile(os.path.join(ws, n))]
        add("OK" if locks else "MISSING", "Lockfile for package.json", "" if locks else "no lockfile; the gate installs from the lock (KP-018)")
    for sub in (d for d in os.listdir(ws) if os.path.isdir(os.path.join(ws, d)) and not d.startswith(".")):
        if os.path.isfile(os.path.join(ws, sub, "package.json")):
            locks = [n for n in ("package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb") if os.path.isfile(os.path.join(ws, sub, n))]
            add("OK" if locks else "MISSING", "Lockfile for %s/package.json" % sub, "" if locks else "no lockfile beside the manifest (KP-018)")
    for root_dir in [ws] + [os.path.join(ws, d) for d in os.listdir(ws) if os.path.isdir(os.path.join(ws, d)) and not d.startswith(".")]:
        if os.path.isfile(os.path.join(root_dir, "pyproject.toml")):
            locks = [n for n in ("uv.lock", "poetry.lock", "pdm.lock", "requirements.lock", "requirements.txt") if os.path.isfile(os.path.join(root_dir, n))]
            label = "Lockfile for %spyproject.toml" % ("" if root_dir == ws else os.path.basename(root_dir) + "/")
            add("OK" if locks else "MISSING", label, "" if locks else "no lockfile beside the manifest (KP-018)")

    # --- the records
    for rel, detail in (
        ("docs/PROJECT_STATUS.md", "the bounded status file (rule 41)"),
        ("docs/INVENTORY.md", "the inventory (rule 41)"),
        ("docs/REQUIREMENTS.md", "the requirements register (rule 44)"),
        ("docs/RUN_PARAMETERS.md", "the run parameters (rule 29)"),
        ("docs/ROSTER.json", "the model roster (rule 38)"),
        ("docs/DESIGN.md", "the design document (rule 45)"),
    ):
        ok = os.path.isfile(os.path.join(ws, rel))
        add("OK" if ok else "MISSING", rel, "" if ok else detail)
    if os.path.isfile(os.path.join(ws, "docs", "diagrams", "INDEX.md")):
        add("OK", "docs/diagrams/INDEX.md")
    else:
        add("MISSING", "docs/diagrams/INDEX.md", "no diagram index: a diagram retrofit item (restructuring plan 8.7), scheduled at the next natural pause")

    # --- installable software
    if installable or os.path.isfile(os.path.join(ws, "docs", "cli-reference.json")):
        has_ref = os.path.isfile(os.path.join(ws, "docs", "cli-reference.json"))
        add("OK" if has_ref else "MISSING", "docs/cli-reference.json", "" if has_ref else "the generated command reference (rule 32)")
        add("OK" if re.search(r"cli-reference", wf_text) else "MISSING", "CLI reference checked in CI", "" if re.search(r"cli-reference", wf_text) else "no CI step keeps docs/cli-reference.json current (rule 32)")

    # --- secrets within the builder's reach (names only)
    env_path = os.path.join(ws, ".env")
    env_text = read(env_path)
    if env_text is not None:
        names = []
        for line in env_text.splitlines():
            m = re.match(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=", line)
            if m and SECRET_NAME.search(m.group(1)):
                names.append(m.group(1))
        if names:
            add("MISSING", "Keys out of the builder's reach", "Workspace/.env holds %s; the builder reads this file (KP-032): move them to the user's environment or the product's encrypted store" % ", ".join(names))
        else:
            add("OK", "Keys out of the builder's reach")

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
