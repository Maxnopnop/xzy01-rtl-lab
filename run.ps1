$ErrorActionPreference = 'Stop'
$candidates = @()
if ($env:RTL_LAB_PYTHON) { $candidates += $env:RTL_LAB_PYTHON }
$cmd = Get-Command python -ErrorAction SilentlyContinue
if ($cmd -and $cmd.Source -notlike '*\WindowsApps\*') { $candidates += $cmd.Source }
$candidates += (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe')
foreach ($pythonPath in $candidates) {
    if (Test-Path -LiteralPath $pythonPath -PathType Leaf) {
        & $pythonPath (Join-Path $PSScriptRoot 'batch.py') @args
        exit $LASTEXITCODE
    }
}
throw 'Python 3.10+ not found. Set RTL_LAB_PYTHON to a Python executable.'
