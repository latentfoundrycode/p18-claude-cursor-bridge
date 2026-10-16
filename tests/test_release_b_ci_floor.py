"""Release B — TASK-002 (security floor in CI) structural test.

enforces: docs/BUILD_PLAN.md TASK-002 Done when; satisfies R-002.
Supervisor-authored (reviewer-independent). Asserts the committed CI floor:
Semgrep (OSS engine, no token, explicit rulesets, --error, diff-aware), OSV-Scanner,
and Socket (authenticated by its repo secret) run unguarded on ubuntu from a
committed requirements.lock; every action is pinned by commit SHA; checkouts do not
persist credentials; secrets appear only in step-level env; and the floor cannot
silently skip itself (no step- or job-level guard, no `|| true` / `|| :` / `|| echo`).
Reads committed files only.
"""
import pathlib
import re

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "tests.yml"
LOCKFILE = ROOT / "requirements.lock"

SHA40 = re.compile(r"@[0-9a-f]{40}(?:\s|$|#)")
SEMGREP = re.compile(r"\bsemgrep\b", re.I)
OSV = re.compile(r"osv-scanner", re.I)
SOCKET = re.compile(r"\bsocket(?:security)?\b", re.I)
SCANNERS = (("semgrep", SEMGREP), ("osv-scanner", OSV), ("socket", SOCKET))
DISABLERS = re.compile(r"(?:\|\||;)\s*(?:true\b|exit\s+0\b|:(?=\s|$|;)|echo\b)")
# a repository secret in any form: any `${{ }}` expression reading the secrets context (up to its closing `}}`, so
# format('{0}', secrets.X) and toJSON(secrets) count) and a bare secrets.X / secrets['X']; expression names are
# case-insensitive
SECRET_CTX = re.compile(r"\$\{\{(?:(?!\}\}).)*?\bsecrets\b|\bsecrets\s*[.\[]", re.S | re.I)
# a secret or the job's own token, for the rule that nothing is installed beside one
SECRET_REF = re.compile(SECRET_CTX.pattern + r"|\bgithub\s*(?:\.\s*token\b|\[\s*['\"]token['\"]\s*\])", re.S | re.I)
INSTALLS = re.compile(r"\b(?:npm|pnpm|yarn|bun)\s+(?:-{1,2}[\w-]+(?:=\S+|\s+[^-\s]\S*)?\s+)*?(?:install|add|i|it|ci|dlx|x|exec)\b|\b(?:npx|bunx|uvx)\b|\bpip3?\s+install\b"
                      r"|\buv\s+(?:pip|tool|add|sync|run)\b|\bgo\s+install\b|\bgem\s+install\b|\bcargo\s+install\b"
                      r"|\bcurl\b|\bwget\b|\bpipx\s+(?:install|run)\b")
# npm's install and clean-install commands with their aliases (npm help install, npm help ci)
NPM_INSTALL = re.compile(r"\bnpm\s+(?:-{1,2}[\w-]+(?:=\S+|\s+[^-\s]\S*)?\s+)*?(?:install|i|in|ins|inst|insta|instal|isnt|isnta|isntal|isntall|add|ci"
                         r"|clean-install|ic|install-clean|isntall-clean|it|cit|install-test|install-ci-test|update|up|upgrade)\b")
