$ErrorActionPreference = 'Stop'
$taskOriginallyPresent = Test-Path Env:OPENROUTER_API_KEY
$taskOriginal = [Environment]::GetEnvironmentVariable('OPENROUTER_API_KEY','Process')
$taskTemp = Join-Path ([IO.Path]::GetTempPath()) ('rtl-launch-test-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $taskTemp | Out-Null
$taskFake = Join-Path $taskTemp 'fake.ps1'
@'
$global:FakeCalls += 1
if ($env:OPENROUTER_API_KEY -ne 'OFFLINE_SYNTHETIC') { throw 'Wrong mock credential boundary' }
$global:LASTEXITCODE = $global:FakeExit
'@ | Set-Content -LiteralPath $taskFake -Encoding UTF8
function Read-Host { param($Prompt,[switch]$AsSecureString) ConvertTo-SecureString 'OFFLINE_SYNTHETIC' -AsPlainText -Force }
$taskResults = @()
try {
    foreach ($taskPrior in @($null,'PREEXISTING_SYNTHETIC')) {
        foreach ($taskAction in @('Preflight','Run')) {
            foreach ($taskCode in @(0,2)) {
                if ($null -eq $taskPrior) { Remove-Item Env:OPENROUTER_API_KEY -ErrorAction SilentlyContinue }
                else { [Environment]::SetEnvironmentVariable('OPENROUTER_API_KEY',$taskPrior,'Process') }
                $global:FakeCalls=0; $global:FakeExit=$taskCode; $taskFailed=$false
                try { & (Join-Path $PSScriptRoot 'Start-Experiments.ps1') -PythonPath $taskFake -Action $taskAction } catch { $taskFailed=$true }
                $taskExpected=1; if ($taskAction -eq 'Run' -and $taskCode -eq 0) { $taskExpected=2 }
                if ($global:FakeCalls -ne $taskExpected -or $taskFailed -ne ($taskCode -ne 0)) { throw 'Unexpected control flow' }
                if ((Test-Path Env:OPENROUTER_API_KEY) -ne ($null -ne $taskPrior)) { throw 'Environment presence restore failure' }
                if ($null -ne $taskPrior -and [Environment]::GetEnvironmentVariable('OPENROUTER_API_KEY','Process') -ne $taskPrior) { throw 'Environment value restore failure' }
                $taskResults += @{prior_present=($null -ne $taskPrior);action=$taskAction;mock_exit=$taskCode;calls=$global:FakeCalls;passed=$true}
            }
        }
    }
    $taskResults | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'powershell51-tests.json') -Encoding UTF8
} finally {
    if ($taskOriginallyPresent) { [Environment]::SetEnvironmentVariable('OPENROUTER_API_KEY',$taskOriginal,'Process') }
    else { Remove-Item Env:OPENROUTER_API_KEY -ErrorAction SilentlyContinue }
    # Keep harmless temporary mock helper as negative-result/debug evidence; no secrets used.
}


