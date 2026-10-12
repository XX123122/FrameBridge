# User-authorized visible Edge session. Never copies or inspects browser profiles.
$ErrorActionPreference = 'Stop'
$edgeExe = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
if (-not (Test-Path -LiteralPath $edgeExe -PathType Leaf)) {
    throw 'Edge executable not found at the verified installation path.'
}
foreach ($policyPath in @('HKLM:\SOFTWARE\Policies\Microsoft\Edge', 'HKCU:\SOFTWARE\Policies\Microsoft\Edge')) {
    if (Test-Path -LiteralPath $policyPath) {
        $policy = Get-ItemProperty -LiteralPath $policyPath
        if ($null -ne $policy.RemoteDebuggingAllowed -and $policy.RemoteDebuggingAllowed -eq 0) {
            throw 'Edge policy disables remote debugging. Stop; do not change or bypass policy.'
        }
    }
}
if (Get-NetTCPConnection -State Listen -LocalPort 9222 -ErrorAction SilentlyContinue) {
    throw 'Port 9222 already has a listener. Inspect the existing connection; do not start another session.'
}
$sessionProfile = Join-Path $env:LOCALAPPDATA 'FrameBridge\edge-session'
# A separate profile is browser-managed. No default profile, Cookie or Token is read or copied.
$arguments = @(
    '--remote-debugging-address=127.0.0.1',
    '--remote-debugging-port=9222',
    ('--user-data-dir="' + $sessionProfile + '"'),
    '--no-first-run',
    '--no-default-browser-check',
    'https://chatgpt.com/'
)
# The user explicitly requested a visible interactive browser and manual sign-in.
Start-Process -FilePath $edgeExe -ArgumentList $arguments -WindowStyle Normal
Write-Output 'Visible independent Edge launched. Complete ChatGPT sign-in manually.'