# The whole workflow as committed, verbatim — every top-level key (triggers, permissions, any env or defaults) and
# every job and step (the supervisor's pin, BUG-001 rounds 5 and 6): a change anywhere in the workflow fails here and
# must change this pin in the same diff, where both reviewers read it (Merge-Verification-Policy §Anti-gaming).
# Regenerate it from the workflow only for a change the gate approves. (`on` reads back as the key True, YAML 1.1.)
WORKFLOW_PIN = {True: {'pull_request': None, 'push': {'branches': ['main']}},
     'jobs': {'security-floor': {'name': 'security floor',
                                 'runs-on': 'ubuntu-latest',
                                 'steps': [{'uses': 'actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09',
                                            'with': {'fetch-depth': 0, 'persist-credentials': False}},
                                           {'env': {'GITHUB_EVENT_BEFORE': '${{ github.event.before }}',
                                                    'GITHUB_EVENT_NAME': '${{ github.event_name }}',
                                                    'GITHUB_EVENT_PULL_REQUEST_BASE_SHA': '${{ '
                                                                                          'github.event.pull_request.base.sha '
                                                                                          '}}',
                                                    'GITHUB_SHA': '${{ github.sha }}'},
                                            'name': 'Semgrep',
                                            'run': 'set -euo pipefail\n'
                                                   'ARGS=(scan --config p/python --config p/secrets --config '
                                                   '.semgrep.yml --config '
                                                   'bridge/cursor-bridge/semgrep-bridge-rules.yml --error)\n'
                                                   'if [ "${GITHUB_EVENT_NAME}" = "pull_request" ]; then\n'
                                                   '  BASELINE="$(git merge-base '
                                                   '"${GITHUB_EVENT_PULL_REQUEST_BASE_SHA}" "${GITHUB_SHA}")"\n'
                                                   '  ARGS+=(--baseline-commit "$BASELINE")\n'
                                                   'elif [ "${GITHUB_EVENT_NAME}" = "push" ]; then\n'
                                                   '  BEFORE="${GITHUB_EVENT_BEFORE}"\n'
                                                   '  if [ "$BEFORE" != '
                                                   '"0000000000000000000000000000000000000000" ]; then\n'
                                                   '    ARGS+=(--baseline-commit "$BEFORE")\n'
                                                   '  fi\n'
                                                   'fi\n'
                                                   'pipx run semgrep==1.176.1 "${ARGS[@]}" .\n',
                                            'shell': 'bash'},
                                           {'name': 'OSV-Scanner',
                                            'run': 'curl -fsSL -o osv-scanner '
                                                   '"https://github.com/google/osv-scanner/releases/download/v2.7.0/osv-scanner_linux_amd64"\n'
                                                   'echo '
                                                   '"160c6253e2922e9e0a6a9771c5c4c40a4b3c6090b34a3cdd5e80c96cc2e4218b  '
                                                   'osv-scanner" | sha256sum -c -\n'
                                                   'chmod +x osv-scanner\n'
                                                   'set +e\n'
                                                   './osv-scanner scan source --config=osv-scanner.toml '
                                                   "--lockfile='requirements.txt:requirements.lock'\n"
                                                   'code=$?\n'
                                                   'set -e\n'
                                                   'if [ "$code" -eq 0 ]; then\n'
                                                   '  exit 0\n'
                                                   'fi\n'
                                                   'if [ "$code" -eq 128 ]; then\n'
                                                   '  echo "OSV-Scanner exit 128: requirements.lock was not '
                                                   'read"\n'
                                                   '  exit 128\n'
                                                   'fi\n'
                                                   'exit "$code"\n',
                                            'shell': 'bash'},
                                           {'uses': 'actions/setup-node@a0853c24544627f65ddf259abe73b1d18a591444',
                                            'with': {'node-version': '22'}},
                                           {'name': 'Install the Socket CLI',
                                            'run': 'npm install -g --ignore-scripts @socketsecurity/cli@1.7.0'},
                                           {'env': {'SOCKET_CLI_API_TOKEN': '${{ secrets.SOCKET_SECURITY_API_KEY '
                                                                            '}}',
                                                    'SOCKET_CLI_ORG_SLUG': '${{ vars.SOCKET_ORG_SLUG }}'},
                                            'name': 'Socket',
                                            'run': 'socket ci --no-banner'}]},
              'tests': {'name': 'bridge programs (${{ matrix.os }})',
                        'runs-on': '${{ matrix.os }}',
                        'steps': [{'uses': 'actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09',
                                   'with': {'persist-credentials': False}},
                                  {'uses': 'actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1',
                                   'with': {'python-version': '3.12'}},
                                  {'run': 'python -m pip install -r requirements.lock'},
                                  {'run': 'python -m pytest tests -q'},
                                  {'name': "windowless check over the bridge's programs",
                                   'run': 'python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge'},
                                  {'name': 'the manifest matches the tree',
                                   'run': 'python bridge/cursor-bridge/bridge-check.py --root bridge --sources '
                                          '--quiet'}],
                        'strategy': {'fail-fast': False, 'matrix': {'os': ['windows-latest', 'ubuntu-latest']}}}},
     'name': 'tests',
     'permissions': {'contents': 'read'}}
