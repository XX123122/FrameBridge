# Separate visible Edge session: explicit current-user consent is required.
[CmdletBinding()]
param(
    [string]$EdgePath,
    [string]$ProfileDirectory,
    [ValidateRange(1024, 65535)][int]$Port = 9222,
    [switch]$ConfirmLocalControl,
    [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'The Edge launcher supports Windows only.' }
if (-not $DryRun -and -not $ConfirmLocalControl) {
    throw 'Review local browser control, then pass -ConfirmLocalControl. No browser was started.'
}
if (-not $EdgePath) {
    $candidates = @(
        (Join-Path ${env:ProgramFiles(x86)} 'Microsoft\Edge\Application\msedge.exe'),
        (Join-Path $env:ProgramFiles 'Microsoft\Edge\Application\msedge.exe'),
        (Join-Path $env:LOCALAPPDATA 'Microsoft\Edge\Application\msedge.exe')
    )
    $EdgePath = $candidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
}
if (-not $EdgePath -or -not (Test-Path -LiteralPath $EdgePath -PathType Leaf)) {
    throw 'Edge not found. Specify the current user''s verified executable with -EdgePath.'
}
$edgeExe = (Resolve-Path -LiteralPath $EdgePath).Path
if (-not $ProfileDirectory) { $ProfileDirectory = Join-Path $env:LOCALAPPDATA 'FrameBridge\edge-session' }
$sessionProfile = [System.IO.Path]::GetFullPath($ProfileDirectory)
if ($sessionProfile.Contains('"')) { throw 'Profile path cannot contain quote characters.' }
$defaultProfile = [System.IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'Microsoft\Edge\User Data'))
if ($sessionProfile -eq $defaultProfile -or $sessionProfile.StartsWith($defaultProfile + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Refusing to use or copy the default Edge profile.'
}
$workspace = [System.IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
if ($sessionProfile -eq $workspace -or $sessionProfile.StartsWith($workspace + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Keep browser login profiles outside this source checkout.'
}
foreach ($policyPath in @('HKLM:\SOFTWARE\Policies\Microsoft\Edge', 'HKCU:\SOFTWARE\Policies\Microsoft\Edge')) {
    if (Test-Path -LiteralPath $policyPath) {
        $policy = Get-ItemProperty -LiteralPath $policyPath
        if ($null -ne $policy.RemoteDebuggingAllowed -and $policy.RemoteDebuggingAllowed -eq 0) {
            throw 'Edge policy disables debugging. Stop; do not change or bypass policy.'
        }
    }
}
$listener = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
$arguments = @('--remote-debugging-address=127.0.0.1', ('--remote-debugging-port=' + $Port),
    ('--user-data-dir="' + $sessionProfile + '"'), '--no-first-run', '--no-default-browser-check', 'https://chatgpt.com/')
if ($DryRun) {
    [PSCustomObject]@{Executable=$edgeExe;ProfileDirectory=$sessionProfile;BindAddress='127.0.0.1';Port=$Port;
        PortAlreadyListening=[bool]$listener;WouldLaunch=$false;LocalControlConfirmed=[bool]$ConfirmLocalControl} | ConvertTo-Json
    return
}
if ($listener) { throw 'Selected port is in use; inspect it rather than starting another session.' }
# Explicitly approved interactive window; browser manages its separate profile.
Start-Process -FilePath $edgeExe -ArgumentList $arguments -WindowStyle Normal
Write-Output 'Visible separate Edge launched. Sign in manually; verify the listener is loopback-only before connecting.'
