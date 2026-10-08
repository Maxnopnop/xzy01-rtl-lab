# Examples and complete workflow: ECE_DESKTOP_GUIDE.md
$ErrorActionPreference = 'Stop'
$runtimePython = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
if (!(Test-Path -LiteralPath $runtimePython)) {
    $runtimePython = (Get-Command python -ErrorAction Stop).Source
}
& $runtimePython (Join-Path $PSScriptRoot 'ece_transfer.py') @args
exit $LASTEXITCODE