FLOOR_JOB = WORKFLOW_PIN["jobs"]["security-floor"]
LOCK_CLOSURE = {"pytest", "pyyaml", "colorama", "iniconfig", "packaging", "pluggy", "pygments"}


def _text():
    return WORKFLOW.read_text(encoding="utf-8")


def _data():
    return yaml.safe_load(_text())


def _jobs(data):
    return {n: j for n, j in (data.get("jobs") or {}).items() if isinstance(j, dict)}


def _steps(job):
    return [s for s in (job.get("steps") or []) if isinstance(s, dict)]


def _body(step):
    return "\n".join(str(step.get(k)) for k in ("uses", "run") if step.get(k))


def _ubuntu_jobs(data):
    return {n: j for n, j in _jobs(data).items() if str(j.get("runs-on", "")).strip() == "ubuntu-latest"}


def _semgrep_step(data):
    for job in _ubuntu_jobs(data).values():
        for step in _steps(job):
            if SEMGREP.search(_body(step)):
                return step
    raise AssertionError("R-002: no Semgrep step on ubuntu-latest")


def test_r002_disabler_pattern_catches_the_idioms():
    """R-002: the guard this test relies on catches the usual exit-status swallowers (a negative test must show its precondition)."""
    for bad in ("socket ci || true", "socket ci || :", "x || exit 0", "x || echo skipped", "x ||:;", "socket ci; true", "x; exit 0"):
        assert DISABLERS.search(bad), bad
    for ok in ("a && b", "set -euo pipefail", "exit \"$code\"", "if [ \"$code\" -eq 0 ]; then"):
        assert not DISABLERS.search(ok), ok


def test_r002_secret_and_install_patterns_catch_their_forms():
    """R-002: the patterns the secret and install checks rely on match each form they claim (a negative test must show its precondition)."""
    for bad in ("${{ secrets.X }}", "${{ secrets['X'] }}", "${{ toJSON(secrets) }}", "${{secrets.X}}",
                "${{ format('{0}', secrets.X) }}", "${{ SECRETS.X }}"):
        assert SECRET_CTX.search(bad) and SECRET_REF.search(bad), bad
    for token in ("${{ github.token }}", "${{ github['token'] }}"):
        assert SECRET_REF.search(token) and not SECRET_CTX.search(token), token
    for ok in ("${{ vars.SOCKET_ORG_SLUG }}", "${{ github.sha }}", "secrets/ folder"):
        assert not SECRET_REF.search(ok), ok
    assert not SECRET_REF.search("${{ github.token_url }}")
    for bad in ("npm install x", "npm ci", "npm exec x", "npm --global i x", "npm --prefix /tmp install x", "npx x", "pnpm dlx x", "yarn dlx x", "bunx x", "uvx x", "uv tool run x",
                "pip3 install x", "go install x", "curl -fsSL x"):
        assert INSTALLS.search(bad), bad
    for bad in ("npm i -g x", "npm add x", "npm isntall x", "npm clean-install", "npm -g install x", "npm --global i x", "npm it",
                "npm --prefix /tmp install x", "npm --prefix=/tmp install x", "npm cit", "npm update -g x"):
        assert NPM_INSTALL.search(bad), bad


def test_r002_commands_split_chains():
    """R-002: a chained second command is read on its own (a negative test must show its precondition)."""
    assert _commands("npm install -g --ignore-scripts a && npm install -g b ; npm i c | tee x || true") == \
        ["npm install -g --ignore-scripts a", "npm install -g b", "npm i c", "tee x", "true"]


def test_r002_lines_join_continuations():
    """R-002: a backslash-continued command is read as one line, so a flag on a continuation counts (a negative test must show its precondition)."""
    step = {"run": "# c\nnpm install -g \\\n  --ignore-scripts \\\n  --ignore-scripts=false pkg\nsocket ci --no-banner\n"}
    assert _lines(step) == ["npm install -g --ignore-scripts --ignore-scripts=false pkg", "socket ci --no-banner"]


def test_r002_workflow_parses():
    """R-002: the workflow is valid YAML with jobs."""
    data = _data()
    assert isinstance(data, dict) and _jobs(data)


def _on(data):
    # YAML 1.1 reads the bare key `on` as the boolean True
    return data.get("on", data.get(True))


