## Command design

### What this variant is

The command design is the interface phase's variant for commands a person types in a terminal (`interface.md`, "The variants"). It turns the agreed design into the commands as the owner will meet them, before any of them is built: what each command is called, what it asks for, what it says back. It is design documentation, written by you like a mockup, upstream of the author/reviewer split. Its artifact is `docs/design/COMMANDS.md`, one section per command, and the owner approves it at the phase's gate (`interface.md`, "The gate").

### Writing the command design

Write `docs/design/COMMANDS.md`, one section per command (and per subcommand), each with:

- **the command line:** its name, its arguments and options, each option's default and the values it accepts;
- **the help text,** word for word as `--help` will print it;
- **the output:** what it prints on success, in the human form and in any machine-readable form the design asks for (`--json`), and where the output goes (the terminal, a file);
- **the failures:** each error the owner can cause (a missing argument, a file that is not there, a service that is down), the message it prints, and its exit code; `0` for success and a stated code for each kind of failure;
- **an example session:** the commands typed and what each printed, for the command's main use.

**A secret is never an option's value.** A command that needs a key, a token or a password reads it from a key file outside the Workspace, asks for it at a prompt that does not echo it, or takes it from the product's own store; it never takes it as an argument, where it lands in the shell's history and in the list of running processes, and never from an environment variable the owner sets (founding rule N2, KP-032). An option may name the key file's path. The example sessions show such values only as plain placeholders, `<your key file>` or `<prompted, not shown>`, never as a string shaped like a real key.

The command design maps onto the agreed functionality **with no gaps, in both directions**, as a mockup does: every capability of `DESIGN.md` that a person reaches through a terminal has its command, and every command traces back to an agreed capability. Walk the design's feature list against the commands and account for each item before presenting. Add every command to `docs/REQUIREMENTS.md` as its own row (Source: command design "<command>"), unless an existing row already covers it.

### Approving the command design

**Gate:** present the example sessions and the help texts to the owner and get explicit approval of the command design before writing the build plan. The owner judges the commands as they will type and read them; the option parsing behind them is not theirs to judge. Do not proceed on a command design with unaccounted gaps in either direction against the design.

**The approved command design's authority** is a mockup's: guidance, not a contract to the letter. A better name for an option, or a clearer message, discovered during the build is fine and needs no re-approval; record it in `docs/CHANGES.md`. A command that does something other than what was approved, or a command added or removed, is a scope question and escalates to the owner. What was built is recorded by the command reference generated from the program itself where the product is installable (`Delivery-Conventions.md` §4), never by `docs/design/COMMANDS.md`, which stays the record of what was approved.
