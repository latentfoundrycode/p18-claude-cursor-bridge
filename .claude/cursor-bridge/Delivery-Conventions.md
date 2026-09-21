# Delivery Conventions — installable software ships with its installer and its command reference

A project is not finished when its tests pass. It is finished when the owner can install it on a Windows 11 x64 machine from one file, run it, upgrade it in place, and remove it cleanly — and when every command the software exposes is written down in a reference the supervisor looks up before it ever tells the owner to type one. This file fixes what that means for each kind of software, which tooling produces it, and how the supervisor proves it.

## 1. What counts as installable — and what each kind ships

| Kind | Examples | Ships as | Section |
|---|---|---|---|
| **Desktop application** | a windowed app (Electron, Tauri, .NET, PySide, Rust/Go GUI) | one installer `.exe` | §2 |
| **Command-line tool** | a `tdp`-style CLI, a batch processor, a developer tool | `install.cmd` + `install.ps1` that puts the command on PATH | §3 |
| **Local server / service** | an HTTP API or worker the owner runs on their PC | same as a command-line tool, plus a `serve`/`start` command; a Windows service only when the design says so | §3 |
| **Library / package** | code other software imports | its package registry artifact (`pip`, `npm`); no installer — the User Manual explains how a consumer installs it | — |
| **Web application (hosted)** | deployed to a server, used in a browser | a deploy procedure, not an installer; out of scope here | — |

Every installable kind also ships a **command reference** (§4) if it has any command-line surface, and follows the **common rules** (§5).

## 2. Desktop application — one installer file

| Item | Requirement |
|---|---|
| Target | Windows 11, x64. The installer refuses 32-bit and ARM hosts with a plain message. |
| File | `dist/<Name>-Setup-<version>-x64.exe` — one self-contained file; `<version>` from the single version source (§5). |
| Install scope | **Per-user** by default: `%LOCALAPPDATA%\Programs\<Name>`, no administrator prompt. Per-machine (`%ProgramFiles%`) only when the design needs a service, a driver, or a machine-wide file association — then the installer asks for elevation and says why. |
| Registration | *Apps & features* entry with name, version, publisher, icon, and a working **Uninstall**; Start-menu shortcut; optional desktop shortcut (checkbox, default off). |
| Already installed → a choice | Running the installer on a machine where `<Name>` is installed opens a dialog: **Upgrade / reinstall** (keeps user data and settings), **Uninstall**, or **Cancel**. Never a silent duplicate install. |
| Reinstall / upgrade | **In place**, same identity (same `AppId`): files replaced, the *Apps & features* entry updated, user data and settings untouched. The correct practice over remove-then-install: nothing the user created is at risk and settings survive. A downgrade prompts first. |
| Uninstall | Removes program files, shortcuts, and the registry entry. **Keeps user data** unless the user ticks *Also remove my data*. |
| Data location | Never inside the install folder: `%APPDATA%\<Name>` (roaming) or `%LOCALAPPDATA%\<Name>` (local), created on first run. |
| Code signing | Unsigned by default; SmartScreen warns on first run and the User Manual explains the two clicks (*More info → Run anyway*). A certificate costs money and identity checks — a **user-level consequence escalated once at Phase 2**, never assumed. |
| Auto-update | None unless designed. The installer is the update path. |

### 2.1 Tooling per stack — use what the stack ships, else Inno Setup

| Stack | Executable | Installer |
|---|---|---|
| Electron | `electron-builder --win --x64` | `electron-builder` NSIS target: `oneClick: false`, `perMachine: false`, `allowToChangeInstallationDirectory: true`, `deleteAppDataOnUninstall: false` (NSIS does upgrade-in-place and the already-installed dialog itself) |
| Tauri | `tauri build` | Tauri bundler, `nsis` target, same settings |
| .NET (WPF / WinUI / Avalonia) | `dotnet publish -c Release -r win-x64 --self-contained` | **Inno Setup** (§2.2) |
| Python (PySide / Tk / wx) | **PyInstaller** `--onedir` (not `--onefile`: faster start, cleaner upgrades) | **Inno Setup** (§2.2) |
| Rust / Go / C++ / other | the stack's x64 release build | **Inno Setup** (§2.2) |

Inno Setup: free, script-based (the script is a committed, reviewable file), one `.exe`, per-user without elevation, registers the uninstaller, upgrades in place by `AppId`, and its `[Code]` section holds the already-installed dialog. MSI (WiX) only when a corporate deployment tool demands it — the owner's call at Phase 2. **Inno Setup is a machine prerequisite** (`winget install --id JRSoftware.InnoSetup -e`; setup guide Step 10; pin the version in `PROJECT_STATUS.md`); GitHub `windows-latest` runners have it preinstalled.

### 2.2 The committed Inno Setup script — `installer/<Name>.iss`

