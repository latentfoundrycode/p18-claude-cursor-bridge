<#
installer-check.ps1 - drive a Windows installer through install / upgrade-in-place / uninstall
silently and assert each state (Packaging-Conventions.md section 6).

  powershell -NoProfile -ExecutionPolicy Bypass -File installer-check.ps1 `
      -Installer dist\App-Setup-1.2.0-x64.exe -AppName "App" -AppId "{GUID}" -Exe "App.exe" -Version "1.2.0" `
      [-SmokeArgs "--version"] [-PerMachine] [-KeepInstalled]

Assumes an Inno Setup installer (silent switches /VERYSILENT /SUPPRESSMSGBOXES /NORESTART;
uninstaller registered as <AppId>_is1). Per-user by default; -PerMachine checks HKLM and
%ProgramFiles% instead. Exit 0 = PASS, 1 = a step failed (the first failing assertion is
printed), 2 = bad arguments. Authored 2026-09-21; parse-checked, not yet exercised on a live
project - verify-first (KP-008) on first use.
#>
param(
  [Parameter(Mandatory=$true)][string]$Installer,
  [Parameter(Mandatory=$true)][string]$AppName,
  [Parameter(Mandatory=$true)][string]$AppId,
  [Parameter(Mandatory=$true)][string]$Exe,
  [Parameter(Mandatory=$true)][string]$Version,
  [string]$SmokeArgs = "--version",
  [switch]$PerMachine,
  [switch]$KeepInstalled
)

$ErrorActionPreference = "Stop"
$hive = if ($PerMachine) { "HKLM:" } else { "HKCU:" }
$regKey = "$hive\Software\Microsoft\Windows\CurrentVersion\Uninstall\$AppId" + "_is1"
$installDir = if ($PerMachine) { Join-Path $env:ProgramFiles $AppName } else { Join-Path $env:LOCALAPPDATA "Programs\$AppName" }
$dataDir = Join-Path $env:APPDATA $AppName
$marker = Join-Path $dataDir "installer-check.marker"
$startMenu = if ($PerMachine) { Join-Path $env:ProgramData "Microsoft\Windows\Start Menu\Programs\$AppName.lnk" } else { Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\$AppName.lnk" }
$silent = @("/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART")
$step = ""

function Fail($msg) { Write-Output "FAIL [$script:step] $msg"; exit 1 }
function Ok($msg)   { Write-Output "ok   [$script:step] $msg" }
function Installed() { Test-Path $regKey }
function RegVersion() { try { (Get-ItemProperty $regKey -ErrorAction Stop).DisplayVersion } catch { "" } }
function UninstallString() { try { (Get-ItemProperty $regKey -ErrorAction Stop).UninstallString } catch { "" } }
function RunSilentUninstall() {
  $u = UninstallString
  if (-not $u) { return }
  $exePath = $u.Trim('"')
  $p = Start-Process -FilePath $exePath -ArgumentList "/VERYSILENT","/SUPPRESSMSGBOXES","/NORESTART" -Wait -PassThru -WindowStyle Hidden
  if ($p.ExitCode -ne 0) { Fail "uninstaller exit code $($p.ExitCode)" }
  Start-Sleep -Seconds 2
}

if (-not (Test-Path $Installer)) { Write-Output "installer-check: no such file: $Installer"; exit 2 }
$Installer = (Resolve-Path $Installer).Path
Write-Output "installer-check: $AppName $Version  installer=$Installer  scope=$(if ($PerMachine) {'per-machine'} else {'per-user'})"

# 1. precondition
$step = "precondition"
if (Installed) { Write-Output "note [$step] $AppName already installed (version $(RegVersion)) - removing leftover first"; RunSilentUninstall }
if (Installed) { Fail "still registered after leftover uninstall" }
Ok "not installed"

# 2. install
$step = "install"
$p = Start-Process -FilePath $Installer -ArgumentList $silent -Wait -PassThru -WindowStyle Hidden
if ($p.ExitCode -ne 0) { Fail "installer exit code $($p.ExitCode)" }
if (-not (Test-Path $installDir)) { Fail "install folder missing: $installDir" }
$exeFull = Join-Path $installDir $Exe
if (-not (Test-Path $exeFull)) { Fail "executable missing: $exeFull" }
if (-not (Installed)) { Fail "Apps & features entry missing: $regKey" }
$rv = RegVersion
if ($rv -ne $Version) { Fail "registered version '$rv' != expected '$Version'" }
if (-not (Test-Path $startMenu)) { Fail "Start-menu shortcut missing: $startMenu" }
Ok "folder, executable, registry entry ($rv), Start-menu shortcut present"

# 3. launch smoke
$step = "smoke"
$out = & $exeFull $SmokeArgs.Split(" ") 2>&1 | Out-String
if ($LASTEXITCODE -ne 0) { Fail "executable exit code $LASTEXITCODE for '$SmokeArgs'; output: $($out.Trim())" }
if ($out -notmatch [regex]::Escape($Version)) { Fail "'$SmokeArgs' output does not contain version $Version; output: $($out.Trim())" }
Ok "'$Exe $SmokeArgs' exits 0 and prints $Version"

# 4. data survives an upgrade-in-place (same installer again)
$step = "upgrade"
New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
Set-Content -Path $marker -Value "installer-check $(Get-Date -Format s)" -Encoding utf8
$p = Start-Process -FilePath $Installer -ArgumentList $silent -Wait -PassThru -WindowStyle Hidden
if ($p.ExitCode -ne 0) { Fail "reinstall exit code $($p.ExitCode)" }
if (-not (Test-Path $marker)) { Fail "user data marker was removed by the reinstall" }
if (-not (Installed)) { Fail "registry entry missing after reinstall" }
if ((RegVersion) -ne $Version) { Fail "registered version changed after reinstall: $(RegVersion)" }
if (-not (Test-Path $exeFull)) { Fail "executable missing after reinstall" }
$dups = @(Get-ChildItem "$hive\Software\Microsoft\Windows\CurrentVersion\Uninstall" | Where-Object { try { (Get-ItemProperty $_.PSPath).DisplayName -eq $AppName } catch { $false } })
if ($dups.Count -ne 1) { Fail "expected exactly one Apps & features entry named '$AppName', found $($dups.Count)" }
Ok "reinstall kept the data marker, one registry entry, version $Version"

# 5. uninstall keeps data
if ($KeepInstalled) { Write-Output "PASS (left installed by request; data marker at $marker)"; exit 0 }
$step = "uninstall"
RunSilentUninstall
if (Installed) { Fail "registry entry still present after uninstall" }
if (Test-Path $exeFull) { Fail "executable still present after uninstall: $exeFull" }
if (Test-Path $startMenu) { Fail "Start-menu shortcut still present after uninstall" }
if (-not (Test-Path $marker)) { Fail "user data was deleted by a default (silent) uninstall - data must be kept unless the user opts to remove it" }
Ok "program files, registry entry, shortcut removed; user data kept"

# 6. cleanup
$step = "cleanup"
Remove-Item -Force $marker
if (-not (Get-ChildItem $dataDir -Force | Select-Object -First 1)) { Remove-Item -Force $dataDir }
Ok "marker removed"
Write-Output "PASS installer-check: install / upgrade-in-place / uninstall verified for $AppName $Version"
exit 0
