param(
    [ValidateSet('OpenWeb','Direct')][string]$Mode = 'OpenWeb',
    [switch]$Offline,
    [string]$PythonPath = 'C:/Users/A/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $PythonPath)) { throw 'Python executable not found; supply -PythonPath.' }
$taskArgs = @('-B', (Join-Path $PSScriptRoot 'check_openrouter.py'))
if ($Mode -eq 'OpenWeb') { $taskArgs += @('--proxy', 'http://127.0.0.1:3213') }
if ($Offline) {
    $taskArgs += '--offline'
    & $PythonPath @taskArgs
    return
}
$taskPreviousKey = [Environment]::GetEnvironmentVariable('OPENROUTER_API_KEY', 'Process')
$taskSecret = Read-Host 'OpenRouter API key (not saved; metadata checks only)' -AsSecureString
try {
    $env:OPENROUTER_API_KEY = [System.Net.NetworkCredential]::new('', $taskSecret).Password
    if ([string]::IsNullOrWhiteSpace($env:OPENROUTER_API_KEY)) { throw 'Empty key; stopped.' }
    & $PythonPath @taskArgs
    if ($LASTEXITCODE -ne 0) { Write-Warning 'Check stopped. No automatic retry or model call was made.' }
} finally {
    [Environment]::SetEnvironmentVariable('OPENROUTER_API_KEY', $taskPreviousKey, 'Process')
    if ($taskSecret) { $taskSecret.Dispose() }
    Remove-Variable taskSecret,taskPreviousKey -ErrorAction SilentlyContinue
}