def _lines(step):
    """The step's commands, one per entry: comments dropped, backslash-continued lines joined into their command."""
    out, held = [], ""
    for raw in str(step.get("run") or "").splitlines():
        s = raw.strip()
        if not held and (not s or s.startswith("#")):
            continue
        if s.endswith("\\"):
            held += s[:-1].strip() + " "
            continue
        out.append((held + s).strip())
        held = ""
    if held.strip():
        out.append(held.strip())
    return out


def _commands(line):
    """The commands of one line, split at `&&`, `||`, `;` and `|`, so a chained second command is read on its own."""
    return [c.strip() for c in re.split(r"&&|\|\||;|\|", line) if c.strip()]


def _floor_step(data, pattern):
    for job in _ubuntu_jobs(data).values():
        for step in _steps(job):
            if any(pattern.search(line) for line in _lines(step)):
                return job, step
    raise AssertionError(f"R-002: no ubuntu step runs {pattern.pattern!r}")


def test_r002_runs_on_pull_request_and_push_to_main():
    """R-002 (docs/BUILD_PLAN.md stage B1 Demonstration: the full gate runs on a PR and on a push to main): the workflow runs on
    every pull request and on every push to main, and no path or branch filter can leave a change unscanned."""
    on = _on(_data())
    assert isinstance(on, dict), "R-002: the workflow's `on:` must be a mapping naming its events"
    assert "pull_request" in on, "R-002: the workflow must run on pull_request"
    push = on.get("push")
    assert isinstance(push, dict) and "main" in (push.get("branches") or []), "R-002: the workflow must run on push to main"
    for event in ("pull_request", "push"):
        spec = on.get(event) or {}
        for key in ("paths", "paths-ignore", "branches-ignore"):
            assert key not in spec, f"R-002: {event} carries a {key} filter"
    pr_branches = (on.get("pull_request") or {}).get("branches")
    assert pr_branches is None or "main" in pr_branches, "R-002: pull_request must cover pull requests into main"
    pr_types = (on.get("pull_request") or {}).get("types")
    assert pr_types is None or {"opened", "synchronize", "reopened"} <= set(pr_types), \
        "R-002: pull_request must run when a pull request opens, updates or reopens"


def test_r002_each_scanner_decides_its_step():
    """R-002: each scanner's own exit status is its step's result, so a finding fails the floor: the Semgrep step runs
    under `set -euo pipefail` and ends with the pinned Semgrep call; OSV-Scanner reads requirements.lock, its status is
    taken at once, `exit 0` appears only under the clean-status branch, and the step ends with `exit "$code"`; the
    step holding the Socket key runs only `socket ci --no-banner` (a name merely echoed is no scanner)."""
    data = _data()
    _, semgrep = _floor_step(data, re.compile(r"^pipx run semgrep=="))
    lines = _lines(semgrep)
    assert lines[0] == "set -euo pipefail", "R-002: the Semgrep step must start with set -euo pipefail"
    assert re.fullmatch(r'pipx run semgrep==\d+\.\d+\.\d+ "\$\{ARGS\[@\]\}" \.', lines[-1]), "R-002: the Semgrep step must end with the pinned Semgrep call"

    _, osv = _floor_step(data, re.compile(r"^\./osv-scanner scan source\b"))
    lines = _lines(osv)
    call = next(i for i, s in enumerate(lines) if s.startswith("./osv-scanner scan source"))
    assert "--lockfile='requirements.txt:requirements.lock'" in lines[call], "R-002: OSV-Scanner must read requirements.lock"
    assert lines[call + 1] == "code=$?", "R-002: OSV-Scanner's status must be taken on the next line"
    for i, s in enumerate(lines):
        if s == "exit 0":
            assert lines[i - 1] == 'if [ "$code" -eq 0 ]; then', "R-002: exit 0 outside the clean-status branch"
    assert lines[-1] == 'exit "$code"', 'R-002: the OSV step must end with exit "$code"'

    _, socket = _floor_step(data, re.compile(r"(?:^|\s)socket\s+ci\b"))
    assert _lines(socket) == ["socket ci --no-banner"], "R-002: the step that holds the Socket key runs only `socket ci --no-banner`"


