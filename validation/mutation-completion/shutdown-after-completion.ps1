param([switch]$ValidateOnly)
$ErrorActionPreference = 'Stop'
$repo = 'E:\Codex\2026-09-25\xzy01-using-llm-for-digital-chip-2\outputs\rtl-batch'
$stateDir = Join-Path $repo 'validation\mutation-completion'
function Assert-Completion {
    [void](Get-Command Stop-Computer -ErrorAction Stop)
    $receipt = Get-Content -LiteralPath (Join-Path $stateDir 'completion.json') -Raw | ConvertFrom-Json
    if ($receipt.status -ne 'COMPLETE' -or $receipt.ci_conclusion -ne 'success' -or $receipt.new_model_calls -ne 0 -or $receipt.mutants -ne 163 -or $receipt.detected_mutants -ne 163 -or $receipt.calibration_passes -ne 25) { throw 'Completion criteria not satisfied' }
    $head = (& git -C $repo rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0 -or $head -ne $receipt.git_head -or $head -ne $receipt.remote_head) { throw 'Repository commit mismatch' }
    $dirty = & git -C $repo status --porcelain
    if ($LASTEXITCODE -ne 0 -or $dirty) { throw 'Repository has unfinished edits' }
    foreach ($artifact in $receipt.archives) {
        $hasher = [System.Security.Cryptography.SHA256]::Create()
        $stream = [System.IO.File]::OpenRead($artifact.path)
        try { $hash = [System.BitConverter]::ToString($hasher.ComputeHash($stream)).Replace('-', '').ToLowerInvariant() } finally { $stream.Dispose(); $hasher.Dispose() }
        if ($hash -ne $artifact.sha256) { throw 'Archive hash mismatch' }
    }
}
try {
    Assert-Completion
    if ($ValidateOnly) { Write-Output 'Completion gates verified; no shutdown issued'; exit 0 }
    @{ status='SCHEDULED'; scheduled_at=(Get-Date).ToString('o'); delay_seconds=90; force=$false; process_id=$PID } | ConvertTo-Json | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $stateDir 'shutdown-status.json')
    Start-Sleep -Seconds 90
    Assert-Completion
    Set-Content -Encoding UTF8 -LiteralPath (Join-Path $stateDir 'release-awake') -Value 'Task complete'
    @{ status='NORMAL_SHUTDOWN_REQUESTED'; requested_at=(Get-Date).ToString('o'); force=$false } | ConvertTo-Json | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $stateDir 'shutdown-status.json')
    Stop-Computer -ErrorAction Stop
} catch {
    @{ status='SHUTDOWN_ABORTED_OR_FAILED'; recorded_at=(Get-Date).ToString('o'); message=$_.Exception.Message; force=$false } | ConvertTo-Json | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $stateDir 'shutdown-status.json')
    exit 1
}
