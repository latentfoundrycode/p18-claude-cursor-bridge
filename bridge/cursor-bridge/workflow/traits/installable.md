# Installable

## Add at intake.questions

For **installable software** — a desktop application, a command-line tool, a local server
— the platform context includes the **delivery**: the project ends with one file the owner
double-clicks on Windows 11 x64 that installs it, upgrades it in place, and uninstalls it
cleanly, per `~/.claude/cursor-bridge/Delivery-Conventions.md` §1 (which kind ships what).
Confirm the kind and the target (Windows 11 x64 unless the user says otherwise), whether it
must be per-machine (a service, a driver, a machine-wide file association) or can be
per-user (the default, no administrator prompt), where its data should live, and — for
anything with a command-line surface — that a generated **command reference** will exist
(§4). This is not optional and not a late addition: it is a stage of the build plan.

### Which delivery kinds the intake passage is for

The passage confirms the kind first; what follows the confirmation is for the kinds `installer` and `install-script`, and a part whose confirmed kind is another takes its delivery questions from its type workflow, if any.

## Add at design.sections

For **installable software** it also has a **Delivery** section
(`~/.claude/cursor-bridge/Delivery-Conventions.md` §6): the kind (§1), the toolchain for
this stack (§2.1 for a desktop app; the install-script contract of §3 for a CLI or local
server), per-user or per-machine with the reason, the data location, the single version
source, whether a server runs as a service, the command-reference generator for any CLI
(§4), and the installer behaviour (already installed → Upgrade / Uninstall / Cancel;
upgrade in place keeps data; uninstall keeps data unless opted out).

### Code signing

**Code signing is the one escalation here**: a certificate costs money and identity verification, so present it once as a user-level consequence — unsigned (SmartScreen warns on first run, the manual explains the two clicks) or signed (the owner buys a certificate) — and record the answer.

### Which delivery kinds the Delivery section is for

The toolchain and the installer behaviour as written are for the kinds `installer` and `install-script`; a part of another kind records its kind's delivery as its type workflow says.

## Add at planning.stages

For **installable software** the plan's **last stage is "Packaging & installer"**: the
build script or install script, the committed installer script (desktop), the CI artifact,
the lifecycle verification (`installer-check.ps1`, or the project's `install-check.ps1` for
a CLI: your own run is a rehearsal, the proof is the owner's run from their terminal by a
run sheet, since a session of the packaged desktop app installs into a hidden copy of the
local application folder, KP-055), the command reference's currency check, and the User Manual's install and command
chapters — with `Delivery-Conventions.md` §2/§3/§4's rows as its acceptance criteria,
verbatim. The increment that first adds a command-line surface carries the
command-reference generator (§4). A plan for installable software without this stage, or a
CLI plan without the generator, is incomplete.

### Which delivery kinds the packaging stage is for

The stage as written is for the delivery kinds `installer` and `install-script`; a part of another kind takes the packaging stage its type workflow adds, if any, and an `Installer verification` answer of `n/a` passes the lifecycle check over.

## Add at planning.critic-lenses

- **Packaging stage (installable software: desktop application, command-line tool, local
  server).** Is the last stage "Packaging & installer", and does it carry
  `Delivery-Conventions.md` §2 / §3 / §4 as checkable acceptance criteria — one-command
  build or install, committed installer or install script, per-user install registered in
  Apps & features (a CLI on PATH from an isolated environment built from the lock file),
  upgrade in place keeping data, Upgrade / Uninstall / Cancel when already installed,
  uninstall keeping data, the lifecycle verification passing, the manual's install chapter?
  A plan for installable software without it is **Blocking**: the owner cannot install the
  result.
- **Command reference (any command-line surface).** Does the increment that first adds a
  command also add the reference generator (`scripts/dump-cli.py` → `docs/cli-reference.json`)
  and the CI currency check, and does every later command-changing increment carry
  "reference regenerated" as a criterion? Without it the supervisor has nothing to look
  commands up in and will instruct the owner from memory — **Blocking**.

## Add at project-end.delivery for installer

- **Deliver the installer** (installable software): run the lifecycle verification one
  final time on the release build (per the `Installer verification` parameter), exercise the
  "already installed" dialog once interactively, then attach the deliverable as a GitHub
  Release asset where a remote exists, or name its path in the report and the manual where
  there is none.

## Add at project-end.delivery for install-script

- **Deliver the install script** (a command-line tool or a local server): as "Deliver the installer" above, with the project's `install-check.ps1` as the lifecycle verification and no "already installed" dialog to exercise.
