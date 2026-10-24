# Freeze the permitted external review artifacts. No implementation/key access.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$root = $PSScriptRoot
$utf8 = [System.Text.UTF8Encoding]::new($false)
$names = @('NEUTRAL_VERDICT.md', 'per_workload_assessment.json', 'source_hashes.json', 'audit_packet.ps1', 'freeze_artifacts.ps1')
if ((Test-Path -LiteralPath (Join-Path $root 'FROZEN.json')) -or (Test-Path -LiteralPath (Join-Path $root 'SHA256SUMS.txt'))) {
    throw 'Already frozen: preserve original and use a separate addendum.'
}
$actualNames = @(Get-ChildItem -LiteralPath $root -Force -File | ForEach-Object { $_.Name } | Sort-Object)
if (@(Compare-Object -ReferenceObject @($names | Sort-Object) -DifferenceObject $actualNames -CaseSensitive).Count -ne 0) {
    throw 'Unexpected or missing external payload file.'
}
$assessment = [System.IO.File]::ReadAllText((Join-Path $root 'per_workload_assessment.json'), $utf8) | ConvertFrom-Json
$sources = [System.IO.File]::ReadAllText((Join-Path $root 'source_hashes.json'), $utf8) | ConvertFrom-Json
$packetRoot = $sources.packet_root
foreach ($entry in $sources.packet_source_files) {
    $actualHash = (Get-FileHash -LiteralPath (Join-Path $packetRoot $entry.path) -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualHash -cne $entry.sha256) { throw "Input changed before freeze: $($entry.path)" }
}
if ($assessment.totals.workload_records -ne 14 -or $assessment.totals.retained_timed_samples -ne 140 -or $assessment.decision.preferred_label -cne 'K') {
    throw 'Assessment totals/decision changed.'
}
$artifacts = @($names | Sort-Object | ForEach-Object {
    $path = Join-Path $root $_
    [ordered]@{ path = $_; bytes = ([System.IO.FileInfo]::new($path)).Length; sha256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() }
})
$freeze = [ordered]@{
    schema = 'neutral-pre-unblinding-freeze-v1'
    frozen_utc = [datetime]::UtcNow.ToString('o')
    input_packet_root = $packetRoot
    input_packet_manifest_sha256 = $sources.actual_manifest_sha256
    blind_status_at_freeze = 'BLIND; no identity key/source/repository/owner report inspected; source binding deferred'
    narrow_verdict = $assessment.decision.narrow_verdict
    preferred_label = $assessment.decision.preferred_label
    full_semantic_and_authoritative_safety_bar_independently_established = $false
    workload_records_verified = 14
    timed_samples_verified = 140
    broad_gates = $assessment.decision.broad_gates
    artifacts = $artifacts
    preservation_rule = 'Do not modify frozen payloads; place any unblinding/source binding or changed judgment in a separate addendum citing this freeze.'
    timestamp_and_immutability_limit = 'Local UTC/hash record only, not an external trusted timestamp, signature, or filesystem immutability guarantee.'
}
[System.IO.File]::WriteAllText((Join-Path $root 'FROZEN.json'), (($freeze | ConvertTo-Json -Depth 12) + "`n"), $utf8)
$manifestLines = @(@($names + 'FROZEN.json') | Sort-Object | ForEach-Object {
    $digest = (Get-FileHash -LiteralPath (Join-Path $root $_) -Algorithm SHA256).Hash.ToLowerInvariant()
    "$digest  $_"
})
$manifestPath = Join-Path $root 'SHA256SUMS.txt'
[System.IO.File]::WriteAllText($manifestPath, (($manifestLines -join "`n") + "`n"), $utf8)
$verifiedEntries = 0
foreach ($line in [System.IO.File]::ReadAllLines($manifestPath, $utf8)) {
    if ($line -cnotmatch '^([0-9a-f]{64})  (.+)$') { throw 'Malformed external manifest' }
    $expected, $name = $Matches[1], $Matches[2]
    $actual = (Get-FileHash -LiteralPath (Join-Path $root $name) -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -cne $expected) { throw "External freeze verification failed: $name" }
    $verifiedEntries++
}
[ordered]@{
    directory = $root; frozen_utc = $freeze.frozen_utc; all_frozen_hashes_verified = $true; manifest_entries_verified = $verifiedEntries
    external_manifest_sha256 = (Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
    freeze_sha256 = (Get-FileHash -LiteralPath (Join-Path $root 'FROZEN.json') -Algorithm SHA256).Hash.ToLowerInvariant()
    verdict_sha256 = (Get-FileHash -LiteralPath (Join-Path $root 'NEUTRAL_VERDICT.md') -Algorithm SHA256).Hash.ToLowerInvariant()
    machine_assessment_sha256 = (Get-FileHash -LiteralPath (Join-Path $root 'per_workload_assessment.json') -Algorithm SHA256).Hash.ToLowerInvariant()
    source_hashes_sha256 = (Get-FileHash -LiteralPath (Join-Path $root 'source_hashes.json') -Algorithm SHA256).Hash.ToLowerInvariant()
} | ConvertTo-Json -Depth 8
