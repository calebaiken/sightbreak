param(
    [string]$PacketRoot = 'C:\Users\blith\AppData\Local\Temp\opencode\blind-trade-read-f12a80a71bbd\packet',
    [string]$OutputRoot = $PSScriptRoot
)

# Independent retained-file audit only. No repository, identity key, network,
# application, Python, native tests, database, or measurement run is accessed.
# Writes derived audit artifacts only in this explicitly authorized output folder.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$expectedManifest = 'd9a6ea8e0721d573bea5437e84fcc25b899d7b8172f092c4ae7d1415b3c56c36'
$utf8 = [System.Text.UTF8Encoding]::new($false)

function Assert-Condition([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw $Message }
}

function Get-Sha256([byte[]]$Bytes) {
    [System.Convert]::ToHexString([System.Security.Cryptography.SHA256]::HashData($Bytes)).ToLowerInvariant()
}

function Assert-NoDuplicateJsonKeys([System.Text.Json.JsonElement]$Element, [string]$Reference) {
    if ($Element.ValueKind -eq [System.Text.Json.JsonValueKind]::Object) {
        $seen = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
        foreach ($property in $Element.EnumerateObject()) {
            Assert-Condition ($seen.Add($property.Name)) "Duplicate JSON key: $Reference/$($property.Name)"
            Assert-NoDuplicateJsonKeys $property.Value "$Reference/$($property.Name)"
        }
    } elseif ($Element.ValueKind -eq [System.Text.Json.JsonValueKind]::Array) {
        $index = 0
        foreach ($child in $Element.EnumerateArray()) {
            Assert-NoDuplicateJsonKeys $child "$Reference/$index"
            $index++
        }
    }
}

function Read-Json([string]$RelativePath) {
    $text = [System.IO.File]::ReadAllText((Join-Path $PacketRoot $RelativePath), $utf8)
    $document = [System.Text.Json.JsonDocument]::Parse($text)
    try { Assert-NoDuplicateJsonKeys $document.RootElement "$RelativePath#" }
    finally { $document.Dispose() }
    ConvertFrom-Json -InputObject $text
}

function Get-Chunks([int]$Count) {
    while ($Count -gt 0) {
        $chunk = [math]::Min(500, $Count)
        [int]$chunk
        $Count -= $chunk
    }
}

function New-InSql([string]$Table, [int]$Count) {
    $columns = if ($Table -ceq 'items') {
        'items.id, items.owner_id, items.definition_id, items.rarity, items.pattern_seed, items.wear, items.variant, items.reservation, items.consumed, items.acquired_at'
    } elseif ($Table -ceq 'players') {
        'players.id, players.display_name'
    } else { throw 'Unexpected IN table' }
    $placeholders = (1..$Count | ForEach-Object { "%(id_1_$_)s::VARCHAR" }) -join ', '
    "SELECT $columns `nFROM $Table `nWHERE $Table.id IN ($placeholders)"
}

function Write-Json([string]$Name, $Value) {
    [System.IO.File]::WriteAllText((Join-Path $OutputRoot $Name), (($Value | ConvertTo-Json -Depth 40) + "`n"), $utf8)
}

