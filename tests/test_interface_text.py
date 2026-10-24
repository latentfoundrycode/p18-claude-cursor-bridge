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
              "no failure message, `--json` output or verbose mode prints a secret or a key file's contents, not even "
              "the line of a key file it could not read;",
              "**an example session:** the commands typed and what each printed",
              "maps onto the agreed functionality **with no gaps, in both directions**, as a mockup does",
              "Add every command to `docs/REQUIREMENTS.md` as its own row (Source: command design \"<command>\")"):
        assert s in w, s


def test_r026_a_secret_is_never_a_commands_option_value():
    """R-026 (TASK-012's security audit, advisory 3; TASK-022's audit and Review A): a key, token or password comes
    from a key file outside the Workspace, a prompt that does not echo, the product's encrypted store or the system's
    credential store, as N2 and KP-032 name them; never an argument, never an environment variable the owner sets; a
    store's passphrase is a secret too; examples show such values only as plain placeholders, and a credential a
    command creates is shown once."""
    w = flat(section(module(COMMAND), "Writing the command design", 3))
    for s in ("**A secret is never an option's value.**",
              "reads it from a key file outside the Workspace, asks for it at a prompt that does not echo it, or takes "
              "it from the product's encrypted store or the system's credential store; it never takes it as an argument",
              "A store's unlock passphrase is a secret under the same rule.",
              "A command that creates or rotates a credential shows it once: its example shows "
              "`<shown once, not reproduced>`, and none of the command's other output repeats it.",
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
              "the command reference generated from the program itself, which every project with a command-line "
              "surface keeps (`Delivery-Conventions.md` §4), never by `docs/design/COMMANDS.md`, which stays the record "
              "of what was approved."):
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
              "(an operation removed or renamed, an input made required or its type narrowed, an output's meaning "
              "changed, an error's code changed, a caller refused that was accepted)",
              "and that a breaking change raises the major version and escalates to the owner as a scope question.",
              "maps onto the agreed functionality **with no gaps, in both directions**, as a mockup does",
              "Add every operation to `docs/REQUIREMENTS.md` as its own row (Source: contract operation \"<operation>\")",
              "(`planning.md`, \"What the interface phase hands to the plan\"), so that the contract is enforced, never "
              "only described.",
              "those get the command design too (`interface/command-design.md`)."):
        assert s in w, s


def test_r026_each_operation_says_who_may_call_it_and_how_the_part_tells():
    """R-026 (TASK-012's security audit, advisory 2; TASK-022's security audit, blocking 1): each operation names its
    callers and the mechanism that tells them apart, never a claim the caller makes: loopback with Host and Origin
    checked for any local program, a checked secret for a token holder or the part's own front end; an operation that
    changes something or reads private data is open to any local program only on the owner's word."""
    w = flat(section(module(CONTRACT), "Writing the contract design", 3))
    for s in ("**Each operation says who may call it, and how the part tells.**",
              "names the callers it accepts and the mechanism that tells them apart, never a claim the caller makes "
              "about itself.",
              "*Any local program* means the part listens on the loopback address only and, where it speaks HTTP, checks "
              "the Host and Origin headers and refuses a call from a web page",
              "*A program holding the part's token* means a secret the caller presents and the part checks.",
              "*Only the part's own front end* means a secret the front end holds, never an Origin header or a client id.",
              "*Only the client that started it* means a server an MCP client starts over its standard input and "
              "output: it opens no listening socket, so its one caller is the process holding its pipes",
              "An operation that changes something or reads the owner's private data is open to any local program only "
              "if the owner approves exactly that at the gate.",
              "An operation open to every caller says so in those words."):
        assert s in w, s


def test_r026_each_operation_bounds_what_its_inputs_may_reach():
    """R-026 (TASK-022's security audit, blocking 2): each operation states what its inputs may reach (a folder, the
    caller's records, hosts), the bound that path traversal and access to another's records cross, and for an MCP
    server the bound that a steered model tests."""
    w = flat(section(module(CONTRACT), "Writing the contract design", 3))
    for s in ("**Each operation says what its inputs may reach:** the folder a path must stay inside, the records a "
              "caller may read or change, the hosts it may fetch from.",
              "For an MCP server this bound carries the most risk, because its caller is a model that a page or a "
              "document it read can steer."):
        assert s in w, s


