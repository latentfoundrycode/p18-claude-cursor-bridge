#!/usr/bin/env python3
"""lock-check: a dependency manifest changed, so the lockfile CI installs from must have too.

Reviewers read what IS in a diff; this checks for what is MISSING from it. If a
dependency manifest changed against <base> and its lockfile did not, the resolved
closure CI installs is stale and the build will fail at import/collection time
(ISS-004, Known-Pitfalls KP-017).

  python lock-check.py <base-ref> [--lock <path>]...

Known pairs (manifest -> any of these lockfiles):
  pyproject.toml / requirements.in / setup.cfg -> requirements.lock, requirements.txt,
        uv.lock, poetry.lock, Pipfile.lock, pdm.lock
  package.json -> package-lock.json, pnpm-lock.yaml, yarn.lock, bun.lockb
  Cargo.toml -> Cargo.lock;  go.mod -> go.sum;  Gemfile -> Gemfile.lock
  composer.json -> composer.lock;  pubspec.yaml -> pubspec.lock;  *.csproj -> packages.lock.json
--lock adds a project-specific lockfile path to the candidate list.
Exit 0 = consistent (or no manifest changed), 1 = manifest changed without its lockfile,
2 = cannot verify. Untracked lockfiles count as changed. ASCII-only on purpose.
"""
import os
import subprocess
import sys

NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

PAIRS = [
    (("pyproject.toml", "requirements.in", "setup.cfg", "setup.py"),
     ("requirements.lock", "requirements.txt", "uv.lock", "poetry.lock", "Pipfile.lock", "pdm.lock")),
    (("package.json",), ("package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lockb", "bun.lock")),
    (("Cargo.toml",), ("Cargo.lock",)),
    (("go.mod",), ("go.sum",)),
    (("Gemfile",), ("Gemfile.lock",)),
    (("composer.json",), ("composer.lock",)),
    (("pubspec.yaml",), ("pubspec.lock",)),
    (("Pipfile",), ("Pipfile.lock",)),
]


def git(args):
    try:
        return subprocess.run(["git"] + args, capture_output=True, text=True, check=True,
                              creationflags=NO_WINDOW).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print("CANNOT VERIFY: git %s failed (%s)" % (" ".join(args), e))
        sys.exit(2)


def main():
    argv = sys.argv[1:]
    if not argv:
        print("usage: lock-check.py <base-ref> [--lock <path>]...")
        return 2
    base = argv[0]
    extra_locks = [argv[i + 1] for i, a in enumerate(argv) if a == "--lock" and i + 1 < len(argv)]

    changed = set(l.strip().replace("\\", "/") for l in git(["diff", "--name-only", base]).splitlines() if l.strip())
    for l in git(["status", "--porcelain", "-uall"]).splitlines():
        if l.startswith("??"):
            changed.add(l[3:].strip().replace("\\", "/"))

    def base_name(p):
        return p.rsplit("/", 1)[-1]

    def same_dir(a, b):
        return os.path.dirname(a) == os.path.dirname(b)

    problems, checked = [], 0
    for path in sorted(changed):
        name = base_name(path)
        for manifests, locks in PAIRS:
            if name in manifests or (name.endswith(".csproj") and "*.csproj" in manifests):
                checked += 1
                candidates = list(locks) + [base_name(x) for x in extra_locks]
                lock_changed = any(base_name(c) in candidates and same_dir(c, path) for c in changed) \
                    or any(x.replace("\\", "/") in changed for x in extra_locks)
                if not lock_changed:
                    problems.append((path, ", ".join(candidates)))
    if name_csproj := [p for p in changed if p.endswith(".csproj")]:
        checked += len(name_csproj)
        if not any(base_name(c) == "packages.lock.json" for c in changed):
            for p in name_csproj:
                problems.append((p, "packages.lock.json"))

    if checked == 0:
        print("lock-check: no dependency manifest changed against %s - nothing to verify" % base)
        return 0
    if problems:
        print("LOCKFILE MISSING FROM DIFF:")
        for m, cands in problems:
            print("  %s changed, but none of [%s] changed alongside it in the same folder" % (m, cands))
        print("Regenerate the lockfile with the project's lock command and commit it in the same increment.")
        return 1
    print("lock-check: %d manifest change(s) each accompanied by a lockfile change" % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
