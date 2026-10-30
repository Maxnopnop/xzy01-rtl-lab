param(
    [ValidateSet('Status','Preflight','Run')][string]$Action = 'Status',
    [string]$Release,
    [string]$PythonPath = 'C:/Users/A/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) { throw 'Python executable not found.' }
$taskRunner = Join-Path $PSScriptRoot 'runner.py'
if ($Action -eq 'Status') {
    & $PythonPath -B $taskRunner status
    exit $LASTEXITCODE
}
if (-not $Release -or -not (Test-Path -LiteralPath $Release -PathType Leaf)) { throw 'Select the NEW36 coordinator release first.' }
& $PythonPath -B $taskRunner preflight --release $Release
if ($LASTEXITCODE -ne 0) { throw 'Preflight blocked. No generation. Preserve evidence.' }
if ($Action -eq 'Preflight') { exit 0 }
$taskHadKey = Test-Path Env:OPENROUTER_API_KEY
$taskPreviousKey = [Environment]::GetEnvironmentVariable('OPENROUTER_API_KEY', 'Process')
$taskSecret = $null
try {
    $taskSecret = Read-Host 'OpenRouter key (hidden; NEW 36 calls, cumulative 38 opportunities)' -AsSecureString
    [Environment]::SetEnvironmentVariable('OPENROUTER_API_KEY', [System.Net.NetworkCredential]::new('', $taskSecret).Password, 'Process')
    if ([string]::IsNullOrWhiteSpace($env:OPENROUTER_API_KEY)) { throw 'Empty key.' }
    & $PythonPath -B $taskRunner run --release $Release
    if ($LASTEXITCODE -ne 0) { throw 'Run stopped. Do not rerun; preserve reservations and STOP.' }
} finally {
    if ($taskHadKey) { [Environment]::SetEnvironmentVariable('OPENROUTER_API_KEY', $taskPreviousKey, 'Process') }
    else { Remove-Item Env:OPENROUTER_API_KEY -ErrorAction SilentlyContinue }
    if ($taskSecret) { $taskSecret.Dispose() }
    Remove-Variable taskSecret,taskPreviousKey,taskHadKey -ErrorAction SilentlyContinue
}
