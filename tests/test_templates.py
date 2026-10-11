"""The templates (release A4, the plan review's R24): the bundled Semgrep rules parse and carry the
schema's keys; the project template names no registry pack inside the file; the Inno Setup
template escapes the GUID in [Setup] only and refuses Arm64; the detector's pin floor is the
first version with projectRoots; the subagents that run commands never leave a waiter behind."""
import os
import re

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
BRIDGE = os.path.join(HERE, os.pardir, "bridge")


def text(*parts):
    with open(os.path.join(BRIDGE, *parts), encoding="utf-8") as f:
        return f.read()


def test_the_bundled_semgrep_rules_are_rules():
    doc = yaml.safe_load(text("cursor-bridge", "semgrep-bridge-rules.yml"))
    assert isinstance(doc, dict) and isinstance(doc.get("rules"), list) and doc["rules"], doc
    for rule in doc["rules"]:
        assert isinstance(rule, dict), rule
        for key in ("id", "languages", "severity", "message"):
            assert key in rule, (rule.get("id"), key)
        assert "pattern" in rule or "patterns" in rule or "pattern-either" in rule, rule.get("id")


def test_the_project_template_names_no_registry_pack_inside_the_file():
    formats = text("cursor-bridge", "Cursor-File-Formats.md")
    block = formats.split("## `.semgrep.yml`", 1)[1].split("\n## ", 1)[0]
    yaml_blocks = re.findall(r"```yaml\n(.*?)```", block, re.S)
    assert yaml_blocks, "the template has a yaml example"
    for y in yaml_blocks:
        doc = yaml.safe_load(y)
        assert all(isinstance(r, dict) for r in doc.get("rules", [])), "a registry pack listed as a string under rules: is not valid (R24): " + y
    assert "--config p/default" in block and "--config .semgrep/bridge-rules.yml" in block, "the packs go on the gate command"


def test_the_inno_template_escapes_the_guid_in_setup_only_and_refuses_arm64():
    delivery = text("cursor-bridge", "Delivery-Conventions.md")
    assert '#define AppGuid "' in delivery and "AppId={{{#AppGuid}}" in delivery, "the bare GUID, escaped in [Setup]"
    assert "'{#AppId}'" not in delivery and "'{' + '{#AppGuid}' + '}' + '_is1'" in delivery, "inside [Code] the braces are added by hand (R24)"
    assert not re.search(r"^Architectures\w+=x64compatible", delivery, re.M) and "ArchitecturesAllowed=x64os" in delivery and "ArchitecturesInstallIn64BitMode=x64os" in delivery, "x64compatible admits Arm64 hosts (R24)"
    ps1 = text("cursor-bridge", "installer-check.ps1")
    assert '[ValidateSet("x64", "x86", "arm64")][string]$Arch' in ps1 and "0x8664" in ps1 and "0xAA64" in ps1, "the installer check reads the executable's machine type"


def test_the_detector_pin_floor_is_the_first_with_project_roots():
    assert "pin ≥ v3.3.0" in text("cursor-bridge", "Cursor-Project-Configuration.md") and "v3.0.2" not in text("cursor-bridge", "Cursor-Project-Configuration.md")


def test_every_subagent_that_runs_commands_leaves_no_waiter_behind():
    for name in sorted(os.listdir(os.path.join(BRIDGE, "agents"))):
        body = text("agents", name)
        tools = re.search(r"^tools:\s*(.*)$", body, re.M)
        if tools and "Bash" in tools.group(1):
            assert "never a polling loop" in body and "KP-042" in body, name
