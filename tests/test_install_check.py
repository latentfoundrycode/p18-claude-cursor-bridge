"""bridge-install.py and bridge-check.py: the owner's settings survive an install, the
bridge's entries are added once, and the check verifies entries rather than bytes (KP-030)."""
import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
RELEASE = os.path.abspath(os.path.join(HERE, os.pardir, ".claude"))
INSTALL = os.path.join(RELEASE, "cursor-bridge", "bridge-install.py")
CHECK = os.path.join(RELEASE, "cursor-bridge", "bridge-check.py")
BRIDGE_SETTINGS = json.load(open(os.path.join(RELEASE, "cursor-bridge", "settings.bridge.json"), encoding="utf-8"))

OWNER_SETTINGS = {
    "switchModelsOnFlag": True,
    "fastMode": False,
    "modelSettings": {"claude-opus-4-8": {"effort": "high"}},
    "permissions": {"allow": ["Bash(ls:*)", "Bash(git status:*)"], "additionalDirectories": ["E:/somewhere"]},
    "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "echo hi"}]}]},
}


def run(prog, *args):
    p = subprocess.run([sys.executable, prog] + list(args), capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def test_merge_keeps_owner_keys_and_adds_bridge_entries(program):
    bi = program("bridge-install")
    merged, changes = bi.merge_settings(OWNER_SETTINGS, BRIDGE_SETTINGS)
    assert merged["switchModelsOnFlag"] is True and merged["modelSettings"] == OWNER_SETTINGS["modelSettings"]
    assert merged["permissions"]["additionalDirectories"] == ["E:/somewhere"]
    assert merged["permissions"]["allow"][:2] == ["Bash(ls:*)", "Bash(git status:*)"], "the owner's entries keep their place"
    for entry in BRIDGE_SETTINGS["permissions"]["allow"]:
        assert entry in merged["permissions"]["allow"]
    for entry in BRIDGE_SETTINGS["permissions"]["deny"]:
        assert entry in merged["permissions"]["deny"]
    assert merged["hooks"]["PreToolUse"] == OWNER_SETTINGS["hooks"]["PreToolUse"]
    assert any("loop-guard" in h["command"] for g in merged["hooks"]["Stop"] for h in g["hooks"])
    assert changes
    again, changes2 = bi.merge_settings(merged, BRIDGE_SETTINGS)
    assert again == merged and changes2 == [], "a second merge changes nothing"


def test_install_into_a_fresh_target_passes_the_check(tmp_path):
    target = tmp_path / ".claude"
    rc, out = run(INSTALL, "--target", str(target))
    assert rc == 0, out
    assert (target / "commands" / "supervisor.md").is_file()
    assert (target / "cursor-bridge" / "bridge-check.py").is_file()
    assert "RESULT: INSTALLED TREE MATCHES" in out
    settings = json.load(open(target / "settings.json", encoding="utf-8"))
    assert settings["permissions"]["deny"] == BRIDGE_SETTINGS["permissions"]["deny"]


def test_install_over_owner_settings_keeps_them_and_backs_up(tmp_path):
    target = tmp_path / ".claude"
    target.mkdir()
    (target / "settings.json").write_text(json.dumps(OWNER_SETTINGS, indent=2), encoding="utf-8")
    rc, out = run(INSTALL, "--target", str(target))
    assert rc == 0, out
    settings = json.load(open(target / "settings.json", encoding="utf-8"))
    assert settings["switchModelsOnFlag"] is True and settings["permissions"]["additionalDirectories"] == ["E:/somewhere"]
    assert any(p.name.startswith("settings.json.bak-") for p in target.iterdir())
    assert "owner keys kept" in out


def test_check_reports_missing_bridge_entry_and_ignores_owner_keys(tmp_path):
    target = tmp_path / ".claude"
    rc, out = run(INSTALL, "--target", str(target))
    assert rc == 0, out
    path = target / "settings.json"
    settings = json.load(open(path, encoding="utf-8"))
    settings["switchModelsOnFlag"] = True                      # an owner key: must not matter
    path.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    rc, out = run(CHECK, "--root", str(target))
    assert rc == 0 and "owner keys kept: switchModelsOnFlag" in out, out
    settings["permissions"]["allow"].remove("Bash(cursor-agent:*)")
    path.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    rc, out = run(CHECK, "--root", str(target))
    assert rc == 1 and "STALE    settings.json" in out and "Bash(cursor-agent:*)" in out, out


def test_dry_run_writes_nothing(tmp_path):
    target = tmp_path / ".claude"
    rc, out = run(INSTALL, "--target", str(target), "--dry-run")
    assert rc == 0 and not target.exists(), out