def test_r026_a_refused_call_changes_nothing_reveals_nothing_and_is_tested():
    """R-026 (TASK-012's security audit, advisory 2; TASK-022's audit): a call from a caller not accepted, or reaching
    outside its bound, is refused with the named error, changes nothing, echoes no credential and does not tell
    "not yours" from "not there"; the enforcing increment tests each refusal, the browser-origin and Host cases too."""
    w = flat(section(module(CONTRACT), "Writing the contract design", 3))
    for s in ("**A refused call changes nothing and reveals nothing.**",
              "or one whose input reaches outside its bound, is refused with the error and the code the entry names.",
              "The refusal does not echo the credential presented, and it does not tell a thing that exists but is not "
              "the caller's apart from a thing that does not exist.",
              "The increment that enforces the contract then tests the refusals as well as the shapes of the replies: a "
              "call without the secret and one with a wrong secret, a call reaching outside its bound and, where the part "
              "speaks HTTP, a call from a web page's origin and one with a wrong Host header."):
        assert s in w, s


def test_r026_credentials_travel_as_the_protocol_carries_them_and_live_where_n2_puts_them():
    """R-026 (TASK-022's audit, advisories): a credential is never an ordinary input or a query-string value, examples
    show placeholders, and the part's keys and the tokens it issues live in N2's homes, never an environment variable
    the owner sets; a server an MCP client starts reads the key file the client's configuration names."""
    w = flat(section(module(CONTRACT), "Writing the contract design", 3))
    for s in ("never as an ordinary input and never in a URL's query string, and the example calls show it only as a "
              "plain placeholder, `<token>`",
              "live where founding rule N2 puts a secret: a key file outside the Workspace, the product's encrypted store "
              "or the system's credential store, never an environment variable the owner sets (KP-032).",
              "A server an MCP client starts therefore reads the key file the client's configuration names, and the "
              "configuration never holds the key."):
        assert s in w, s


def test_r026_the_contract_designs_gate_and_an_added_operation_escalates():
    """R-026 (TASK-012's security audit, advisory 1; TASK-022's Review A and audit, convergent on the widened caller):
    the contract design has its own **Gate:**; after approval only a change that keeps every approved operation
    working, adds none and widens none is recorded in docs/CHANGES.md; a breaking change, an added operation and a
    widened one (a caller accepted that was refused, an input reaching beyond its bound) escalate."""
    g = flat(section(module(CONTRACT), "Approving the contract design", 3))
    for s in ("**Gate:** present `CONTRACT.md`'s operations, in plain words with their example calls, who may make "
              "each and what each may reach, to the owner and get explicit approval of what the part offers before "
              "writing the build plan.",
              "Do not proceed on a contract with unaccounted gaps in either direction against the design.",
              "a change that keeps every approved operation working as approved, **adds none and widens none**",
              "is recorded in `docs/CHANGES.md`.",
              "A breaking change escalates to the owner as a scope question, and so do an added operation and a widened "
              "one: a caller accepted that the approved entry refuses, or an input allowed to reach beyond its approved "
              "bound."):
        assert s in g, s


def test_r026_neither_file_carries_stand_in_wording():
    """R-026, TASK-022's Done when: completion-check.py's stand-in patterns, shown first to match two stand-ins (a
    weakened pattern would pass any wording; Review A, TASK-012 and TASK-022), find nothing in either file, so a body
    left as a placeholder cannot pass."""
    rx = standin_rx()
    assert rx.search("this screen arrives in a later release") and rx.search("coming soon"), "the patterns match nothing"
    for rel in (COMMAND, CONTRACT):
        for n, line in enumerate(module(rel).split("\n"), 1):
            assert not rx.search(line), (rel, n, line)
