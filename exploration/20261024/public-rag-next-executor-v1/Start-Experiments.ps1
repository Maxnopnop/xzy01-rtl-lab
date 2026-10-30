param(
    [ValidateSet('Preflight','Run')][string]$Action = 'Preflight',
    [string]$PythonPath = 'C:/Users/A/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) { throw 'Python executable not found.' }
$taskHadKey = Test-Path Env:OPENROUTER_API_KEY
$taskPreviousKey = [Environment]::GetEnvironmentVariable('OPENROUTER_API_KEY', 'Process')
$taskSecret = $null
try {
    $taskSecret = Read-Host 'OpenRouter API key (process only; not saved)' -AsSecureString
    [Environment]::SetEnvironmentVariable('OPENROUTER_API_KEY', [System.Net.NetworkCredential]::new('', $taskSecret).Password, 'Process')
    if ([string]::IsNullOrWhiteSpace($env:OPENROUTER_API_KEY)) { throw 'Empty key; stopped.' }
    & $PythonPath -B (Join-Path $PSScriptRoot 'runner.py') preflight
    if ($LASTEXITCODE -ne 0) { throw 'Preflight blocked. No generation. Do not retry a model call.' }
    if ($Action -eq 'Run') {
        & $PythonPath -B (Join-Path $PSScriptRoot 'runner.py') run
        if ($LASTEXITCODE -ne 0) { throw 'Run stopped. Preserve evidence; no automatic retry or continuation.' }
    }
} finally {
    if ($taskHadKey) {
        [Environment]::SetEnvironmentVariable('OPENROUTER_API_KEY', $taskPreviousKey, 'Process')
    } else { Remove-Item Env:OPENROUTER_API_KEY -ErrorAction SilentlyContinue }
    if ($taskSecret) { $taskSecret.Dispose() }
    Remove-Variable taskSecret,taskPreviousKey,taskHadKey -ErrorAction SilentlyContinue
}
