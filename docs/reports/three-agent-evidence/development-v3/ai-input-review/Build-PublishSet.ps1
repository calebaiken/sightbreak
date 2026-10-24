# Documentation packaging only. This script never runs Godot, git, a campaign,
# or an archived runner. Its only writes are under the pinned publication root.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = 'C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3\docs\reports\three-agent-evidence\development-v3\ai-input-review'
$external = 'C:\Users\blith\AppData\Local\Temp\opencode\sol-ai-evidence-20261019'
$expectedLedgerHash = '726e035f325d2d1f0a1f254ce35314dbdedfbed263385d4d696a4b1150933b68'
if ([IO.Path]::GetFullPath($PSScriptRoot) -ne $root) { throw 'Publication path is not the authorized root.' }
$utf8 = [Text.UTF8Encoding]::new($false)
function Hash([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
function Destination([string]$Relative) {
    $path = [IO.Path]::GetFullPath((Join-Path $root $Relative))
    if (-not $path.StartsWith($root + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw "Out-of-scope write: $Relative" }
    return $path
}
function Write-Json([string]$Relative, $Data) {
    $path = Destination $Relative
    [IO.Directory]::CreateDirectory((Split-Path $path)) | Out-Null
    [IO.File]::WriteAllText($path, ($Data | ConvertTo-Json -Depth 60) + "`n", $utf8)
}
$ledgerPath = Join-Path $external 'SHA256SUMS.txt'
if ((Hash $ledgerPath) -ne $expectedLedgerHash) { throw 'Original external checksum ledger changed.' }
$inventory = [Collections.Generic.List[object]]::new()
$lookup = @{}
foreach ($line in [IO.File]::ReadAllLines($ledgerPath)) {
    if ($line -notmatch '^([a-f0-9]{64})  (.+)$') { throw 'Malformed external checksum entry.' }
    $expected = $Matches[1]
    $relative = $Matches[2].Replace('\','/')
    $path = Join-Path $external $relative
    if ((Hash $path) -ne $expected) { throw "Original evidence hash mismatch: $relative" }
    $item = [ordered]@{external_path=$relative; bytes=(Get-Item -LiteralPath $path).Length; sha256=$expected}
    $inventory.Add($item)
    $lookup[$relative] = $item
}
if ($inventory.Count -ne 341) { throw 'Expected the complete original 341-payload-file bundle.' }
$externalFiles = @(Get-ChildItem -LiteralPath $external -File -Recurse)
if ($externalFiles.Count -ne 342) { throw 'External bundle has unexpected additional or missing files.' }
$selection = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($file in @(
    'commands.jsonl','commands-started.jsonl','comparison-summary.json',
    'sealed-source-manifest.json','source-sha256.json','source-verification.json',
    'neutral-first-assessment.md','neutral-worktrees.json','neutral-worktrees.attempt1.json',
    'initial-attempts.md','protocol.md',
    'native_contract_probe.gd','native_elimination_contract.gd','native_equipment_contract.gd',
    'native_behavior_probe.gd','native_policy_probe.gd','Summarize-Results.ps1',
    'Invoke-Recorded.ps1','Run-Probe.ps1','Run-Retained.ps1','Run-Confirmations.ps1'
)) { $selection.Add($file) | Out-Null }
foreach ($dir in @('runtime-north','runtime-south','extra-north','extra-south','host-failures')) {
    foreach ($file in Get-ChildItem (Join-Path $external $dir) -File -Recurse) {
        $selection.Add([IO.Path]::GetRelativePath($external, $file.FullName).Replace('\','/')) | Out-Null
    }
}
foreach ($stem in @(
    'engine-version','north-import','south-import','north-match-check-only','south-match-check-only',
    'candidate-commit-claims','candidate-commit-delta','candidate-branch-game-changes','candidate-merge-base',
    'candidate-main-native-smoke','retained-file-list','initial-source-status',
    'north-final-status','north-final-head-r3','south-final-head-r3',
    'north-final-status-r3','south-final-status-r3','owner-final-status-r3'
)) {
    foreach ($stream in @('stdout','stderr')) { $selection.Add("logs/$stem.$stream.log") | Out-Null }
}
# Preserve every archived retained-V2 .log, including its earlier failed imports,
# indentation/expectation attempts, and controls. These are historical, not PR14 reruns.
foreach ($file in Get-ChildItem "$external\retained-v2" -File -Filter '*.log') {
    $selection.Add('retained-v2/' + $file.Name) | Out-Null
}
foreach ($probe in @('module_probe','authority_contract_probe','integration_controls','objective_controls','native_comparison_extended')) {
    $selection.Add("retained-v2/$probe.gd") | Out-Null
}
$copied = [Collections.Generic.List[object]]::new()
foreach ($relative in $selection | Sort-Object) {
    if (-not $lookup.ContainsKey($relative)) { throw "Selection is absent from original ledger: $relative" }
    $source = Join-Path $external $relative
    $destinationRelative = 'evidence/' + $relative
    $destination = Destination $destinationRelative
    [IO.Directory]::CreateDirectory((Split-Path $destination)) | Out-Null
    if (-not (Test-Path -LiteralPath $destination)) { [IO.File]::Copy($source, $destination, $false) }
    if ((Hash $destination) -ne $lookup[$relative].sha256) { throw "Copy differs from original: $relative" }
    $copied.Add([ordered]@{package_path=$destinationRelative; external_path=$relative; bytes=$lookup[$relative].bytes; sha256=$lookup[$relative].sha256})
}
$ledgerCopy = Destination 'provenance/external-SHA256SUMS.txt'
[IO.Directory]::CreateDirectory((Split-Path $ledgerCopy)) | Out-Null
if (-not (Test-Path -LiteralPath $ledgerCopy)) { [IO.File]::Copy($ledgerPath, $ledgerCopy, $false) }
if ((Hash $ledgerCopy) -ne $expectedLedgerHash) { throw 'Copied external ledger differs.' }
Write-Json 'provenance/copied-files.json' @($copied.ToArray())
$omitted = foreach ($item in $inventory) {
    if (-not $selection.Contains($item.external_path)) {
        [ordered]@{external_path=$item.external_path; bytes=$item.bytes; sha256=$item.sha256; retained_at=$external}
    }
}
Write-Json 'provenance/omitted-files.json' @($omitted)

# Derived receipts retain original timestamp strings, argument arrays and stream
# hashes. File reads were not instrumented; do not invent a claims-read timestamp.
$allReceipts = [Collections.Generic.List[object]]::new()
foreach ($ledger in @('commands.jsonl','runtime-north/commands.jsonl','runtime-south/commands.jsonl','extra-north/commands.jsonl','extra-south/commands.jsonl')) {
    $lineNumber = 0
    foreach ($line in [IO.File]::ReadAllLines((Join-Path $external $ledger))) {
        $lineNumber++
        $record = $line | ConvertFrom-Json
        # PowerShell may auto-convert ISO dates and drop insignificant trailing
        # zeros when reserializing. Keep the original UTC strings verbatim.
        foreach ($key in @('started_utc','finished_utc')) {
            $match = [regex]::Match($line, '"' + $key + '"\s*:\s*"([^"]+)"')
            if ($match.Success) { $record.$key = $match.Groups[1].Value }
        }
        $allReceipts.Add([pscustomobject]@{ledger=$ledger; line=$lineNumber; record=$record})
    }
}
$compileReceipts = foreach ($label in @('north','south')) {
    $entry = @($allReceipts | Where-Object { $_.ledger -eq 'commands.jsonl' -and $_.record.name -eq "$label-match-check-only" })
    if ($entry.Count -ne 1) { throw "Expected one direct compile receipt for $label." }
    [ordered]@{
        label=$label; original_ledger='evidence/commands.jsonl'; original_line=$entry[0].line
        receipt=$entry[0].record
        package_stdout="evidence/logs/$label-match-check-only.stdout.log"
        package_stderr="evidence/logs/$label-match-check-only.stderr.log"
    }
}
Write-Json 'provenance/compile-receipts.json' @($compileReceipts)
$events = foreach ($entry in $allReceipts) {
    if ($entry.ledger.StartsWith('runtime-') -or $entry.record.name -in @(
        'engine-version','north-import','south-import','exact-diff-stat','exact-diff-names','exact-ai-diff',
        'candidate-commit-claims','north-match-check-only','south-match-check-only'
    )) {
        [ordered]@{original_ledger=('evidence/' + $entry.ledger); original_line=$entry.line; receipt=$entry.record}
    }
}
$metadata = foreach ($relative in @('neutral-first-assessment.md','sealed-source-manifest.json','logs/candidate-commit-claims.stdout.log')) {
    $file = Get-Item -LiteralPath (Join-Path $external $relative)
    [ordered]@{external_path=$relative; sha256=(Hash $file.FullName); creation_utc=$file.CreationTimeUtc.ToString('o'); last_write_utc=$file.LastWriteTimeUtc.ToString('o')}
}
Write-Json 'provenance/chronology.json' ([ordered]@{
    metadata_captured_utc=[DateTime]::UtcNow.ToString('o')
    limitation='Process timestamps are original receipts; file timestamps are later-observed NTFS metadata, not signed read events. Pre-claim ordering and non-consumption are reviewer attestations in the unchanged neutral assessment.'
    original_file_metadata=@($metadata); command_events=@($events | Sort-Object { $_.receipt.started_utc })
})

# Line-numbered extracts, not full source snapshots. Recover the exact parent
# file using the git-show command in its original ledger if more context is needed.
$sourceManifest = Get-Content "$external\sealed-source-manifest.json" -Raw | ConvertFrom-Json
$nativeHashes = Get-Content "$external\source-sha256.json" -Raw | ConvertFrom-Json
$extractSpecs = @(
    @{side='candidate'; file='bot_ai.gd'; ranges=@(@(1,55),@(75,81),@(113,146),@(148,172),@(177,251),@(262,310),@(451,501),@(516,607),@(624,637),@(713,767))},
    @{side='candidate'; file='match.gd'; ranges=@(@(13,16),@(25,46),@(198,215),@(373,403),@(450,457))},
    @{side='candidate'; file='actor.gd'; ranges=@(@(30,51),@(490,537),@(603,613))},
    @{side='candidate'; file='arena.gd'; ranges=@(@(1,13))},
    @{side='candidate'; file='weapons.gd'; ranges=@(@(1,13))},
    @{side='baseline'; file='bot_ai.gd'; ranges=@(@(17,65),@(86,93),@(185,227),@(264,277),@(348,418),@(487,522),@(644,674),@(686,698))},
    @{side='baseline'; file='match.gd'; ranges=@(@(438,464),@(526,533))}
)
$extracts = foreach ($spec in $extractSpecs) {
    $label = if ($spec.side -eq 'candidate') { 'south' } else { 'north' }
    $tree = $sourceManifest.worktrees | Where-Object label -eq $label
    $relative = "$($spec.side)-source/$($spec.file)"
    $path = Join-Path $external $relative
    $lines = [IO.File]::ReadAllLines($path)
    $repoPath = 'game/scripts/gameplay/' + $spec.file
    $treeLine = @(Get-Content "$external\logs\$label-source-tree.stdout.log" | Where-Object { $_.EndsWith("`t$repoPath") })
    if ($treeLine.Count -ne 1 -or $treeLine[0] -notmatch '^\d+ blob ([a-f0-9]{40})\t') { throw "Cannot resolve source blob: $repoPath" }
    $blob = $Matches[1]
    $native = @($nativeHashes | Where-Object { $_.label -eq $label -and [IO.Path]::GetFileName($_.path) -eq $spec.file })
    $rangePairs = $spec.ranges
    # A one-range @(@(first,last)) literal is flattened by PowerShell. Rebox it
    # before iteration; multi-range specifications are already nested arrays.
    if ($rangePairs[0] -is [int]) { $rangePairs = ,$rangePairs }
    $ranges = foreach ($range in $rangePairs) {
        if ($range[1] -gt $lines.Count) { throw "Source excerpt out of range: $relative" }
        [ordered]@{first_line=$range[0]; last_line=$range[1]; text=($lines[($range[0]-1)..($range[1]-1)] -join "`n")}
    }
    [ordered]@{
        commit=$tree.commit; repository_path=$repoPath; git_blob_sha1=$blob
        external_snapshot=$relative; snapshot_sha256=$lookup[$relative].sha256
        native_worktree_sha256=$native[0].sha256
        recovery_command=@('git','show',"$($tree.commit):$repoPath")
        excerpt_encoding='JSON strings; LF-joined source lines, not a byte-for-byte whole-file copy'
        ranges=@($ranges)
    }
}
Write-Json 'provenance/source-excerpts.json' @($extracts)

# Analysis only: verify repeated captured streams rather than rerunning tests.
$repeats = foreach ($label in @('north','south')) {
    foreach ($probe in @('native_behavior_probe','native_policy_probe','native_contract_probe','native_equipment_contract')) {
        $r1 = "evidence/extra-$label/logs/$probe-r1.stdout.log"
        $r2 = "evidence/extra-$label/logs/$probe-r2.stdout.log"
        [ordered]@{label=$label; probe=$probe; r1=$r1; r2=$r2; r1_sha256=(Hash (Destination $r1)); r2_sha256=(Hash (Destination $r2)); byte_identical=(Hash (Destination $r1)) -eq (Hash (Destination $r2))}
    }
}
Write-Json 'provenance/repeat-verification.json' @($repeats)
Write-Json 'provenance/publication-receipt.json' ([ordered]@{
    packaged_utc=[DateTime]::UtcNow.ToString('o'); allowed_write_root=$root; external_root=$external
    original_external_payload_files=341; original_external_total_files=342
    original_external_total_bytes=($externalFiles | Measure-Object Length -Sum).Sum
    external_checksum_ledger_sha256=$expectedLedgerHash; external_payload_hash_mismatches=0
    copied_payload_files=$copied.Count; copied_payload_bytes=($copied.ToArray() | ForEach-Object { $_['bytes'] } | Measure-Object -Sum).Sum
    omitted_payload_files=@($omitted).Count; omitted_payload_bytes=(@($omitted) | ForEach-Object { $_['bytes'] } | Measure-Object -Sum).Sum
    external_report_sha256=$lookup['REPORT.md'].sha256
    new_native_runs=0; packaging_script_git_invocations=0; git_mutations=0; runtime_or_owner_branch_writes=0
    read_only_git_status='Read-only git --no-optional-locks status was used outside this script to inspect the already-dirty integration; no index/branch mutation or campaign was performed.'
    integration_policy='Retain V2 bot runtime; do not wholesale merge 48eb058. Documentation packaging is not acceptance.'
    authored_documents='REPORT.md, CHRONOLOGY.md, COMMANDS.md, PACKAGE.md, PACKAGING-ATTEMPTS.md and Build-PublishSet.ps1 were authored with patch; JSON receipts and checksum ledger are mechanically derived.'
})
if ((Hash $ledgerPath) -ne $expectedLedgerHash) { throw 'Original ledger changed during packaging.' }
$checksumLines = foreach ($file in Get-ChildItem -LiteralPath $root -File -Recurse | Sort-Object FullName) {
    if ($file.FullName -eq "$root\SHA256SUMS.txt") { continue }
    '{0}  {1}' -f (Hash $file.FullName), [IO.Path]::GetRelativePath($root,$file.FullName).Replace('\','/')
}
[IO.File]::WriteAllLines((Destination 'SHA256SUMS.txt'), [string[]]$checksumLines, $utf8)
foreach ($line in $checksumLines) {
    $parts = $line -split '  ',2
    if ((Hash (Destination $parts[1])) -ne $parts[0]) { throw "Publication hash mismatch: $($parts[1])" }
}
$files = @(Get-ChildItem -LiteralPath $root -File -Recurse)
[ordered]@{
    package_root=$root; files=$files.Count; bytes=($files | Measure-Object Length -Sum).Sum
    checksummed_payload_files=$checksumLines.Count; checksum_mismatches=0
    copied_original_payload_files=$copied.Count; omitted_original_payload_files=@($omitted).Count
    report_sha256=(Hash "$root\REPORT.md"); checksum_ledger_sha256=(Hash "$root\SHA256SUMS.txt")
} | ConvertTo-Json -Depth 5
