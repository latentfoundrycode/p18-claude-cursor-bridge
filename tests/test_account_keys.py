"""Account keys are withheld from builder and reviewer runs (2026.10.04e): release 0b told
projects to move paid keys "to the user's environment", which hands them to every process
the owner starts, while the launcher withheld only GitHub variables. The Python recipe
(bridge_env.stripped_env) and the shell recipe (cursor-agent.shim) must decide the same way."""
import os
import shutil
import subprocess

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
SHIM = os.path.join(HERE, os.pardir, ".claude", "cursor-bridge", "cursor-agent.shim")

WITHHELD = ["ANTHROPIC_API_KEY", "OPENROUTER_API_KEY", "AZURE_DI_API_KEY", "MODAL_TOKEN_ID", "MODAL_TOKEN_SECRET",
            "HF_TOKEN", "NPM_TOKEN", "SOCKET_CLI_API_TOKEN", "SEMGREP_APP_TOKEN", "STRIPE_SECRET_KEY",
            "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "PGPASSWORD", "MINIO_ROOT_PASSWORD", "MY_PRIVATE_KEY",
            "GOOGLE_APPLICATION_CREDENTIALS", "LLM_APIKEY", "GH_TOKEN", "GITHUB_TOKEN", "TOKEN", "SECRET"]
KEPT = ["PATH", "HOME", "CURSOR_API_KEY", "CURSOR_TOKEN", "TOKENIZERS_PARALLELISM", "SECRETARY", "KEYBOARD_LAYOUT",
        "MONKEY", "PYTHONUTF8", "DATABASE_URL", "REANGLE_INSTANCE_NAME", "LOG_LEVEL"]


def sample_env(tmp_path):
    env = {k: "v" for k in WITHHELD + KEPT}
    env["PATH"] = os.environ.get("PATH", "")
    env["LOCALAPPDATA"] = str(tmp_path)
    for k in ("SYSTEMROOT", "SystemRoot", "TEMP", "TMP", "COMSPEC", "PATHEXT"):
        if k in os.environ:
            env[k] = os.environ[k]
    return env


def test_python_recipe_withholds_account_keys_and_keeps_the_rest(program, tmp_path):
    be = program("bridge_env")
    out = be.stripped_env(sample_env(tmp_path))
    for k in WITHHELD:
        assert k not in out, "%s must not reach a builder or reviewer run" % k
    for k in KEPT:
        assert k in out, "%s was withheld by mistake" % k
    assert out["GIT_CONFIG_KEY_0"] == "credential.helper", "the recipe's own variable must survive its own filter"


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