def test_r002_no_install_runs_beside_a_secret():
    """R-002 (secure-coding.snapshot.md V14, never expose secrets; the brief: no secret on a scanner's path beyond its own
    token): no step that carries a secret (any expression reading the secrets context) installs or fetches anything;
    every npm install skips lifecycle scripts — the line's one mention of the setting is the bare `--ignore-scripts`
    (npm takes the last of several, so `--ignore-scripts --ignore-scripts=false` runs scripts), and no env at any level
    sets npm's ignore-scripts config to anything but `true` (or `1`); and the Socket CLI is installed at the version the inventory records (1.7.0; a
    bump is an admission, supervisor.md rule 14) in a step of the floor's job before the scan."""
    data = _data()
    envs = [data.get("env")] + [j.get("env") for j in _jobs(data).values()] + [s.get("env") for j in _jobs(data).values() for s in _steps(j)]
    for env in envs:
        for key, value in (env or {}).items():
            if "ignore_scripts" in str(key).lower().replace("-", "_"):
                assert str(value).strip().lower() in ("true", "1"), f"R-002: an env sets npm's ignore-scripts config to {value!r}"
    for name, job in _jobs(data).items():
        for step in _steps(job):
            if SECRET_REF.search(str(step.get("env") or {})):
                for s in _lines(step):
                    assert not INSTALLS.search(s), f"R-002: a step holding a secret installs or fetches ({name}): {s!r}"
            for s in _lines(step):
                for seg in _commands(s):
                    if not NPM_INSTALL.search(seg):
                        continue
                    tokens = seg.split()
                    mentions = [i for i, t in enumerate(tokens) if "ignore-scripts" in t.lower() or "ignore_scripts" in t.lower()]
                    assert [tokens[i] for i in mentions] == ["--ignore-scripts"], f"R-002: npm install must carry exactly one bare --ignore-scripts: {seg!r}"
                    after = tokens[mentions[0] + 1].lower() if mentions[0] + 1 < len(tokens) else ""
                    assert after not in ("true", "false", "0", "1"), f"R-002: --ignore-scripts given a value ({after}) npm would read: {seg!r}"
    job, socket = _floor_step(_data(), re.compile(r"(?:^|\s)socket\s+ci\b"))
    steps = _steps(job)
    before = steps[: steps.index(socket)]
    assert any(re.search(r"\bnpm\s+install\b.*\s@socketsecurity/cli@1\.7\.0(?:\s|$)", s) for st in before for s in _lines(st)), \
        "R-002: the Socket CLI is not installed at its recorded version (1.7.0) before the scan"


def test_r002_floor_job_is_the_pinned_one():
    """R-002 (docs/BUILD_PLAN.md TASK-002; the stage B1 review): the `security floor` job is exactly the committed one
    — its name, runner and every step verbatim, so no scanner can be skipped, its status overwritten or a step added
    beside the key without this pin changing in the same diff."""
    data = _data()
    assert data["jobs"].get("security-floor") == FLOOR_JOB, "R-002: the security floor job differs from the pinned one"


def test_r002_workflow_is_the_pinned_one():
    """R-002 (the stage B1 review, BUG-001 round 6): the whole workflow is exactly the committed one, so a workflow-level
    `env:` or `defaults:` (a `run.shell` that skips every step, a registry, NODE_OPTIONS, BASH_ENV), a new job or a
    changed trigger cannot change how the floor runs without this pin changing in the same diff."""
    assert _data() == WORKFLOW_PIN, "R-002: the workflow differs from the pinned one"


def test_r002_workflow_is_the_only_one():
    """R-002 (BUG-001 round 6, Review A): the pin and the one-secret rule read one file, so the workflow folder holds
    that file alone; a second workflow (handing a secret to an install, or running on `pull_request_target`) fails
    here and must widen these tests in the same diff."""
    names = sorted(p.name for p in WORKFLOW.parent.iterdir())
    assert names == [WORKFLOW.name], f"R-002: the workflow folder holds {names}, not the pinned workflow alone"


