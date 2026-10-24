param()

$ErrorActionPreference = 'Stop'
$BlindRoot = 'C:\Users\blith\AppData\Local\Temp\opencode\sol-visual-20261019-b83f76-evidence\blind'
$ReferenceRoot = 'C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3-evidence\cs2-references-20261019'
$OutputRoot = $PSScriptRoot
$Utf8 = [System.Text.UTF8Encoding]::new($false)

# This auditor reads only the blinded packet, four allowed references, and this
# new verdict directory. It never writes to inputs, executes the engine, or
# reads a mapping, a private directory, repository code, or source history.
foreach ($name in @('inspected-images.json', 'integrity-check.json', 'freeze.json', 'SHA256SUMS.txt')) {
    if (Test-Path -LiteralPath (Join-Path $OutputRoot $name)) {
        throw "Refusing to overwrite existing frozen output: $name"
    }
}

function Write-NewText([string]$Name, [string]$Text) {
    $path = Join-Path $OutputRoot $Name
    $stream = [System.IO.File]::Open($path, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write)
    try {
        $bytes = $Utf8.GetBytes($Text)
        $stream.Write($bytes, 0, $bytes.Length)
    } finally {
        $stream.Dispose()
    }
}

function Read-Json([string]$Path) {
    return (Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json -Depth 100)
}

function Get-Hash([string]$Path) {
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
}

