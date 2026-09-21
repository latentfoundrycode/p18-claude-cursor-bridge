# Packaging Conventions — desktop applications ship as an installer

A desktop project is not finished when its tests pass. It is finished when the owner can double-click one file on a Windows 11 x64 machine and get a properly installed application — registered in *Apps & features*, with a Start-menu entry, upgradable in place, and cleanly removable. This file fixes what that means, which tooling produces it per stack, and how the supervisor proves it deterministically.

## 1. The deliverable

| Item | Requirement |
|---|---|
| Target | Windows 11, x64. The installer refuses 32-bit and ARM hosts with a plain message. |
| File | `dist/<Name>-Setup-<version>-x64.exe` — one self-contained file; `<version>` from the project's single version source (see §5). |
| Install scope | **Per-user** by default: `%LOCALAPPDATA%\Programs\<Name>`, no administrator prompt. Per-machine (`%ProgramFiles%`) only when the design needs a service, a driver, or a machine-wide file association — and then the installer asks for elevation and says why. |
| Registration | *Apps & features* entry with name, version, publisher, icon, and a working **Uninstall**; Start-menu shortcut; optional desktop shortcut (a checkbox, default off). |
| Already installed → the installer offers a choice | Running the installer on a machine where `<Name>` is installed opens a dialog: **Upgrade / reinstall** (keeps user data and settings) or **Uninstall** or **Cancel**. It never silently duplicates an install. |
| Reinstall / upgrade | **In place**, same identity (same `AppId` / upgrade code): files are replaced, the *Apps & features* entry is updated, user data and settings are untouched. This is the correct practice over remove-then-install: nothing the user created is ever at risk, and settings survive. A *downgrade* (older version over newer) prompts before proceeding. |
| Uninstall | Removes program files, shortcuts, and the registry entry. **Keeps user data** (`%APPDATA%\<Name>` or `%LOCALAPPDATA%\<Name>`) unless the user ticks *Also remove my data* on the uninstall dialog. The User Manual says where the data lives. |
| Data location | Never inside the install folder. Config and data under `%APPDATA%\<Name>` (roaming) or `%LOCALAPPDATA%\<Name>` (local); the app creates them on first run. |
| Code signing | Unsigned by default. Windows SmartScreen then warns "unknown publisher" on first run of the installer; the User Manual explains the two clicks (*More info → Run anyway*). A signing certificate costs money and identity verification, so it is a **user-level consequence escalated once at Phase 2**, never assumed. |
| Auto-update | None unless designed. An installer is the update path: download the new one, run it, choose *Upgrade*. |

## 2. Tooling per stack — use what the stack already ships, else Inno Setup

| Stack | Executable | Installer | Notes |
|---|---|---|---|
| Electron | `electron-builder` (`--win --x64`) | `electron-builder` **NSIS** target with `oneClick: false`, `perMachine: false`, `allowToChangeInstallationDirectory: true`, `deleteAppDataOnUninstall: false` | NSIS handles upgrade-in-place and *Apps & features* itself; the "already installed" dialog is its default (it offers to uninstall the previous version). |
| Tauri | `tauri build` | Tauri's bundler, `nsis` target (same settings as above) | Prefer `nsis` over `msi` for the per-user default. |
| .NET (WPF / WinUI / Avalonia) | `dotnet publish -c Release -r win-x64 --self-contained` | **Inno Setup** (§3) | Self-contained so no runtime install step. |
| Python (PySide / Tk / wx) | **PyInstaller** (`--onedir`, not `--onefile` — faster start, cleaner upgrades) | **Inno Setup** (§3) | Pin PyInstaller; exclude dev deps. |
| Rust / Go / C++ | the stack's release build, x64 | **Inno Setup** (§3) | |
| Anything else | the stack's native release build | **Inno Setup** (§3) unless the stack ships an installer target that meets §1 | |

Why Inno Setup as the default: free, script-based (the script is a committed file, reviewable in a diff), produces one `.exe`, supports per-user installs without elevation, registers the uninstaller, upgrades in place by `AppId`, and its `[Code]` section is where the "already installed" dialog lives. MSI (WiX) only when a corporate deployment tool requires MSI — the owner decides that at Phase 2.

**Inno Setup is a machine prerequisite, not a project dependency.** On the build machine: `winget install --id JRSoftware.InnoSetup -e` (the setup guide carries the run sheet); pin the version in `PROJECT_STATUS.md`. GitHub's `windows-latest` runners have it preinstalled, so CI can build the installer with the same script.

## 3. The Inno Setup script — the committed template

