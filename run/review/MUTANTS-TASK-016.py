"""TASK-016 mutation driver (supervisor-side): each mutant applied to a scratch copy of bridge/ and tests/,
tests/test_trace_check.py run there, the copy restored and byte-checked. The Workspace is never edited.
usage: task016_mutants.py <Workspace> <scratch folder outside the Workspace>"""
import pathlib
import shutil
import subprocess
import sys

if len(sys.argv) != 3:
    sys.exit(__doc__)
REPO = pathlib.Path(sys.argv[1]).resolve()
SCRATCH = pathlib.Path(sys.argv[2]).resolve() / "task016-copy"
assert REPO not in SCRATCH.parents, "the scratch folder must be outside the Workspace"
TC = "bridge/cursor-bridge/trace-check.py"

MUTANTS = [
    ("e-reword-any-file", TC, "            if file_rel != CORE_REL:\n                continue\n", ""),
    ("f-new-against-core-only", TC, "    baseline_set = set(baseline_units_by_norm.keys())",
     '    baseline_set = set(t["normal"] for t in baseline_supervisor_traced)'),
    ("j-absent-commit-not-reported", TC,
     '            errors.append((\n                sha,\n                "baseline commit is absent from this repository; a shallow clone is the likely cause",\n            ))',
     "            pass"),
    ("b-copy-across-files-only", TC, "        elif c > b:", "        elif c > b and len(current_paths_for_norm.get(nf, [])) > 1:"),
    ("c-excused-counted", TC, "            if not unit_excused(rel, u, excused_current):\n                current_counts_c",
     "            if True:\n                current_counts_c"),
    ("i-no-citations", TC, "        check_citations(rel, current_file_units[rel], all_headings, findings_cite)", "        pass"),
    # rounds 2 to 4 (names marked "expected to survive" are redundant guards or need a file symbolic link,
    # which this Windows account cannot make; those tests run on Linux CI)
    ("l-containment-dropped (killed by the before-realpath positive control)", TC,
     "    if not bridge_contains(root, current):\n        return False\n    return True", "    return True"),
    ("u-walk-keeps-junction-folders", TC,
     "        for name in dirnames:\n            full = os.path.join(dirpath, name)\n            if is_path_link(full):",
     "        for name in dirnames:\n            full = os.path.join(dirpath, name)\n            if os.path.islink(full):"),
    ("ad-linked-file-skipped-silently (file link; expected to survive here)", TC,
     '            if is_path_link(full):\n                walk_errors.append((\n                    slash(os.path.relpath(full, root)),\n                    "is a link",\n                ))\n                return found\n            rel = slash',
     "            if is_path_link(full):\n                continue\n            rel = slash"),
    ("v-ref-walk-skips-link-test", TC, "    if first_link_on_rel_path(root, bridge_rel):\n        return False\n", ""),
    ("ae-linked-bridge-not-tested (empty rest)", TC,
     '        if first_link_on_rel_path(root, "bridge"):\n            return False\n', ""),
    ("ab-walk-start-not-tested (redundant: the files read by name lie under workflow/; expected to survive)", TC,
     "    link_rel = first_link_on_rel_path(root, workflow_rel)", "    link_rel = None"),
    ("ac-core-not-tested", TC, "    link_rel = first_link_on_rel_path(root, CORE_REL)", "    link_rel = None"),
    ("ac-baseline-not-tested (exceptions check catches a folder link; file link expected to survive here)", TC,
     "    link_rel = first_link_on_rel_path(root, BASELINE_REL)", "    link_rel = None"),
    ("ac-exceptions-not-tested (file link; expected to survive here)", TC,
     "    link_rel = first_link_on_rel_path(root, EXCEPTIONS_REL)", "    link_rel = None"),
    ("w-map-homes-unescaped", TC, 'home = ", ".join(escape_field(p) for p in paths) if paths else "-"',
     'home = ", ".join(paths) if paths else "-"'),
    ("x-refs-sorted-by-text", TC, "    for rel, line_no, ref in findings_ref:", "    for rel, line_no, ref in sorted(findings_ref):"),
    ("y-chain-scanned-inside-the-quote", TC,
     "        chain_pos = end + 1\n        while True:\n            chain_m = re.match(",
     "        chain_pos = start\n        while True:\n            chain_m = re.search("),
    ("ag-search-resumes-inside-the-quote", TC, "        pos = chain_pos\n    return out", "        pos = start\n    return out"),
    ("ah-empty-chain-quote", TC, "\"([^\"]+)\"', normal[chain_pos:]", "\"([^\"]*)\"', normal[chain_pos:]"),
    ("ah-empty-first-quote", TC, "        if end == start:\n            pos = end + 1\n            continue\n", ""),
    ("z-device-rule-dropped", TC, "    if seg.split(\".\", 1)[0].upper() in WIN_DEVICE_NAMES:\n        return True\n", ""),
    ("trailing-dot-rule-dropped", TC, "    if seg.endswith(\".\") and seg != \"...\":\n        return True\n", ""),
    ("af-placeholder-refused", TC, "    if seg.endswith(\".\") and seg != \"...\":", "    if seg.endswith(\".\"):"),
    ("aa-git-show-failure-continues", TC,
     '            print("ERROR: git show: %s" % escape_field(git_err))\n            print("RESULT: not checked")\n            return 2\n',
     '            errors.append(("git show", git_err))\n            continue\n'),
    ("walk-onerror-dropped", TC, "os.walk(under_workflow, onerror=onerror)", "os.walk(under_workflow)"),
    ("one-strip-undone (shown text unstripped)", TC, '                findings_ref.append((rel, no, "~/.claude/" + rest))',
     '                findings_ref.append((rel, no, "~/.claude/" + m.group(1)))'),
]


def copy():
    if SCRATCH.exists():
        shutil.rmtree(SCRATCH)
    for part in ("bridge", "tests"):
        shutil.copytree(REPO / part, SCRATCH / part, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))


def run():
    p = subprocess.run([sys.executable, "-m", "pytest", "tests/test_trace_check.py", "-q", "-p", "no:cacheprovider"],
                       cwd=str(SCRATCH), capture_output=True, text=True, encoding="utf-8", errors="replace",
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return p.returncode, (p.stdout.strip().splitlines() or ["?"])[-1]


def main():
    copy()
    rc, last = run()
    print("baseline: rc=%d %s" % (rc, last))
    if rc != 0:
        sys.exit("baseline not green")
    survived = 0
    for name, rel, old, new in MUTANTS:
        target = SCRATCH / rel
        original = target.read_bytes()
        text = original.decode("utf-8")
        nl = "\r\n" if "\r\n" in text else "\n"
        old_n, new_n = old.replace("\n", nl), new.replace("\n", nl)
        if text.count(old_n) != 1:
            print("%s: pattern found %d times, not applied" % (name, text.count(old_n)))
            survived += 1
            continue
        target.write_bytes(text.replace(old_n, new_n).encode("utf-8"))
        try:
            rc, last = run()
        finally:
            target.write_bytes(original)
        assert target.read_bytes() == original, name
        survived += rc == 0
        print("%s: %s (%s)" % (name, "KILLED" if rc != 0 else "SURVIVED", last))
    shutil.rmtree(SCRATCH)
    print("survived: %d of %d" % (survived, len(MUTANTS)))


if __name__ == "__main__":
    main()