Assert-Condition ([System.IO.Path]::GetFullPath($PacketRoot) -cne [System.IO.Path]::GetFullPath($OutputRoot)) 'Output must be outside packet'
Assert-Condition (-not (Test-Path -LiteralPath (Join-Path $OutputRoot 'FROZEN.json'))) 'Output is already frozen'
$manifestPath = Join-Path $PacketRoot 'SHA256SUMS.txt'
$manifestBytes = [System.IO.File]::ReadAllBytes($manifestPath)
$manifestSha = Get-Sha256 $manifestBytes
Assert-Condition ($manifestSha -ceq $expectedManifest) 'Manifest digest differs from supplied anchor'
$entries = [System.Collections.Generic.Dictionary[string,string]]::new([System.StringComparer]::Ordinal)
$sourceFiles = [System.Collections.Generic.List[object]]::new()
foreach ($line in [System.IO.File]::ReadAllLines($manifestPath, $utf8)) {
    Assert-Condition ($line -cmatch '^([0-9a-f]{64})  (.+)$') 'Malformed input manifest'
    $digest, $name = $Matches[1], $Matches[2]
    Assert-Condition (-not $entries.ContainsKey($name)) "Duplicate manifest path: $name"
    $fullPath = [System.IO.Path]::GetFullPath((Join-Path $PacketRoot $name))
    Assert-Condition ($fullPath.StartsWith($PacketRoot + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) 'Manifest path escapes packet'
    $bytes = [System.IO.File]::ReadAllBytes($fullPath)
    $actualSha = Get-Sha256 $bytes
    Assert-Condition ($actualSha -ceq $digest) "Packet hash mismatch: $name"
    $entries.Add($name, $digest)
    $sourceFiles.Add([ordered]@{ path = $name; bytes = $bytes.Length; sha256 = $actualSha; manifest_sha256 = $digest; verified = $true })
}
$allItems = @(Get-ChildItem -LiteralPath $PacketRoot -Recurse -Force)
Assert-Condition (@($allItems | Where-Object { ($_.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 }).Count -eq 0) 'Packet contains a reparse point'
$actualNames = @($allItems | Where-Object { -not $_.PSIsContainer } | ForEach-Object { [System.IO.Path]::GetRelativePath($PacketRoot, $_.FullName).Replace('\', '/') } | Sort-Object)
$expectedNames = @(@($entries.Keys) + 'SHA256SUMS.txt' | Sort-Object)
Assert-Condition (@(Compare-Object -ReferenceObject $expectedNames -DifferenceObject $actualNames -CaseSensitive).Count -eq 0) 'Unexpected or missing packet files'
$sourceFiles.Add([ordered]@{ path = 'SHA256SUMS.txt'; bytes = $manifestBytes.Length; sha256 = $manifestSha; supplied_sha256 = $expectedManifest; verified = $true })

$records = @{ K = Read-Json 'K/measurement.json'; R = Read-Json 'R/measurement.json' }
$equivalence = Read-Json 'equivalence.json'
$cases = @(@(0,0), @(1,0), @(1,2), @(10,1), @(40,1), @(40,20), @(501,0))
$baseShapes = @(
    "SELECT sessions.token_hash, sessions.player_id, sessions.expires_at `nFROM sessions `nWHERE sessions.token_hash = %(pk_1)s::VARCHAR",
    "SELECT players.id, players.username, players.display_name, players.password_hash, players.credits, players.xp, players.active, players.last_trade `nFROM players `nWHERE players.id = %(pk_1)s::VARCHAR",
    "SELECT trades.id, trades.a, trades.b, trades.revision, trades.offers, trades.confirmations, trades.state `nFROM trades `nWHERE trades.a = %(a_1)s::VARCHAR OR trades.b = %(b_1)s::VARCHAR"
)
$itemPkSql = "SELECT items.id, items.owner_id, items.definition_id, items.rarity, items.pattern_seed, items.wear, items.variant, items.reservation, items.consumed, items.acquired_at `nFROM items `nWHERE items.id = %(pk_1)s::VARCHAR"
$environmentK = $records.K.environment | ConvertTo-Json -Depth 10 -Compress
$environmentR = $records.R.environment | ConvertTo-Json -Depth 10 -Compress
Assert-Condition ($environmentK -ceq $environmentR) 'Environment records differ'
Assert-Condition ($equivalence.schema -ceq 'anonymous-trade-read-equivalence-v1' -and $equivalence.rows.Count -eq 7) 'Equivalence schema or row count differs'
$assessments = [System.Collections.Generic.List[object]]::new()
$pairAssessments = [System.Collections.Generic.List[object]]::new()
$totalStatements = @{ K = 0L; R = 0L }
$totalSamples = 0
$totalShapes = 0
foreach ($label in @('K', 'R')) {
    $record = $records[$label]
    Assert-Condition ($record.schema -ceq 'anonymous-trade-read-measurement-v1' -and $record.variant -ceq $label) "Record identity/schema mismatch: $label"
    Assert-Condition ($record.completed -ceq $true -and $record.database_dropped -ceq $true) "Completion flags not true: $label"
    Assert-Condition ($null -eq $record.authoritative_state_hashes.before -and $null -eq $record.authoritative_state_hashes.after -and $record.authoritative_state_hashes.status -ceq 'not_retained') "Unexpected state hash metadata: $label"
    Assert-Condition ($record.rows.Count -eq 7) "Workload count differs: $label"
    for ($i = 0; $i -lt $cases.Count; $i++) {
        $row = $record.rows[$i]
        $sourceRef = "$label/measurement.json#/rows/$i"
        Assert-Condition ($row.trades -eq $cases[$i][0] -and $row.items_per_side -eq $cases[$i][1]) "Workload order differs: $sourceRef"
        Assert-Condition ($row.samples.Count -eq 10) "Wrong sample count: $sourceRef"
        $uniqueItems = [int](2 * $row.trades * $row.items_per_side)
        $uniqueParticipants = if ($row.trades -gt 0) { [int]($row.trades + 1) } else { 0 }
        $itemChunks = @(Get-Chunks $uniqueItems)
        $participantChunks = @(Get-Chunks $uniqueParticipants)
        $budget = 3 + $itemChunks.Count + $participantChunks.Count
        Assert-Condition ($row.budget -eq $budget) "Budget mismatch: $sourceRef"
        $expectedObservedCount = if ($label -ceq 'K') { $budget } else { 3 + $row.trades + $uniqueItems }
        $sampleChecks = [System.Collections.Generic.List[object]]::new()
        for ($j = 0; $j -lt 10; $j++) {
            $sample = $row.samples[$j]
            $sampleRef = "$sourceRef/samples/$j"
            Assert-Condition ($sample.milliseconds -is [double] -or $sample.milliseconds -is [long]) "Non-numeric timing: $sampleRef"
            Assert-Condition ([double]::IsFinite([double]$sample.milliseconds) -and $sample.milliseconds -ge 0) "Invalid timing: $sampleRef"
            Assert-Condition (($sample.statements -is [long]) -and $sample.statements -gt 0) "Invalid statement count: $sampleRef"
            Assert-Condition ($sample.statements -eq $expectedObservedCount) "Statement model disagreement: $sampleRef"
            $sampleChecks.Add([ordered]@{ sample_index_0based = $j; source_reference = $sampleRef; milliseconds = $sample.milliseconds; statements = $sample.statements; valid = $true })
            $totalStatements[$label] += $sample.statements
            $totalSamples++
        }
        $sortedSamples = @($sampleChecks | Sort-Object -Property { [double]$_.milliseconds })
        $independentlySortedTimes = @($row.samples | ForEach-Object { [double]$_.milliseconds } | Sort-Object)
        for ($j = 0; $j -lt 10; $j++) {
            Assert-Condition ($sortedSamples[$j].milliseconds -eq $independentlySortedTimes[$j]) "Independent sorted-duration check differs: $sourceRef/$j"
        }
        $median = ([double]$sortedSamples[4].milliseconds + [double]$sortedSamples[5].milliseconds) / 2
        $decimalMedian = ([decimal]$sortedSamples[4].milliseconds + [decimal]$sortedSamples[5].milliseconds) / 2
        $p95Rank = [int][math]::Ceiling(10 * .95)
        $p95 = [double]$sortedSamples[$p95Rank - 1].milliseconds
        $counts = @($row.samples.statements | Sort-Object -Unique)
        $medianError = [math]::Abs($row.median_ms - $median)
        Assert-Condition ($medianError -le (1e-12 * [math]::Max([math]::Abs($median), 1))) "Median mismatch: $sourceRef"
        Assert-Condition ($row.p95_ms -eq $p95) "P95 mismatch: $sourceRef"
        Assert-Condition (@(Compare-Object -ReferenceObject $counts -DifferenceObject @($row.query_counts) -CaseSensitive).Count -eq 0) "Query count set mismatch: $sourceRef"
        Assert-Condition ($row.read_only -ceq $true) "Read-only assertion not true: $sourceRef"
        Assert-Condition ($row.response_sha256 -cmatch '^[0-9a-f]{64}$') "Invalid expected response digest: $sourceRef"
        $expectedShapes = [System.Collections.Generic.List[string]]::new()
        foreach ($sql in $baseShapes) { $expectedShapes.Add($sql) }
        if ($label -ceq 'K') {
            foreach ($chunk in @($itemChunks | Select-Object -Unique)) { $expectedShapes.Add((New-InSql 'items' $chunk)) }
            foreach ($chunk in @($participantChunks | Select-Object -Unique)) { $expectedShapes.Add((New-InSql 'players' $chunk)) }
        } elseif ($uniqueItems -gt 0) { $expectedShapes.Add($itemPkSql) }
        Assert-Condition ($row.sql_shapes.Count -eq $expectedShapes.Count) "Shape count disagreement: $sourceRef"
        $seenSql = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
        $shapeChecks = [System.Collections.Generic.List[object]]::new()
        for ($j = 0; $j -lt $row.sql_shapes.Count; $j++) {
            $sql = [string]$row.sql_shapes[$j]
            $shapeRef = "$sourceRef/sql_shapes/$j"
            Assert-Condition ($sql -ceq $expectedShapes[$j]) "Unexpected SQL text: $shapeRef"
            Assert-Condition ($seenSql.Add($sql)) "Duplicate deduplicated SQL shape: $shapeRef"
            Assert-Condition ($sql.TrimStart().StartsWith('SELECT', [System.StringComparison]::Ordinal)) "Non-SELECT shape: $shapeRef"
            $table = [regex]::Match($sql, '(?m)^FROM (\w+)').Groups[1].Value
            $parameters = @([regex]::Matches($sql, '%\(([^)]+)\)s') | ForEach-Object { $_.Groups[1].Value })
            $kind = if ($sql.Contains(' IN (')) { 'batched_id_in' } elseif ($table -ceq 'trades') { 'participant_or' } elseif ($table -ceq 'sessions') { 'session_token_hash' } else { 'id_primary_key' }
            $sqlBytes = $utf8.GetBytes($sql)
            $shapeChecks.Add([ordered]@{
                shape_index_0based = $j; source_reference = $shapeRef; table = $table; kind = $kind
                utf8_sha256 = (Get-Sha256 $sqlBytes); utf8_bytes = $sqlBytes.Length
                placeholder_count = $parameters.Count; first_placeholder = $parameters[0]; last_placeholder = $parameters[-1]
                select_only = $true; exact_expected_sql_text_match = $true; placeholder_sequence_checked_by_exact_template = $true
                narrow_participant_projection = ($table -ceq 'players' -and $kind -ceq 'batched_id_in')
            })
            $totalShapes++
        }
        $findings = if ($label -ceq 'K') {
            if ($row.trades -eq 0) { @('Empty history: no item/participant enrichment queries.') }
            elseif ($uniqueItems -eq 1600) { @('Eight executed statements, six deduplicated shapes; expected item batches 500/500/500/100 are consistent with the 500/100 unique shapes, not an independently retained multiplicity trace.') }
            elseif ($uniqueParticipants -eq 502) { @('Two distinct participant IN shapes contain 500 and 2 placeholders; five executed statements support participant chunking across 500.') }
            else { @('Recorded count equals recomputed common batch budget.') }
        } else { @('Recorded counts fit 3 + trades + unique offered items; repeated per-table multiplicities are inferred, not retained as traces.') }
        $assessments.Add([ordered]@{
            label = $label; row_index_0based = $i; source_reference = $sourceRef
            trades = $row.trades; items_per_side = $row.items_per_side
            unique_offered_items_from_method = $uniqueItems; unique_participants_from_method = $uniqueParticipants
            sample_count = $row.samples.Count; samples = @($sampleChecks.ToArray())
            sorted_duration_samples = @($sortedSamples | ForEach-Object { [ordered]@{ sample_index_0based = $_.sample_index_0based; milliseconds = $_.milliseconds } })
            recorded_median_ms = $row.median_ms; recomputed_median_ms = $median; decimal_median_ms = $decimalMedian
            median_middle_samples_0based = @($sortedSamples[4].sample_index_0based, $sortedSamples[5].sample_index_0based)
            median_absolute_error_ms = $medianError; median_agrees = $true
            recorded_p95_ms = $row.p95_ms; recomputed_nearest_rank_p95_ms = $p95; p95_rank_1based = $p95Rank
            p95_sample_index_0based = $sortedSamples[$p95Rank - 1].sample_index_0based; p95_agrees = $true
            recomputed_query_count_set = $counts; query_counts_agree = $true; all_ten_statement_counts_identical = ($counts.Count -eq 1)
            recorded_budget = $row.budget; recomputed_budget = $budget; meets_recorded_budget = ($counts[-1] -le $budget)
            expected_count_model = $(if ($label -ceq 'K') { '3 + ceil(unique_items/500) + ceil(unique_participants/500)' } else { '3 + trades + unique_items (observational fit, not source proof)' })
            count_model_agrees_all_samples = $true
            item_batch_sizes_implied_by_method_and_count_model = $(if ($label -ceq 'K') { @($itemChunks) } else { $null })
            participant_batch_sizes_implied_by_method_and_count_model = $(if ($label -ceq 'K') { @($participantChunks) } else { $null })
            unique_sql_shape_count_last_timed_request_only = $row.sql_shapes.Count; last_timed_request_statement_count = $row.samples[9].statements
            sql_shapes = @($shapeChecks.ToArray()); sql_shapes_consistent = $true; full_execution_trace_and_bound_parameters_retained = $false
            expected_response_sha256 = $row.response_sha256; response_digest_kind = 'expected_fixture_not_actual_response'
            actual_response_bodies_or_digests_retained = $false; recorded_snapshot_equality = $row.read_only
            authoritative_state_before_sha256 = $null; authoritative_state_after_sha256 = $null
            independent_authoritative_state_hash_verification = 'NEEDS MORE EVIDENCE'
            record_arithmetic_integrity = 'PASS'; findings = $findings
        })
    }
}

for ($i = 0; $i -lt 7; $i++) {
    $k, $r, $pair = $records.K.rows[$i], $records.R.rows[$i], $equivalence.rows[$i]
    $kCount, $rCount = [int]$k.query_counts[0], [int]$r.query_counts[0]
    Assert-Condition ($pair.trades -eq $k.trades -and $pair.items_per_side -eq $k.items_per_side) "Equivalence coordinates differ: $i"
    Assert-Condition ($pair.expected_response_sha256.K -ceq $k.response_sha256 -and $pair.expected_response_sha256.R -ceq $r.response_sha256) "Equivalence digest references differ: $i"
    Assert-Condition ($k.response_sha256 -ceq $r.response_sha256 -and $pair.expected_response_fingerprints_equal -ceq $true) "Expected fixture digests differ: $i"
    Assert-Condition ($pair.recorded_snapshot_equality.K -ceq $k.read_only -and $pair.recorded_snapshot_equality.R -ceq $r.read_only) "Snapshot flags differ: $i"
    Assert-Condition ($pair.state_hash_equivalence -ceq 'not_evaluable_not_retained') "Misstated state hash equivalence: $i"
    Assert-Condition ($kCount -le $rCount) "K count regression: $i"
    $pairAssessments.Add([ordered]@{
        row_index_0based = $i; trades = $k.trades; items_per_side = $k.items_per_side
        K_reference = "K/measurement.json#/rows/$i"; R_reference = "R/measurement.json#/rows/$i"; equivalence_reference = "equivalence.json#/rows/$i"
        K_statements_every_timed_request = $kCount; R_statements_every_timed_request = $rCount
        statements_saved_per_request_K_vs_R = ($rCount - $kCount); percent_fewer_statements_K_vs_R = (100.0 * ($rCount - $kCount) / $rCount)
        count_winner = $(if ($kCount -lt $rCount) { 'K' } else { 'TIE' })
        K_meets_budget = ($kCount -le $k.budget); R_meets_budget = ($rCount -le $r.budget)
        K_median_ms = $k.median_ms; R_median_ms = $r.median_ms
        observed_R_to_K_median_ratio_not_causal_speedup = ($r.median_ms / $k.median_ms)
        K_p95_observed_max_ms = $k.p95_ms; R_p95_observed_max_ms = $r.p95_ms
        K_timed_range_ms = @(@($k.samples.milliseconds | Sort-Object)[0], @($k.samples.milliseconds | Sort-Object)[-1])
        R_timed_range_ms = @(@($r.samples.milliseconds | Sort-Object)[0], @($r.samples.milliseconds | Sort-Object)[-1])
        expected_response_sha256_equal = $true; expected_response_sha256 = $k.response_sha256
        recorded_success_assertions = 'Method reports status 200 and complete canonical equality on each warm-up and timed request; no actual bodies or per-response digests retained.'
        recorded_authoritative_snapshot_equality = @{ K = $true; R = $true }
        independent_state_hash_equivalence = 'NOT EVALUABLE: both null/not_retained, never equality evidence'
    })
}
Assert-Condition ($totalSamples -eq 140 -and $assessments.Count -eq 14) 'Overall retained workload/sample totals differ'
$now = [datetime]::UtcNow.ToString('o')
$sourceHashes = [ordered]@{
    schema = 'neutral-blind-input-source-hashes-v1'; audited_utc = $now; packet_root = $PacketRoot
    expected_manifest_sha256 = $expectedManifest; actual_manifest_sha256 = $manifestSha; supplied_anchor_matches = $true
    packet_file_count_including_manifest = $actualNames.Count; manifest_covered_payload_files = $entries.Count
    all_packet_hashes_verified = $true; unexpected_or_missing_packet_files = @(); duplicate_manifest_entries = @(); packet_reparse_points = @()
    packet_source_files = @($sourceFiles.ToArray())
    original_implementation_source_hashes = @{ K = $null; R = $null; status = 'WITHHELD_NOT_INSPECTED; source binding intentionally deferred until after frozen verdict' }
    original_measurement_routine_and_fixture_hashes = @{ hashes = $null; status = 'WITHHELD_NOT_IN_PACKET; controller equality assertion not independently verified' }
    commit_tree_branch_database_mapping_and_original_timestamps = 'WITHHELD_NOT_INSPECTED'
    meaning_of_source_hashes = 'Exact bytes of the permitted packet inputs only, not original implementation provenance or an endorsement of measurement authenticity.'
}
$output = [ordered]@{
    schema = 'neutral-blind-trade-read-assessment-v1'; assessed_utc = $now; packet_manifest_sha256 = $manifestSha
    reviewer_mode = 'Independent fresh-context blind critic; anonymous labels only; no identity inference attempted'
    audit_execution = 'PowerShell/.NET retained-file arithmetic only; no Python, application, native tests, bulk tests, database, network, repository, or identity key accessed'
    powershell_version = $PSVersionTable.PSVersion.ToString(); environment_records_identical = $true; recorded_measurement_environment = $records.K.environment
    totals = [ordered]@{
        anonymous_variants = 2; workload_pairs = 7; workload_records = $assessments.Count; retained_timed_samples = $totalSamples
        warmups_per_workload_stated_not_raw_retained = 2; total_stated_warmups = 28
        K_timed_statement_callbacks = $totalStatements.K; R_timed_statement_callbacks = $totalStatements.R
        all_timed_statement_callbacks = ($totalStatements.K + $totalStatements.R)
        K_fewer_statement_pairs = @($pairAssessments | Where-Object { $_.count_winner -ceq 'K' }).Count
        tied_statement_pairs = @($pairAssessments | Where-Object { $_.count_winner -ceq 'TIE' }).Count
        K_count_regressions = 0; sql_shape_entries_across_records = $totalShapes
        all_14_medians_p95s_query_sets_budgets_recomputed = $true; all_140_samples_checked = $true
        all_7_expected_fixture_digest_pairs_match = $true; all_14_recorded_snapshot_equalities_true = $true
        independent_actual_response_hashes_verified = $false; independent_state_hashes_verified = $false
    }
    decision = [ordered]@{
        narrow_verdict = 'ACCEPT WITH QUALIFICATIONS'; preferred_label = 'K'; confidence = 'HIGH for retained statement counts; conditional for recorded successful equivalence/state assertions'
        scope = 'Successful deterministic GET /trades fixtures in this retained packet only; materially fewer executed SQL callbacks without measured count regression'
        full_semantic_and_authoritative_safety_bar_independently_established = $false
        neither_label_receives_broad_acceptance = $true
        statuses = [ordered]@{
            packet_integrity = 'PASS'; measured_query_efficiency_K = 'PASS'; measured_query_efficiency_R = 'FAIL'
            latency_generalization = 'NEEDS MORE EVIDENCE'
            response_equivalence_evidence = 'PASS'
            independently_auditable_state_preservation = 'NEEDS MORE EVIDENCE'
            source_monetary_contract_safety = 'NOT EVALUATED'
        }
        response_equivalence_PASS_qualification = 'Matching expected digests and reported complete assertions only; independently auditable actual-response equivalence still NEEDS MORE EVIDENCE.'
        broad_gates = [ordered]@{ human = 'UNVERIFIED'; device = 'UNVERIFIED'; '8.5' = 'UNVERIFIED'; production = 'UNVERIFIED'; concurrent_load = 'UNVERIFIED'; unbounded_history = 'UNVERIFIED' }
    }
    pairs = @($pairAssessments.ToArray()); workloads = @($assessments.ToArray())
    blind_limitations = @(
        'Hash integrity is anchored to the supplied manifest, not independently authenticated execution or source provenance.',
        'Measurement routine and fixture source/fingerprints are withheld; methodology assertions cannot be re-run or source-audited here.',
        'No actual response bodies/digests, expected bodies, authoritative snapshots, state digests, bound parameters, or complete SQL traces are retained.',
        'Canonicalization removes top-level trade-list order differences; nested offer/confirmation order is stated to remain significant.',
        'Ten sequential warm samples per workload, non-interleaved runs, uncontrolled host load; no causal throughput or production-tail conclusions.',
        'Only the declared seven synthetic workload pairs are assessable; absence of earlier failures/dropped original runs is not provable.',
        'No failure/adversarial/concurrent/monetary/source tests; no human/device/8.5/production/unbounded-history acceptance.'
    )
}
Write-Json 'source_hashes.json' $sourceHashes
Write-Json 'per_workload_assessment.json' $output
[ordered]@{
    audited_utc = $now; packet_hashes_pass = $true; workload_records = $assessments.Count; timed_samples = $totalSamples
    K_timed_statements = $totalStatements.K; R_timed_statements = $totalStatements.R; unique_shape_entries_checked = $totalShapes
    all_arithmetic_pass = $true; all_exact_sql_templates_pass = $true
    pair_assessments = @($pairAssessments.ToArray())
    written = @('source_hashes.json', 'per_workload_assessment.json')
} | ConvertTo-Json -Depth 12
