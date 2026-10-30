$ErrorActionPreference = 'Stop'
& 'C:/Users/A/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B (Join-Path $PSScriptRoot 'collect.py')
exit $LASTEXITCODE
