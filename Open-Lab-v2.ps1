$ErrorActionPreference = 'Stop'
$candidates = @($env:RTL_LAB_PYTHON)
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCommand -and $pythonCommand.Source -notlike '*\WindowsApps\*') { $candidates += $pythonCommand.Source }
$candidates += (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe')
foreach ($candidate in $candidates) {
    if ($candidate -and (Test-Path -LiteralPath $candidate -PathType Leaf)) {
        & $candidate -c 'import sys, tkinter; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>$null
        if ($LASTEXITCODE -ne 0) { continue }
        $windowed = Join-Path (Split-Path $candidate) 'pythonw.exe'
        if (-not (Test-Path -LiteralPath $windowed)) { $windowed = $candidate }
        Start-Process -FilePath $windowed -ArgumentList @('"' + (Join-Path $PSScriptRoot 'console_gui_v2.py') + '"') -WorkingDirectory $PSScriptRoot -WindowStyle Normal
        exit 0
    }
}
throw 'Python 3.10+ with tkinter is required. Set RTL_LAB_PYTHON to python.exe.'