```ini
#define AppName "<Name>"
#define AppVersion "<version>"          ; injected at build time from the single version source (§5)
#define AppPublisher "<publisher>"
#define AppExe "<Name>.exe"
#define AppId "{{<GUID — generated once, never changed>}}"   ; the identity that makes upgrades in-place

[Setup]
AppId={#AppId}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\{#AppName}   ; per-user; {autopf} only for a per-machine design
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist
OutputBaseFilename={#AppName}-Setup-{#AppVersion}-x64
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
WizardStyle=modern
DisableProgramGroupPage=yes
CloseApplications=yes

[Files]
Source: "..\build\win-x64\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked

[Run]
Filename: "{app}\{#AppExe}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent

[Code]
// --- already installed: Upgrade / Uninstall / Cancel ------------------------------------
function InstalledUninstallString(var S: string): Boolean;
begin
  Result := RegQueryStringValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\' + '{#AppId}' + '_is1', 'UninstallString', S)
         or RegQueryStringValue(HKLM, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\' + '{#AppId}' + '_is1', 'UninstallString', S);
end;

function InstalledVersion(): string;
begin
  if not RegQueryStringValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\' + '{#AppId}' + '_is1', 'DisplayVersion', Result) then
    if not RegQueryStringValue(HKLM, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\' + '{#AppId}' + '_is1', 'DisplayVersion', Result) then
      Result := '';
end;

function InitializeSetup(): Boolean;
var
  Uninst: string; Choice, ResultCode: Integer;
begin
  Result := True;
  if WizardSilent() then exit;                      // silent runs (the verification) go straight to upgrade-in-place
  if InstalledUninstallString(Uninst) then begin
    Choice := MsgBox('{#AppName} ' + InstalledVersion() + ' is already installed.' + #13#10#13#10 +
                     'Yes    = Upgrade / reinstall (version {#AppVersion}; your data and settings are kept)' + #13#10 +
                     'No     = Uninstall {#AppName}' + #13#10 +
                     'Cancel = Exit without changes', mbConfirmation, MB_YESNOCANCEL);
    if Choice = IDNO then begin
      Exec(RemoveQuotes(Uninst), '', '', SW_SHOW, ewWaitUntilTerminated, ResultCode);
      Result := False;
    end else if Choice = IDCANCEL then
      Result := False;
  end;
end;

// --- uninstall keeps data unless the user says otherwise ---------------------------------
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
    if not UninstallSilent() then
      if MsgBox('Also remove your {#AppName} data and settings?' + #13#10 +
                '(' + ExpandConstant('{userappdata}\{#AppName}') + ')', mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
        DelTree(ExpandConstant('{userappdata}\{#AppName}'), True, True, True);
end;
```

