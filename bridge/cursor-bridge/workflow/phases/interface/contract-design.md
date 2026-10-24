## Contract design

### What this variant is

The contract design is the interface phase's variant for a protocol other software calls, such as an MCP server's tools or a local API (`interface.md`, "The variants"). Its user is a program, so what the owner approves is what the part offers, in plain words; the contract's exact form is technical and is enforced by tests, not judged by the owner. Its artifacts are `docs/design/CONTRACT.md`, which states in plain words every operation the part offers, and the machine-readable contract file `CONTRACT.md` names, which tests enforce; the owner approves what the part offers, from `CONTRACT.md`, at the phase's gate (`interface.md`, "The gate").

### Writing the contract design

Write two things. **`docs/design/CONTRACT.md`**, in plain words: every operation the part offers, what it is for, what it needs, what it gives back, and each way it can fail, with one example call and reply per operation. **The contract file**, at the path `CONTRACT.md` names, in the protocol's own machine-readable form (a JSON Schema per operation, an OpenAPI document, an MCP tool list): each operation's name, its inputs with their types and which are required, its outputs, its errors with their codes, and the contract's version.

**Each operation says who may call it.** Its entry in both files names the callers it accepts (any local program, a program holding the part's token, only the part's own front end) and how a call from anyone else is refused: the error it returns, its code, and that the refused call changes nothing. An operation open to every caller says so in those words. The increment that enforces the contract then tests the refusals as well as the shapes of the replies. A credential an operation needs travels as the protocol carries one (a header, the MCP session's authentication), never as an ordinary input, and the example calls show it only as a plain placeholder, `<token>`, never as a string shaped like a real key.

State in `CONTRACT.md` how the version changes: what counts as a breaking change (an operation removed or renamed, an input made required, an output's meaning changed, a caller refused that was accepted), and that a breaking change raises the major version.

The contract maps onto the agreed functionality **with no gaps, in both directions**, as a mockup does: every capability of `DESIGN.md` that other software reaches through the protocol has its operation, and every operation traces back to an agreed capability. Add every operation to `docs/REQUIREMENTS.md` as its own row (Source: contract operation "<operation>"), unless an existing row already covers it. The build plan then carries the increment whose tests check the built part against the contract file (`planning.md`, "What the interface phase hands to the plan"), so that the contract is enforced, never only described.

Where the part also has commands a person types (a service's administrative commands), those get the command design too (`interface/command-design.md`).

### Approving the contract design

**Gate:** present `CONTRACT.md`'s operations, in plain words with their example calls and who may make each, to the owner and get explicit approval of what the part offers before writing the build plan. Do not proceed on a contract with unaccounted gaps in either direction against the design.

**After approval,** a change that keeps every approved operation working as approved **and adds none** (an optional input, a clearer error message) is recorded in `docs/CHANGES.md`. An added operation escalates to the owner as a scope question, as a breaking change does: an operation is something the part offers that the owner has not approved, whether or not anything that was approved stops working.
