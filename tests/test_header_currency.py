"""TASK-050, the supervisor's currency test (R-057; D-002), at the end of the program readers' increments: every
record kind bridge_env holds a fallback reader for has its schema in HEADER_SCHEMAS, every key a stated type, and no
program under bridge/cursor-bridge/ keeps a reading of the design's enumerated list of eleven, each matched as a use
(a `re` call's argument, a constant set, a call's argument, or the name of a function defined or used), with
docstrings stripped by `ast`, so a description never matches (KP-073).

enforces: docs/DESIGN.md, "Change: release B2", "The fallback readers, one copy each" and "The retired readings,
enumerated"; docs/BUILD_PLAN.md, TASK-050's Done when; R-057.

Two of the eleven are matched in their own program only, because another program keeps a like form for another
purpose by design: (2) the four exact `Awaiting user on:` values in session-start.py (loop-guard.py keeps the set for
its own normalisation); (4) the `Phase: ` reading in conformance-check.py (workflow-check.py keeps its placement
check). The others are matched over the twelve programs that read a dual-read record.

The supervisor's cases stand above the marker at the end of this file. The builder adds its own cases below the
marker and edits nothing above it.
"""
import ast
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIDGE = os.path.join(ROOT, "bridge", "cursor-bridge")
sys.path.insert(0, BRIDGE)
import bridge_env  # noqa: E402

TWELVE = ["loop-guard.py", "session-start.py", "conformance-check.py", "workflow-check.py", "inventory-check.py",
          "evaluate-reports.py", "plan-check.py", "scope-check.py", "completion-check.py", "diagram-check.py",
          "bridge-run.py", "review-guard.py"]
KINDS = ["project-status", "build-plan", "brief", "inventory", "requirements", "diagram-index", "deviations",
         "run-parameters"]
FALLBACKS = {"project-status": "status_fallback", "build-plan": "plan_prose_fallback", "brief": "brief_prose_fallback",
             "inventory": "inventory_fallback", "requirements": "register_fallback",
             "diagram-index": "diagram_index_fallback", "deviations": "deviations_fallback",
             "run-parameters": "run_parameters_fallback"}


def code_tree(program):
    with open(os.path.join(BRIDGE, program), encoding="utf-8") as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and body:
            first = body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                node.body = body[1:] or [ast.Pass()]
    return tree


def re_patterns(tree):
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) \
                and n.func.value.id == "re" and n.args and isinstance(n.args[0], ast.Constant) \
                and isinstance(n.args[0].value, str):
            out.append(n.args[0].value)
    return out


def names(tree):
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Name):
            out.add(n.id)
        elif isinstance(n, ast.Attribute):
            out.add(n.attr)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.add(n.name)
    return out


def defined(tree):
    return {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def constant_sets(tree):
    for n in ast.walk(tree):
        if isinstance(n, (ast.Tuple, ast.List, ast.Set)) and n.elts and \
                all(isinstance(e, ast.Constant) and isinstance(e.value, str) for e in n.elts):
            yield frozenset(e.value for e in n.elts)


def call_args(tree, name):
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            called = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else None)
            if called == name:
                yield [a.value for a in n.args if isinstance(a, ast.Constant)]


def whole_file_r_rx(tree):
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ("findall", "finditer", "search") \
                and isinstance(n.func.value, ast.Name) and n.func.value.id == "R_RX" and n.args \
                and isinstance(n.args[0], ast.Call) and isinstance(n.args[0].func, ast.Name) and n.args[0].func.id == "read":
            out.append(n.lineno)
    return out


# ---------------------------------------------------------------- the schemas and the fallbacks

def test_r057_every_record_kind_has_its_schema_and_its_fallback():
    for kind in KINDS:
        assert kind in bridge_env.HEADER_SCHEMAS, kind
        assert callable(getattr(bridge_env, FALLBACKS[kind], None)), "bridge_env.%s is missing" % FALLBACKS[kind]


def test_r057_every_schema_key_has_a_stated_type():
    for kind, schema in bridge_env.HEADER_SCHEMAS.items():
        assert isinstance(schema, dict) and schema, kind
        for key, typ in schema.items():
            assert isinstance(typ, str) and typ.strip(), "%s.%s has no stated type" % (kind, key)


def test_r057_the_run_parameters_fallback_gives_the_schemas_keys():
    fallback = getattr(bridge_env, "run_parameters_fallback", None)
    assert fallback is not None, "bridge_env.run_parameters_fallback is missing (TASK-050)"
    keys = [k for k in bridge_env.HEADER_SCHEMAS["run-parameters"] if k not in ("record", "header")]
    assert list(fallback("# Run parameters\n")) == keys


# ---------------------------------------------------------------- the eleven retired readings, as uses

def reading_1(tree):
    return sorted(names(tree) & {"parse_workflows_tail", "workflows_lines_parsed"})


def reading_2(tree):
    return ["the four exact values"] if frozenset(["nothing", "none", "", "-"]) in set(constant_sets(tree)) else []


def reading_3(tree):
    return [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)
            and "[0-9.]+[a-z]?" in n.value]


def reading_4(tree):
    return ([a for a in call_args(tree, "status_field") if "Phase" in a]
            + [a for a in call_args(tree, "startswith") if "Phase: " in a])


def reading_5(tree):
    return [p for p in re_patterns(tree) if "Satisfies" in p]


def reading_6(tree):
    return sorted(defined(tree) & {"brief_scope"})


def reading_7(tree):
    return [p for p in re_patterns(tree) if p == r"^##\s+(\w+)"]


def reading_8(tree):
    return ([] if "diagram_index_selected_ids" in names(tree) else ["no call of bridge_env.diagram_index_selected_ids"])


def reading_9(tree):
    return whole_file_r_rx(tree)


def reading_10(tree):
    return [p for p in re_patterns(tree) if "Ceiling above twice" in p]


def reading_11(tree):
    return sorted(defined(tree) & {"merged_ids"})


CASES = (
    [("1", p, reading_1) for p in TWELVE]
    + [("2", "session-start.py", reading_2)]
    + [("3", p, reading_3) for p in TWELVE]
    + [("4", "conformance-check.py", reading_4)]
    + [("5", "completion-check.py", reading_5)]
    + [("6", p, reading_6) for p in TWELVE]
    + [("7", p, reading_7) for p in TWELVE]
    + [("8", "plan-check.py", reading_8)]
    + [("9", p, reading_9) for p in TWELVE]
    + [("10", p, reading_10) for p in TWELVE]
    + [("11", p, reading_11) for p in TWELVE]
)


@pytest.mark.parametrize("number,program,match", CASES,
                         ids=["reading-%s-%s" % (n, p[:-3]) for n, p, _ in CASES])
def test_r057_no_program_keeps_a_retired_reading(number, program, match):
    found = match(code_tree(program))
    assert not found, "%s keeps retired reading (%s): %s" % (program, number, found)


# ---------------------------------------------------------------- builder's cases below this line


def test_r057_run_parameters_fallback_is_the_only_ceiling_above_twice_reader():
    """R-057: CEILING_LIFT_RE lives in bridge_env alone; loop-guard does not keep a copy."""
    assert hasattr(bridge_env, "CEILING_LIFT_RE")
    lg_tree = code_tree("loop-guard.py")
    assert not reading_10(lg_tree)