### 2.3 Verification — `installer-check.ps1`, silent, per-user, reversed

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ~/.claude/cursor-bridge/installer-check.ps1 -Installer dist\<Name>-Setup-<v>-x64.exe -AppName "<Name>" -AppId "<GUID>" -Exe "<Name>.exe" -Version "<v>"
```

Precondition (not installed) → install silently → folder, executable, *Apps & features* entry with the right version, Start-menu shortcut → launch smoke (`--version` prints the version) → write a data marker, reinstall silently, marker survives, still one registry entry → uninstall silently, program and entry gone, marker still there → cleanup. `PASS` or the first failing assertion. Runs where the `Installer verification` run parameter says (`local` default; `ci-only`). The already-installed *dialog* cannot be exercised silently; the supervisor tries it once interactively at project end.

## 3. Command-line tools and local servers — an install script that puts the command on PATH

The owner double-clicks one file and afterwards can open any terminal and type the command. No "activate the environment first", no "run it from the repo folder".

| Item | Requirement |
|---|---|
| Files | `install.cmd` (double-clickable; it only launches the PowerShell script with the right policy) and `install.ps1` (the logic), both committed at the repo root; plus `uninstall.cmd`. A `.cmd` wrapper exists because double-clicking a `.ps1` opens an editor, not a run. |
| What install does | (1) checks prerequisites and says exactly what is missing and how to get it (the runtime the stack needs — Python x.y, Node x — via `winget` where possible); (2) creates an **isolated environment** under `%LOCALAPPDATA%\Programs\<Name>` (a venv for Python, a private `node_modules` for Node, the binary for compiled stacks) and installs the project **from its lock file** — never "latest"; (3) puts the command on the **user PATH** through a launcher in `%LOCALAPPDATA%\Programs\<Name>\bin` (a `<cmd>.cmd` shim for a venv entry point, or the binary itself), and adds that folder to the user PATH once; (4) writes an `installed.json` (version, install date, location) and registers an *Apps & features* entry with the uninstaller so the tool is discoverable and removable like anything else; (5) downloads large first-run assets (models, datasets) only with a stated size and the owner's consent, into the data location, never silently. |
| Already installed → a choice | The script detects `installed.json` and asks: **Upgrade / reinstall** (in place, same folder; data and config kept), **Uninstall**, or **Cancel** — the same three as §2. |
| Upgrade | In place: the environment is rebuilt from the new lock file in the same folder; the launcher stays; config and data are untouched. |
| Uninstall | `uninstall.cmd` (or the *Apps & features* entry): removes the environment, the launcher, the PATH entry, the registry entry; **keeps data and config** unless asked. |
| Data and config | `%APPDATA%\<Name>` (config) and `%LOCALAPPDATA%\<Name>` (cache, indexes, models); never the install folder, never the repo. |
| Silent mode | `install.ps1 -Silent` (upgrade-in-place without prompts) and `install.ps1 -Uninstall -Silent`, so the lifecycle can be verified without a human. |
| Server / service | A local server ships the same way with a `serve` (or `start`) command. It becomes a Windows service or a scheduled task **only** if the design says the owner needs it running without a terminal; then the installer registers it, `uninstall` removes it, and the manual says how to start and stop it. |
| Verification | The packaging stage writes `scripts/install-check.ps1` for the project, following §2.3's six steps against `install.ps1 -Silent`: precondition → install → **a fresh shell** finds `<cmd> --version` on PATH and it prints the version → data marker survives a reinstall → uninstall removes the launcher and PATH entry and keeps the marker → cleanup. It runs where `Installer verification` says. |

Why an isolated environment and a launcher rather than `pip install` into the owner's Python: nothing else on the machine changes, two tools cannot fight over a dependency, and uninstall is a folder delete.

## 4. The command reference — generated from the code, looked up before every instruction

A project with any command-line surface maintains **one machine-readable reference of every command, sub-command, flag, argument, default, and one-line description**, generated from the program itself so it cannot drift from what is implemented.

| Item | Requirement |
|---|---|
| Files | `docs/cli-reference.json` (the source of truth; one object per command with its path, description, arguments, options with type/default/required, and examples) and `docs/CLI_REFERENCE.md` rendered from it for humans; the User Manual's command chapter is rendered from the same JSON. |
| Generator | `scripts/dump-cli.py` (or the stack's equivalent) walks the real command tree — Typer/Click's command objects, argparse's parser tree, Commander's/yargs' registered commands — and writes the JSON. It is code the builder writes in the increment that first adds the CLI, and re-runs in every increment that changes a command. |
| Currency check | A CI step regenerates the JSON and fails if it differs from the committed file (`git diff --exit-code docs/cli-reference.json`), so an added flag without a regenerated reference cannot merge. Locally the pre-commit gate runs the same regeneration. |
| Acceptance | Every increment that adds or changes a command carries "the reference regenerated and committed" as an acceptance criterion, and `diff-reviewer` treats a command change without a reference change as a `FAIL`. |
| **The supervisor's rule** | Before writing any run sheet, report, or manual passage that tells the owner to type a project command, the supervisor **reads the command in `docs/cli-reference.json`** and copies the exact spelling, flags, and argument order from there — never from memory of the design, the plan, or an earlier conversation. If the reference has no such command, the command does not exist: the supervisor runs `<cmd> --help` to confirm before claiming otherwise, and treats a gap between the reference and `--help` as an issue. A command the owner cannot find in `--help` is a made-up command, and a made-up command in a run sheet is a `FAIL` of the run-sheet rule. |

## 5. Common rules

- **Single version source.** One place holds the version (`package.json`, `pyproject.toml`, the `.csproj`, `Cargo.toml`, or `VERSION`); the executable's version, the installer, `installed.json`, *Apps & features*, `--version`, and the *About* screen all derive from it.
- **One build command.** `scripts/build-installer.ps1` (desktop) or the install script itself (CLI) is the one way to produce the deliverable — the supervisor, CI, and the owner run the same thing. `build/` and `dist/` are gitignored; the deliverable is a CI artifact on tagged builds and a GitHub Release asset at project end where a remote exists.
- **Unsigned by default**, code signing escalated once at Phase 2 (§2).
- **Verification is reversible and per-user**, which is why the supervisor may run it on the owner's machine under `Installer verification: local`.

## 6. Where it lands in the loop

- **Phase 1** — the platform context names the kind (§1) and therefore the deliverable; the owner's target is Windows 11 x64 unless they say otherwise.
- **Phase 2** — `docs/DESIGN.md` gets a **Delivery** section: the kind, the toolchain, per-user vs per-machine with the reason, data location, the version source, code signing (the one escalation), whether a server runs as a service, and — for any CLI — the command-reference generator.
- **Phase 4** — the plan's **last stage is "Packaging & installer"**: the build or install script, the installer script (desktop), the CI artifact, the lifecycle verification, the command reference's currency check, and the User Manual's install and command chapters, with §2/§3/§4's rows as checkable acceptance criteria. The increment that first adds a CLI carries the reference generator. `plan-critic` blocks a plan for installable software without the stage, and a CLI plan without the generator.
- **Phase 6** — packaging increments go through the normal gate; the stage close runs the lifecycle verification as its test.
- **Project end** — the deliverable is attached as a release asset (remote) or named by path (local); the User Manual opens with *Install, upgrade, uninstall* and, for a CLI, continues with the command chapter rendered from the reference.
