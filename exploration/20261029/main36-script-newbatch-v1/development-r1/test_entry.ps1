$ErrorActionPreference = 'Stop'
$taskHere = $PSScriptRoot
$taskMock = Join-Path $taskHere 'ps-offline'
New-Item -ItemType Directory -Path $taskMock -ErrorAction Stop | Out-Null
$taskTokens = $null
$taskErrors = $null
[System.Management.Automation.Language.Parser]::ParseFile((Join-Path $taskHere 'Start-Experiments.ps1'), [ref]$taskTokens, [ref]$taskErrors) | Out-Null
if ($taskErrors.Count -ne 0) { throw 'PS syntax error' }
$taskFake = Join-Path $taskMock 'fake-python.cmd'
@'
@echo off
if defined OPENROUTER_API_KEY (echo %~3 KEY_PRESENT>> "%TRACE_FILE%") else (echo %~3 KEY_ABSENT>> "%TRACE_FILE%")
exit /b 0
'@ | Set-Content -LiteralPath $taskFake -Encoding ASCII
$taskRelease = Join-Path $taskMock 'NOT_A_RELEASE.json'
'{"decision":"OFFLINE_FIXTURE"}' | Set-Content -LiteralPath $taskRelease -Encoding ASCII
$env:TRACE_FILE = Join-Path $taskMock 'trace.txt'
$taskPrevious = [Environment]::GetEnvironmentVariable('OPENROUTER_API_KEY','Process')
$taskHad = Test-Path Env:OPENROUTER_API_KEY
try {
    Remove-Item Env:OPENROUTER_API_KEY -ErrorAction SilentlyContinue
    $script:taskPromptCount = 0
    function Read-Host { param($Prompt,[switch]$AsSecureString) $script:taskPromptCount++; ConvertTo-SecureString 'OFFLINE_SYNTHETIC_ONLY' -AsPlainText -Force }
    & (Join-Path $taskHere 'Start-Experiments.ps1') -Action Run -Release $taskRelease -PythonPath $taskFake
    if (Test-Path Env:OPENROUTER_API_KEY) { throw 'Credential not cleared' }
    $taskTrace = @(Get-Content -LiteralPath $env:TRACE_FILE)
    if ($script:taskPromptCount -ne 1 -or $taskTrace.Count -ne 2 -or $taskTrace[0] -ne 'preflight KEY_ABSENT' -or $taskTrace[1] -ne 'run KEY_PRESENT') { throw 'One-prompt entry sequence failed' }
    @{passed=$true;prompt_count=$script:taskPromptCount;trace=$taskTrace;credential_cleared=$true;network_calls=0;model_calls=0;scope='PowerShell 5.1 actual entry with fake executable, not a release or live runner'} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskHere 'powershell-audit.json') -Encoding UTF8
} finally {
    if ($taskHad) { [Environment]::SetEnvironmentVariable('OPENROUTER_API_KEY',$taskPrevious,'Process') }
    else { Remove-Item Env:OPENROUTER_API_KEY -ErrorAction SilentlyContinue }
    Remove-Item Env:TRACE_FILE -ErrorAction SilentlyContinue
}
