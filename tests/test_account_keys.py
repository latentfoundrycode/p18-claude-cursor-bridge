"""Account keys are withheld from builder and reviewer runs (2026.10.04e): release 0b told
projects to move paid keys "to the user's environment", which hands them to every process
the owner starts, while the launcher withheld only GitHub variables. The Python recipe
(bridge_env.stripped_env) and the shell recipe (cursor-agent.shim) must decide the same way."""
import os
import shutil
import subprocess

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
SHIM = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "cursor-agent.shim")

WITHHELD = ["ANTHROPIC_API_KEY", "OPENROUTER_API_KEY", "AZURE_DI_API_KEY", "MODAL_TOKEN_ID", "MODAL_TOKEN_SECRET",
            "HF_TOKEN", "NPM_TOKEN", "SOCKET_CLI_API_TOKEN", "SEMGREP_APP_TOKEN", "STRIPE_SECRET_KEY",
            "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "PGPASSWORD", "MINIO_ROOT_PASSWORD", "MY_PRIVATE_KEY",
            "GOOGLE_APPLICATION_CREDENTIALS", "LLM_APIKEY", "GH_TOKEN", "GITHUB_TOKEN", "TOKEN", "SECRET",
            "SFVF_SECRETS_PASSPHRASE", "SFVF_SECRETS_PATH", "DEPLOY_KEYS", "API_TOKENS"]
KEPT = ["PATH", "HOME", "CURSOR_API_KEY", "CURSOR_TOKEN", "TOKENIZERS_PARALLELISM", "SECRETARY", "KEYBOARD_LAYOUT",
        "MONKEY", "PYTHONUTF8", "DATABASE_URL", "REANGLE_INSTANCE_NAME", "LOG_LEVEL"]


def sample_env(tmp_path):
    """A sample environment: the owner's home is a temporary folder holding .cursor (the
    CLI's state), .gitconfig and .claude (what must not reach the run)."""
    home = tmp_path / "home"
    for d in (".cursor", ".claude", ".ssh", ".cache/huggingface/hub", ".cache/torch", ".cache/puppeteer"):
        (home / d).mkdir(parents=True, exist_ok=True)
    (home / ".cache" / "huggingface" / "token").write_text("hf_not_for_the_builder\n", encoding="utf-8")
    (home / ".gitconfig").write_text("[user]\n\tname = owner\n", encoding="utf-8")
    env = {k: "v" for k in WITHHELD + KEPT}
    env["PATH"] = os.environ.get("PATH", "")
    env["LOCALAPPDATA"] = str(tmp_path / "localappdata")
    env["HOME"] = env["USERPROFILE"] = str(home)
    for k in ("SYSTEMROOT", "SystemRoot", "TEMP", "TMP", "COMSPEC", "PATHEXT"):
        if k in os.environ:
            env[k] = os.environ[k]
    return env


def same_path(a, b):
    return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))


def assert_own_home(out, tmp_path):
    """The run's home is the agent's folder (KP-038): .cursor there is the owner's real one,
    .claude and the owner's stores are absent, and git keeps the global configuration."""
    agent_home = tmp_path / "home" / ".cursor-bridge" / "agent-home"
    assert same_path(out["HOME"], str(agent_home)) and same_path(out["USERPROFILE"], str(agent_home)), (out["HOME"], out["USERPROFILE"])
    assert os.path.lexists(agent_home / ".cursor") and os.path.samefile(agent_home / ".cursor", tmp_path / "home" / ".cursor")
    assert sorted(os.listdir(agent_home)) == [".cursor"], "nothing but the link"
    assert same_path(out["GIT_CONFIG_GLOBAL"], str(tmp_path / "home" / ".gitconfig"))
    if os.name == "nt":
        assert out["HOMEDRIVE"] + out["HOMEPATH"] == out["USERPROFILE"]
    home = tmp_path / "home"
    for var, rel in (("HF_HUB_CACHE", "huggingface/hub"), ("TORCH_HOME", "torch"), ("PUPPETEER_CACHE_DIR", "puppeteer")):
        assert same_path(out[var], str(home / ".cache" / rel)), "%s: the cache is passed through by its own variable" % var
    hidden = {os.path.normcase(os.path.abspath(str(p))) for p in (home, home / ".cache", home / ".cache" / "huggingface")}
    for k, v in out.items():
        assert os.path.normcase(os.path.abspath(v)) not in hidden, "%s=%s would show the owner's token file again" % (k, v)
    assert "HF_HOME" not in out and "XDG_CACHE_HOME" not in out


def link_state(tmp_path, state):
    """Put the agent home's link into `state`: healthy, plain folder, dangling, elsewhere."""
    home = tmp_path / "home"
    link = home / ".cursor-bridge" / "agent-home" / ".cursor"
    link.parent.mkdir(parents=True, exist_ok=True)
    if state == "plain folder":
        link.mkdir()
        return
    target = {"healthy": home / ".cursor", "dangling": tmp_path / "gone", "elsewhere": tmp_path / "other"}[state]
    target.mkdir(exist_ok=True)
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], capture_output=True)
    else:
        os.symlink(str(target), str(link))
    if state == "dangling":
        target.rmdir()