`installer/<Name>.iss`, committed, filled per project. The parts that meet §1 are marked; the builder writes the rest from the design.

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
DefaultDirName={localappdata}\Programs\{#AppName}   ; per-user (§1); {autopf} only for a per-machine design
PrivilegesRequired=lowest                           ; no UAC for per-user
ArchitecturesAllowed=x64compatible                  ; Windows 11 x64 only
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist
OutputBaseFilename={#AppName}-Setup-{#AppVersion}-x64
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
WizardStyle=modern
DisableProgramGroupPage=yes
CloseApplications=yes                               ; upgrade with the app running: ask to close it

[Files]
Source: "..\build\win-x64\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked

[Run]
Filename: "{app}\{#AppExe}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; program folder only — user data under {userappdata}\{#AppName} is kept (§1)

[Code]
// --- "already installed" dialog (§1): Upgrade / Uninstall / Cancel ---------------------
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
  Uninst: string; Choice, ResultCode: Integer; Installed: string;
begin
  Result := True;
  if WizardSilent() then exit;                      // silent runs (the verification script) go straight to upgrade-in-place
  if InstalledUninstallString(Uninst) then begin
    Installed := InstalledVersion();
    Choice := MsgBox('{#AppName} ' + Installed + ' is already installed.' + #13#10#13#10 +
                     'Yes    = Upgrade / reinstall (version {#AppVersion}; your data and settings are kept)' + #13#10 +
                     'No     = Uninstall {#AppName}' + #13#10 +
                     'Cancel = Exit without changes', mbConfirmation, MB_YESNOCANCEL);
    if Choice = IDNO then begin
      Exec(RemoveQuotes(Uninst), '', '', SW_SHOW, ewWaitUntilTerminated, ResultCode);
      Result := False;                              // uninstalled (or the user backed out of it); do not continue installing
    end else if Choice = IDCANCEL then
      Result := False;
    // IDYES: fall through — same AppId, so Inno upgrades in place and updates Apps & features
  end;
end;

// --- uninstall: keep data unless the user says otherwise (§1) ---------------------------
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
    if not UninstallSilent() then
      if MsgBox('Also remove your {#AppName} data and settings?' + #13#10 +
                '(' + ExpandConstant('{userappdata}\{#AppName}') + ')', mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
        DelTree(ExpandConstant('{userappdata}\{#AppName}'), True, True, True);
end;
```

A downgrade guard (compare `InstalledVersion()` with `{#AppVersion}` and prompt) is added when the design calls for it; the default template allows same-or-newer.

## 4. The build — one command, reproducible

The project carries one script the supervisor, CI, and the owner all run the same way: `scripts/build-installer.ps1` (PowerShell, since the target is Windows), which (1) builds the executable for `win-x64` into `build/win-x64/`, (2) reads the version from the single source, (3) runs the installer tool (`ISCC.exe installer\<Name>.iss /DAppVersion=<version>` for Inno; the stack's own command otherwise), and (4) leaves exactly one file in `dist/`. `build/` and `dist/` are gitignored; the installer is a **CI artifact** on every tagged build and a **GitHub Release asset** at project end where a remote exists. The User Manual names the path and the file.

## 5. Single version source

One place holds the version (`package.json`, `pyproject.toml`, the `.csproj`, `Cargo.toml`, or a `VERSION` file); the executable's file version, the installer's `AppVersion`, the *Apps & features* entry, and the app's *About* screen all derive from it. Two places that can disagree is an issue waiting to happen.

## 6. Verification — deterministic, on the build machine, per-user, reversible

The supervisor proves §1 with the bundled `~/.claude/cursor-bridge/installer-check.ps1`, which drives the installer **silently** through the full lifecycle and asserts each state:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ~/.claude/cursor-bridge/installer-check.ps1 -Installer dist\<Name>-Setup-<v>-x64.exe -AppName "<Name>" -AppId "<GUID>" -Exe "<Name>.exe" -Version "<v>"
```

1. **Precondition** — not installed (or the check uninstalls a leftover first and says so).
2. **Install** (`/VERYSILENT /SUPPRESSMSGBOXES /NORESTART`) → the install folder exists, the executable is there, the *Apps & features* registry entry exists with the right `DisplayVersion`, the Start-menu shortcut exists.
3. **Launch smoke** — the executable starts and exits cleanly with `--version` (or the project's smoke flag) and prints the version.
4. **Data survives an upgrade** — write a marker file under `%APPDATA%\<Name>`, run the same installer again silently (this is the in-place reinstall path), assert the marker is still there and the registry version is unchanged.
5. **Uninstall** (`unins000.exe /VERYSILENT`) → install folder gone, registry entry gone, shortcut gone, **marker still there** (data kept by default).
6. Cleanup of the marker; `PASS` or the first failing assertion.

Every step is per-user and reversible, which is why the supervisor may run it on the owner's machine — but only with the **`Installer verification`** run parameter set to `local` (the default for desktop projects; `ci-only` runs the same script on a `windows-latest` runner instead). The "already installed" *dialog* itself cannot be exercised silently; it is verified once by the supervisor with a throwaway interactive run at project end, and the owner sees it the first time they upgrade.

## 7. Where it lands in the loop

- **Phase 1** — "desktop application" in the platform context triggers this file; the owner's target is Windows 11 x64 unless they say otherwise.
- **Phase 2** — `docs/DESIGN.md` gets a **Packaging & distribution** section: stack toolchain from §2, per-user vs per-machine with the reason, data location, the version source, code signing (the one escalation), and that the installer meets §1.
- **Phase 4** — the plan's **last stage is "Packaging & installer"**: the build script, the installer script, CI artifact, the verification, the User Manual's install chapter. Its acceptance criteria are §1's rows and §6's six steps, verbatim, checkable. `plan-critic` blocks a desktop plan without it.
- **Phase 6** — the packaging increments go through the normal gate. The stage close runs `installer-check.ps1` as its test.
- **Project end** — the installer is attached as a release asset (remote) or named by path (local); the User Manual's first chapter is *Install, upgrade, uninstall*, with the SmartScreen note.