function Resolve-Contained([string]$Root, [string]$Relative) {
    $rootFull = [System.IO.Path]::GetFullPath($Root).TrimEnd('\') + '\'
    $full = [System.IO.Path]::GetFullPath((Join-Path $Root $Relative))
    if (-not $full.StartsWith($rootFull, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Path escapes its explicitly allowed input root: $Relative"
    }
    return $full
}

$index = Read-Json (Join-Path $BlindRoot 'index.json')
$judgments = Read-Json (Join-Path $OutputRoot 'pair-judgments.json')
$sequences = Read-Json (Join-Path $OutputRoot 'sequence-judgments.json')
$scores = Read-Json (Join-Path $OutputRoot 'scoped-scores.json')
$expectedTicks = @(0, 58, 66, 67, 74, 78, 82, 98, 110, 118, 126, 134, 146)

if ($index.pairs.Count -ne 39 -or $judgments.pairs.Count -ne 39) { throw 'Pair count must be 39.' }
if ($sequences.sequences.Count -ne 3 -or $scores.categories.Count -ne 7) { throw 'Sequence/category count mismatch.' }
$seen = @{}
foreach ($row in $judgments.pairs) {
    $key = "$($row.sequence):$($row.pair)"
    if ($seen.ContainsKey($key)) { throw "Duplicate pair: $key" }
    $seen[$key] = $true
    if ($row.winner -notin @('A', 'B', 'tie', 'uncertain', 'inconclusive')) { throw "Invalid winner: $key" }
    if ($row.confidence -notin @('low', 'medium', 'high')) { throw "Invalid confidence: $key" }
    if ($row.tick -ne $expectedTicks[$row.pair]) { throw "Tick mismatch: $key" }
    $match = @($index.pairs | Where-Object { $_.sequence -eq $row.sequence -and $_.pair -eq $row.pair })
    if ($match.Count -ne 1 -or $match[0].tick -ne $row.tick) { throw "Index mismatch: $key" }
}
foreach ($sequence in @('01', '02', '03')) {
    $rows = @($judgments.pairs | Where-Object sequence -eq $sequence)
    if ($rows.Count -ne 13) { throw "Sequence $sequence must have 13 rows." }
}

Add-Type -AssemblyName System.Drawing
$inspected = [System.Collections.Generic.List[object]]::new()
function Add-InspectedImage([string]$Root, [string]$Relative, [string]$Role, [object]$Sequence, [object]$Pair, [object]$Tick) {
    $path = Resolve-Contained $Root $Relative
    $file = Get-Item -LiteralPath $path
    $image = [System.Drawing.Image]::FromFile($path)
    try {
        $width = $image.Width
        $height = $image.Height
    } finally {
        $image.Dispose()
    }
    if ($Role -eq 'individual_native_pair' -and ($width -ne 1280 -or $height -ne 720)) {
        throw "Native dimensions mismatch: $Relative"
    }
    $inspected.Add([ordered]@{
        root = $Root
        relative_path = $Relative.Replace('\', '/')
        full_path = $path
        role = $Role
        sequence = $Sequence
        pair = $Pair
        tick = $Tick
        bytes = $file.Length
        width = $width
        height = $height
        sha256 = Get-Hash $path
        visually_inspected = $true
        visual_tool = 'functions.read'
        note = 'Unique image entry; some images were reinspected. Hashing/dimension decoding did not modify the file.'
    })
}

foreach ($sequence in @('01', '02', '03')) {
    foreach ($part in @('pickup', 'return-ready')) {
        Add-InspectedImage $BlindRoot "contact-sheets/sequence$sequence-$part.png" 'chronological_contact_sheet' $sequence $null $null
    }
}
foreach ($row in $index.pairs) {
    Add-InspectedImage $BlindRoot $row.a_native_lossless 'individual_native_pair' $row.sequence $row.pair $row.tick
    Add-InspectedImage $BlindRoot $row.b_native_lossless 'individual_native_pair' $row.sequence $row.pair $row.tick
}
$referenceNames = @('first-person-rifle.jpg', 'nuke-bombsite-a.jpg', 'operators.jpg', 'smoke.jpg')
foreach ($name in $referenceNames) {
    Add-InspectedImage $ReferenceRoot $name 'official_valve_still_reference' $null $null $null
}
if ($inspected.Count -ne 88) { throw 'Expected 88 unique inspected images.' }
if (@($inspected.full_path | Sort-Object -Unique).Count -ne 88) { throw 'Inspected image list contains duplicates.' }

$packetSnapshot = [System.Collections.Generic.List[object]]::new()
$packetHashes = @{}
foreach ($file in (Get-ChildItem -LiteralPath $BlindRoot -File -Recurse | Sort-Object FullName)) {
    $relative = [System.IO.Path]::GetRelativePath($BlindRoot, $file.FullName).Replace('\', '/')
    $hash = Get-Hash $file.FullName
    $packetHashes[$relative] = $hash
    $packetSnapshot.Add([ordered]@{path=$relative; bytes=$file.Length; sha256=$hash; visually_inspected=($inspected.full_path -contains $file.FullName)})
}
$providedManifest = Read-Json (Join-Path $BlindRoot 'sha256-manifest.json')
$manifestMismatches = [System.Collections.Generic.List[object]]::new()
foreach ($entry in $providedManifest.files) {
    $null = Resolve-Contained $BlindRoot $entry.path
    $relative = $entry.path.Replace('\', '/')
    if (-not $packetHashes.ContainsKey($relative) -or $packetHashes[$relative] -ne $entry.sha256.ToLowerInvariant()) {
        $manifestMismatches.Add([ordered]@{path=$relative; expected=$entry.sha256; actual=$packetHashes[$relative]})
    }
}
if ($manifestMismatches.Count -gt 0) { throw 'Blinded packet hash mismatch; do not freeze.' }

$referenceManifestPath = Join-Path $ReferenceRoot 'manifest.json'
$referenceManifest = Read-Json $referenceManifestPath
$referenceChecks = [System.Collections.Generic.List[object]]::new()
foreach ($name in $referenceNames) {
    $entry = @($referenceManifest.references | Where-Object file -eq $name)
    if ($entry.Count -ne 1) { throw "Missing/ambiguous official reference: $name" }
    $actual = Get-Hash (Resolve-Contained $ReferenceRoot $name)
    $matches = ($actual -eq $entry[0].sha256.ToLowerInvariant())
    if (-not $matches) { throw "Official reference hash mismatch: $name" }
    $referenceChecks.Add([ordered]@{file=$name; sha256=$actual; matches_provided_manifest=$matches; publisher_url=$entry[0].url; capture_date='not supplied by publisher'})
}

$inventory = [ordered]@{
    schema_version = 1
    unique_visually_inspected_images = $inspected.Count
    native_originals = 78
    contact_sheets = 6
    official_reference_stills = 4
    actual_native_dimensions_verified = $true
    declaration = 'Visual inspection was performed using functions.read before this read-only hash/dimension audit. Hash-only packet files are not visually inspected.'
    images = $inspected.ToArray()
}
Write-NewText 'inspected-images.json' (($inventory | ConvertTo-Json -Depth 30) + "`n")

$integrity = [ordered]@{
    schema_version = 1
    checked_utc = [DateTime]::UtcNow.ToString('o')
    blind_root = $BlindRoot
    input_writes_performed = $false
    original_packet_preserved = $true
    blind_manifest_sha256 = Get-Hash (Join-Path $BlindRoot 'sha256-manifest.json')
    provided_blind_manifest_entries_checked = $providedManifest.files.Count
    provided_blind_manifest_mismatches = $manifestMismatches.ToArray()
    packet_snapshot_file_count = $packetSnapshot.Count
    packet_snapshot = $packetSnapshot.ToArray()
    reference_manifest_sha256 = Get-Hash $referenceManifestPath
    reference_checks = $referenceChecks.ToArray()
    note = 'Snapshot is restricted to blind/. No parent/private/mapping/source identity content was read. A file may be hashed without being visually inspected. Original-manifest matching covers every entry present in that manifest; the snapshot additionally hashes all files now in blind/.'
}
Write-NewText 'integrity-check.json' (($integrity | ConvertTo-Json -Depth 30) + "`n")

$artifactNames = @('verdict.md', 'pair-judgments.json', 'sequence-judgments.json', 'scoped-scores.json', 'audit.ps1', 'inspected-images.json', 'integrity-check.json')
$artifactHashes = [System.Collections.Generic.List[object]]::new()
foreach ($name in $artifactNames) {
    $path = Join-Path $OutputRoot $name
    $artifactHashes.Add([ordered]@{file=$name; bytes=(Get-Item -LiteralPath $path).Length; sha256=Get-Hash $path})
}
$freeze = [ordered]@{
    schema_version = 1
    status = 'frozen_before_unblinding'
    frozen_at_utc = [DateTime]::UtcNow.ToString('o')
    output_directory = $OutputRoot
    reviewer_declarations = [ordered]@{
        private_mapping_opened = $false
        source_identities_inspected = $false
        ownership_or_newness_inferred = $false
        source_code_inspected = $false
        project_source_edited = $false
        engine_executed = $false
        performance_claims_used = $false
        github_used = $false
        historical_rubric_preview_incident = $true
        historical_scores_used_as_evidence = $false
        identity_blind_but_not_completely_prior_assessment_naive = $true
        stop_without_unblinding = $true
    }
    validation = [ordered]@{pair_rows=39; sequences=3; categories=7; unique_images=88; native_images=78; native_size=@(1280,720); blinded_manifest_all_entries_match=$true; official_reference_hashes_match=$true}
    artifact_hashes = $artifactHashes.ToArray()
}
Write-NewText 'freeze.json' (($freeze | ConvertTo-Json -Depth 30) + "`n")

$sumLines = [System.Collections.Generic.List[string]]::new()
foreach ($name in ($artifactNames + @('freeze.json'))) {
    $sumLines.Add("$(Get-Hash (Join-Path $OutputRoot $name))  $name")
}
Write-NewText 'SHA256SUMS.txt' (($sumLines -join "`n") + "`n")

[ordered]@{
    output_directory=$OutputRoot
    frozen_at_utc=$freeze.frozen_at_utc
    pair_rows=39
    unique_images=88
    native_size_verified='1280x720 for all 78 native originals'
    blind_manifest_entries_checked=$providedManifest.files.Count
    blind_manifest_mismatches=0
    reference_hashes_match=4
    verdict_sha256=Get-Hash (Join-Path $OutputRoot 'verdict.md')
    pair_judgments_sha256=Get-Hash (Join-Path $OutputRoot 'pair-judgments.json')
    freeze_sha256=Get-Hash (Join-Path $OutputRoot 'freeze.json')
    sha256sums_sha256=Get-Hash (Join-Path $OutputRoot 'SHA256SUMS.txt')
} | ConvertTo-Json -Depth 10