def test_r002_one_step_holds_a_secret():
    """R-002 (secure-coding.snapshot.md V14; the brief: no secret on a scanner's path beyond its own token): in the whole
    workflow exactly one step refers to a repository secret, in any key — the Socket scan, which runs only
    `socket ci --no-banner` — so no action, install or other command is handed one; and no job passes secrets on
    (a reusable-workflow call with `secrets:`, `secrets: inherit` included)."""
    data = _data()
    for name, job in _jobs(data).items():
        assert "secrets" not in job, f"R-002: job {name} passes secrets on"
    holders = [(name, step.get("name")) for name, job in _jobs(data).items() for step in _steps(job)
               if SECRET_CTX.search(str(step))]
    assert holders == [("security-floor", "Socket")], f"R-002: the steps referring to a secret are {holders}"


def test_r002_three_scanners_unguarded_on_ubuntu():
    """R-002: Semgrep, OSV-Scanner, and Socket each run on ubuntu with no guard that could skip them."""
    data = _data()
    for label, pattern in SCANNERS:
        found = False
        for job in _ubuntu_jobs(data).values():
            for step in _steps(job):
                body = _body(step)
                if not pattern.search(body):
                    continue
                assert "if" not in job, f"R-002: the job running {label} has a job-level if:"
                assert not job.get("continue-on-error"), f"R-002: the job running {label} uses continue-on-error"
                assert "if" not in step, f"R-002: {label} step is guarded by if:"
                assert not step.get("continue-on-error"), f"R-002: {label} step uses continue-on-error"
                assert not DISABLERS.search(body), f"R-002: {label} command swallows its own exit status"
                found = True
        assert found, f"R-002: no unguarded {label} step on ubuntu-latest"


def test_r002_semgrep_not_on_other_runners():
    """R-002: Semgrep runs only on ubuntu (it is unreliable on Windows), never on another runner."""
    data = _data()
    ubuntu = _ubuntu_jobs(data)
    for name, job in _jobs(data).items():
        if name in ubuntu:
            continue
        for step in _steps(job):
            assert not SEMGREP.search(_body(step)), f"R-002: Semgrep runs in non-ubuntu job {name}"


def test_r002_semgrep_oss_blocking_explicit_diff_aware():
    """R-002: Semgrep is a `scan` (OSS, no token, no --pro) with --error, explicit --config rulesets incl. the bridge rules, and diff-aware baselines."""
    step = _semgrep_step(_data())
    body = _body(step)
    assert re.search(r"\(scan\b|\bsemgrep\S*\s+scan\b", body), "R-002: Semgrep must run `scan`, not `ci`"
    assert "--error" in body, "R-002: --error must make a finding fail the step"
    assert body.count("--config") >= 2, "R-002: explicit rulesets via --config"
    assert "bridge/cursor-bridge/semgrep-bridge-rules.yml" in body, "R-002: the bridge rules must be loaded"
    assert "pull_request" in body and "push" in body, "R-002: Semgrep must branch on pull_request and push"
    assert body.count("--baseline-commit") >= 2, "R-002: Semgrep must be diff-aware on both pull_request and push (--baseline-commit on each path)"
    assert "--pro" not in body and "install-semgrep-pro" not in body, "R-002: OSS engine (owner's decision 2026-10-12)"
    assert "SEMGREP_APP_TOKEN" not in _text(), "R-002: no Semgrep token in the workflow (OSS engine)"


def test_r002_every_uses_is_commit_pinned():
    """R-002: every `uses:` names a 40-hex commit SHA, and at least one uses: exists."""
    seen = 0
    for line in _text().splitlines():
        m = re.search(r"^\s*(?:-\s*)?uses:\s*(\S+)", line)
        if not m:
            continue
        seen += 1
        assert SHA40.search(m.group(1) + " "), f"R-002: unpinned uses: {m.group(1)!r}"
    assert seen >= 1, "R-002: no uses: lines found (vacuous pass)"


def test_r002_checkouts_do_not_persist_credentials():
    """R-002: every actions/checkout step sets persist-credentials: false, and at least one exists."""
    seen = 0
    for job in _jobs(_data()).values():
        for step in _steps(job):
            if "actions/checkout" not in str(step.get("uses", "")):
                continue
            seen += 1
            assert (step.get("with") or {}).get("persist-credentials") is False, "R-002: checkout persists credentials"
    assert seen >= 1, "R-002: no checkout step found (vacuous pass)"


