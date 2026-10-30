$ErrorActionPreference = 'Stop'
& 'C:/Users/A/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B (Join-Path $PSScriptRoot 'fetch_results.py')
if ($LASTEXITCODE -ne 0) { throw 'Git return fetch/import stopped; preserve evidence. No EDA was executed.' }
