param([string]$Shared = 'C:/Users/A/Documents/FYP')
$ErrorActionPreference = 'Stop'
& 'C:/Users/A/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B (Join-Path $PSScriptRoot 'collect.py') --shared $Shared
if ($LASTEXITCODE -ne 0) { throw 'Return import rejected; preserve files. No tool was executed.' }
