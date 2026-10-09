$ErrorActionPreference = 'Stop'
$candidates = @($env:RTL_LAB_PYTHON)
$cmd = Get-Command python -ErrorAction SilentlyContinue
if ($cmd -and $cmd.Source -notlike '*\WindowsApps\*') { $candidates += $cmd.Source }
$candidates += (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe')
foreach ($pythonPath in $candidates) {
    if ($pythonPath -and (Test-Path -LiteralPath $pythonPath -PathType Leaf)) {
        Push-Location $PSScriptRoot
        try { & $pythonPath (Join-Path $PSScriptRoot 'model_platform.py') @args; $modelExit = $LASTEXITCODE }
        finally { Pop-Location }
        exit $modelExit
    }
}
throw 'Python 3.10+ not found. Set RTL_LAB_PYTHON.'