def test_python_recipe_withholds_account_keys_and_keeps_the_rest(program, tmp_path):
    be = program("bridge_env")
    out = be.stripped_env(sample_env(tmp_path))
    for k in WITHHELD:
        assert k not in out, "%s must not reach a builder or reviewer run" % k
    for k in KEPT:
        assert k in out, "%s was withheld by mistake" % k
    assert out["GIT_CONFIG_KEY_0"] == "credential.helper", "the recipe's own variable must survive its own filter"
    assert_own_home(out, tmp_path)
    again = be.stripped_env(sample_env(tmp_path))
    assert again["HOME"] == out["HOME"], "a second run finds the folder and uses it"


@pytest.mark.parametrize("state", ["plain folder", "dangling", "elsewhere"])
def test_a_run_whose_link_is_not_the_owners_cursor_is_refused_by_both_recipes(program, tmp_path, state):
    """Review of 2026.10.06a, finding 2: the two recipes must decide alike on a damaged link,
    and the installer repairs a link that leads nowhere or elsewhere, never a plain folder."""
    be = program("bridge_env")
    env = sample_env(tmp_path)
    link_state(tmp_path, state)
    with pytest.raises(be.AgentHomeError, match="plain folder" if state == "plain folder" else "does not lead to"):
        be.stripped_env(env)
    if shutil.which("sh"):
        text = open(SHIM, encoding="utf-8").read()
        probe = tmp_path / "shim-probe.sh"
        probe.write_text(text.rstrip()[: -len('exec cursor-agent.cmd "$@"')] + "env\n", encoding="utf-8", newline="\n")
        p = subprocess.run([shutil.which("sh"), str(probe)], capture_output=True, text=True, env=env)
        assert p.returncode == 125 and "KP-038" in p.stderr, "the shim must refuse too: " + p.stdout + p.stderr
    home, problem = be.agent_home(env, create=True, repair=True)
    if state == "plain folder":
        assert "plain folder" in problem, "a plain folder is never removed"
    else:
        assert problem is None and os.path.samefile(os.path.join(home, ".cursor"), tmp_path / "home" / ".cursor"), "the installer repairs the link"
        assert "HOME" in be.stripped_env(env)


def test_a_healthy_link_is_accepted_and_the_rename_probe_passes(program, tmp_path):
    be = program("bridge_env")
    env = sample_env(tmp_path)
    link_state(tmp_path, "healthy")
    assert be.agent_home(env, create=False)[1] is None
    assert be.rename_probe(env) is None
    assert not os.path.lexists(tmp_path / "home" / ".cursor-bridge" / "probe-link") and not (tmp_path / "home" / ".cursor-bridge" / "probe-target").exists()


@pytest.mark.skipif(shutil.which("sh") is None, reason="needs a POSIX shell (Git Bash on Windows)")
def test_shim_withholds_exactly_what_the_python_recipe_does(program, tmp_path):
    """Run the shim's own text with its last line replaced by `env`, on the same sample."""
    text = open(SHIM, encoding="utf-8").read()
    assert text.rstrip().endswith('exec cursor-agent.cmd "$@"')
    probe = tmp_path / "shim-probe.sh"
    probe.write_text(text.rstrip()[: -len('exec cursor-agent.cmd "$@"')] + "env\n", encoding="utf-8", newline="\n")
    env = sample_env(tmp_path)
    p = subprocess.run([shutil.which("sh"), str(probe)], capture_output=True, text=True, env=env)
    assert p.returncode == 0, p.stderr
    names = {line.split("=", 1)[0] for line in p.stdout.splitlines() if "=" in line}
    be = program("bridge_env")
    expected = be.stripped_env(env)
    for k in WITHHELD:
        assert k not in names, "the shim lets %s through" % k
    for k in KEPT:
        assert k in names, "the shim withheld %s by mistake" % k
    for k in WITHHELD + KEPT:
        assert (k in names) == (k in expected), "shim and bridge_env disagree on %s" % k
    assert "GIT_CONFIG_KEY_0" in names and "BRIDGE_V" not in names
    values = dict(line.split("=", 1) for line in p.stdout.splitlines() if "=" in line)
    assert_own_home(values, tmp_path)
    assert not any(k.startswith("BRIDGE_") for k in values)


@pytest.mark.skipif(shutil.which("sh") is None, reason="needs a POSIX shell (Git Bash on Windows)")
def test_the_shim_refuses_a_run_whose_home_cannot_be_prepared(tmp_path):
    text = open(SHIM, encoding="utf-8").read()
    probe = tmp_path / "shim-probe.sh"
    probe.write_text(text.rstrip()[: -len('exec cursor-agent.cmd "$@"')] + "env\n", encoding="utf-8", newline="\n")
    env = sample_env(tmp_path)
    env["USERPROFILE"] = env["HOME"] = str(tmp_path / "home" / ".gitconfig")       # a file where the folder must be made
    p = subprocess.run([shutil.which("sh"), str(probe)], capture_output=True, text=True, env=env)
    assert p.returncode == 125 and "refused" in p.stderr and "KP-038" in p.stderr, p.stdout + p.stderr
