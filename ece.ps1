# Examples and complete workflow: ECE_DESKTOP_GUIDE.md
$ErrorActionPreference = 'Stop'
$runtimePython = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
if (!(Test-Path -LiteralPath $runtimePython)) {
    $runtimePython = (Get-Command python -ErrorAction Stop).Source
}
$entryScript = 'ece_transfer.py'
if ($args.Count -gt 0 -and $args[0] -in @('history','prepare','ingest','status','--state-dir')) {
    $entryScript = 'ece_workflow.py'
}
Push-Location $PSScriptRoot
try { & $runtimePython (Join-Path $PSScriptRoot $entryScript) @args }
finally { Pop-Location }
exit $LASTEXITCODE
