## Contract design

### What this variant is

The contract design is the interface phase's variant for a protocol other software calls, such as an MCP server's tools or a local API (`interface.md`, "The variants"). Its user is a program, so what the owner approves is what the part offers, in plain words; the contract's exact form is technical and is enforced by tests, not judged by the owner. Its artifacts are `docs/design/CONTRACT.md`, which states in plain words every operation the part offers, and the machine-readable contract file `CONTRACT.md` names, which tests enforce; the owner approves what the part offers, from `CONTRACT.md`, at the phase's gate (`interface.md`, "The gate").