def test_r002_pip_installs_only_from_lockfile():
    """R-002: every pip install is exactly `-r requirements.lock`, and at least one exists."""
    seen = 0
    for line in _text().splitlines():
        if "pip install" not in line:
            continue
        seen += 1
        assert line.split("pip install", 1)[1].strip() == "-r requirements.lock", f"R-002: pip install must be exactly `-r requirements.lock`: {line!r}"
    assert seen >= 1, "R-002: no pip install found (vacuous pass)"


def test_r002_lockfile_pins_closure():
    """R-002: requirements.lock pins pytest 9.1.1, pyyaml 6.0.3 and their closure, every line with ==, and holds exactly
    the admitted set of packages (a new name is a new dependency: the admission gate, supervisor.md step 5b, then this set)."""
    text = LOCKFILE.read_text(encoding="utf-8")
    low = text.lower()
    assert "pytest==9.1.1" in low and "pyyaml==6.0.3" in low
    names = set()
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        assert "==" in s, f"R-002: unpinned requirement line: {s!r}"
        names.add(s.split("==", 1)[0].strip().lower())
    assert names == LOCK_CLOSURE, f"R-002: the lock's packages differ from the admitted closure: {sorted(names ^ LOCK_CLOSURE)}"


def test_r002_secrets_only_in_step_env():
    """R-002: `secrets.` appears only inside a step's env: mapping (never in run/with/uses, job- or workflow-level keys), and Socket is authenticated by its repo secret."""
    data = _data()
    assert not SECRET_CTX.search(str({k: v for k, v in data.items() if k != "jobs"})), "R-002: secret at workflow level"
    for name, job in _jobs(data).items():
        assert not SECRET_CTX.search(str({k: v for k, v in job.items() if k != "steps"})), f"R-002: secret at job level in {name}"
        for step in _steps(job):
            for key, value in step.items():
                if key == "env":
                    continue
                assert not SECRET_CTX.search(str(value)), f"R-002: secret outside step env ({key}) in {name}"
    _, step = _floor_step(data, re.compile(r"(?:^|\s)socket\s+ci\b"))
    socket_authenticated = "secrets.SOCKET_SECURITY_API_KEY" in str(step.get("env") or {})
    assert socket_authenticated, "R-002: the Socket step is not authenticated by secrets.SOCKET_SECURITY_API_KEY in its env"


def test_r002_socket_names_its_organization():
    """R-002: the Socket step names its organization through SOCKET_CLI_ORG_SLUG from the repository variable SOCKET_ORG_SLUG (without it the Socket API answers 404 Organization not found, observed on PR #16)."""
    _, step = _floor_step(_data(), re.compile(r"(?:^|\s)socket\s+ci\b"))
    value = re.sub(r"\s+", "", str((step.get("env") or {}).get("SOCKET_CLI_ORG_SLUG", "")))
    assert value == "${{vars.SOCKET_ORG_SLUG}}", "R-002: Socket step must set exactly SOCKET_CLI_ORG_SLUG: ${{ vars.SOCKET_ORG_SLUG }}"


def test_r002_socket_prints_no_banner():
    """R-002 / secure-coding.snapshot.md V14 (never log secrets, credentials or tokens): every `socket ci` call, in every job,
    runs with --no-banner. The CLI's banner prints the first characters of its API token ("token: <5 chars>*** (env)");
    GitHub masks only a whole secret, and the repository is public, so the banner put part of the key into public logs
    (PR #16, 2026-10-12)."""
    calls = 0
    for job in _jobs(_data()).values():
        for step in _steps(job):
            for line in str(step.get("run") or "").splitlines():
                if re.search(r"(?:^|\s)socket\s+ci\b", line):
                    calls += 1
                    assert re.search(r"(?:^|\s)--no-banner(?:\s|$)", line), f"R-002: socket ci must run with --no-banner: {line.strip()!r}"
    assert calls >= 1, "R-002: no `socket ci` call found (vacuous pass)"


def test_r002_least_privilege_permissions():
    """R-002: a least-privilege `permissions: {contents: read}` block covers the floor."""
    data = _data()
    top = data.get("permissions")
    if isinstance(top, dict) and top.get("contents") == "read":
        return
    for job in _ubuntu_jobs(data).values():
        perms = job.get("permissions")
        if isinstance(perms, dict) and perms.get("contents") == "read":
            return
    raise AssertionError("R-002: no least-privilege `permissions: {contents: read}` block on the floor")
