"""R-026: the interface text for command design and contract design is written (TASK-022).

enforces: docs/REQUIREMENTS.md R-026; docs/BUILD_PLAN.md, TASK-022, Done when (the artifacts, the gates, the three
rules added at TASK-012's gate: an added operation escalates, each operation says who may call it and how a refused
call fails, a secret is never a command's option value and examples use plain placeholders; no stand-in wording).

Supervisor-written: the variant bodies are governance text, authored and tested by the supervisor."""
import importlib.util
import os

from phase_modules import BRIDGE, module, flat, headings, section

CB = os.path.join(BRIDGE, "cursor-bridge")
COMMAND = "interface/command-design.md"
CONTRACT = "interface/contract-design.md"


def standin_rx():
    spec = importlib.util.spec_from_file_location("completion_check_interface_text", os.path.join(CB, "completion-check.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.STANDIN_RX


def test_r026_the_variant_files_have_their_body_sections():
    """R-026: each file keeps its heading and declaring paragraph (TASK-012, TASK-014) and gains its body under
    headings of its own, so each `new` trace entry excuses one section and the declaring one stays as pinned."""
    assert headings(module(COMMAND)) == [(2, "Command design"), (3, "What this variant is"),
                                         (3, "Writing the command design"), (3, "Approving the command design")]
    assert headings(module(CONTRACT)) == [(2, "Contract design"), (3, "What this variant is"),
                                          (3, "Writing the contract design"), (3, "Approving the contract design")]


def test_r026_the_command_design_writes_its_artifact_section_by_section():
    """R-026, §6.9: the command design writes docs/design/COMMANDS.md, one section per command, with the command line,
    the help text word for word, the output in each form, the failures with their exit codes and an example session;
    it maps onto the design in both directions and adds each command to the register."""
    w = flat(section(module(COMMAND), "Writing the command design", 3))
    for s in ("Write `docs/design/COMMANDS.md`, one section per command (and per subcommand), each with:",
              "**the command line:** its name, its arguments and options, each option's default and the values it accepts;",
              "**the help text,** word for word as `--help` will print it;",
              "**the output:** what it prints on success, in the human form and in any machine-readable form",
              "**the failures:** each error the owner can cause",
              "and its exit code; `0` for success and a stated code for each kind of failure;",
              "**an example session:** the commands typed and what each printed",
              "maps onto the agreed functionality **with no gaps, in both directions**, as a mockup does",
              "Add every command to `docs/REQUIREMENTS.md` as its own row (Source: command design \"<command>\")"):
        assert s in w, s


def test_r026_a_secret_is_never_a_commands_option_value():
    """R-026 (TASK-012's security audit, advisory 3): a key, token or password comes from a key file outside the
    Workspace, a prompt that does not echo, or the product's store; never an argument, never an environment variable
    the owner sets (N2, KP-032); example sessions show such values only as plain placeholders."""
    w = flat(section(module(COMMAND), "Writing the command design", 3))
    for s in ("**A secret is never an option's value.**",
              "reads it from a key file outside the Workspace, asks for it at a prompt that does not echo it, or takes "
              "it from the product's own store; it never takes it as an argument",
              "never from an environment variable the owner sets (founding rule N2, KP-032)",
              "The example sessions show such values only as plain placeholders, `<your key file>` or "
              "`<prompted, not shown>`, never as a string shaped like a real key."):
        assert s in w, s


def test_r026_the_command_designs_gate_and_authority():
    """R-026: the command design has its own **Gate:** before the plan; after approval it is a mockup's guidance, a
    command added, removed or changed in what it does escalates as scope, and the generated command reference, never
    docs/design/COMMANDS.md, records what was built (Review A, TASK-012)."""
    g = flat(section(module(COMMAND), "Approving the command design", 3))
    for s in ("**Gate:** present the example sessions and the help texts to the owner and get explicit approval of the "
              "command design before writing the build plan.",
              "Do not proceed on a command design with unaccounted gaps in either direction against the design.",
              "A command that does something other than what was approved, or a command added or removed, is a scope "
              "question and escalates to the owner.",
              "never by `docs/design/COMMANDS.md`, which stays the record of what was approved."):
        assert s in g, s


def test_r026_the_contract_design_writes_both_artifacts_and_its_versioning():
    """R-026, §6.8: the contract design writes docs/design/CONTRACT.md in plain words and the machine-readable contract
    file it names, states what a breaking change is and that it raises the major version, maps onto the design in both
    directions, and points to the plan's contract-enforcement increment."""
    w = flat(section(module(CONTRACT), "Writing the contract design", 3))
    for s in ("**`docs/design/CONTRACT.md`**, in plain words: every operation the part offers",
              "**The contract file**, at the path `CONTRACT.md` names, in the protocol's own machine-readable form",
              "its errors with their codes, and the contract's version.",
              "State in `CONTRACT.md` how the version changes: what counts as a breaking change",
              "and that a breaking change raises the major version.",
              "maps onto the agreed functionality **with no gaps, in both directions**, as a mockup does",
              "Add every operation to `docs/REQUIREMENTS.md` as its own row (Source: contract operation \"<operation>\")",
              "(`planning.md`, \"What the interface phase hands to the plan\"), so that the contract is enforced, never "
              "only described.",
              "those get the command design too (`interface/command-design.md`)."):
        assert s in w, s


def test_r026_each_operation_says_who_may_call_it_and_how_a_refusal_fails():
    """R-026 (TASK-012's security audit, advisory 2): each operation names its callers and how anyone else is refused
    (the error, its code, nothing changed), so the enforcing increment tests refusals as well as shapes; a credential
    travels as the protocol carries one and examples show it as a placeholder."""
    w = flat(section(module(CONTRACT), "Writing the contract design", 3))
    for s in ("**Each operation says who may call it.**",
              "and how a call from anyone else is refused: the error it returns, its code, and that the refused call "
              "changes nothing.",
              "An operation open to every caller says so in those words.",
              "The increment that enforces the contract then tests the refusals as well as the shapes of the replies.",
              "never as an ordinary input, and the example calls show it only as a plain placeholder, `<token>`"):
        assert s in w, s


def test_r026_the_contract_designs_gate_and_an_added_operation_escalates():
    """R-026 (TASK-012's security audit, advisory 1): the contract design has its own **Gate:**; after approval only a
    change that keeps every approved operation working and adds none is recorded in docs/CHANGES.md; an added
    operation escalates as a breaking change does."""
    g = flat(section(module(CONTRACT), "Approving the contract design", 3))
    for s in ("**Gate:** present `CONTRACT.md`'s operations, in plain words with their example calls and who may make "
              "each, to the owner and get explicit approval of what the part offers before writing the build plan.",
              "Do not proceed on a contract with unaccounted gaps in either direction against the design.",
              "a change that keeps every approved operation working as approved **and adds none**",
              "is recorded in `docs/CHANGES.md`.",
              "An added operation escalates to the owner as a scope question, as a breaking change does"):
        assert s in g, s


def test_r026_neither_file_carries_stand_in_wording():
    """R-026, TASK-022's Done when: completion-check.py's stand-in patterns find nothing in either file, so a body
    left as a placeholder cannot pass."""
    rx = standin_rx()
    for rel in (COMMAND, CONTRACT):
        for n, line in enumerate(module(rel).split("\n"), 1):
            assert not rx.search(line), (rel, n, line)
