Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
function Read-Records([string]$Path, [string]$Prefix) {
    foreach ($line in Get-Content $Path) {
        if ($line.StartsWith($Prefix + ' {')) {
            $line.Substring($Prefix.Length + 1) | ConvertFrom-Json
        }
    }
}
$results = [ordered]@{}
foreach ($label in @('north','south')) {
    $data = @(Read-Records "$PSScriptRoot\extra-$label\logs\native_behavior_probe-r1.stdout.log" 'NATIVE_BEHAVIOR')
    $contract = @(Read-Records "$PSScriptRoot\extra-$label\logs\native_contract_probe-r1.stdout.log" 'NATIVE_CONTRACT')
    $equipment = @(Read-Records "$PSScriptRoot\extra-$label\logs\native_equipment_contract-r1.stdout.log" 'NATIVE_EQUIPMENT')
    $policy = @(Read-Records "$PSScriptRoot\extra-$label\logs\native_policy_probe-r1.stdout.log" 'NATIVE_POLICY')
    $elimination = @(Read-Records "$PSScriptRoot\extra-$label\logs\native_elimination_contract-r1.stdout.log" 'NATIVE_ELIMINATION')
    $anchors = @($data | Where-Object case -eq 'anchor_arrival')
    $precision = @($data | Where-Object case -eq 'sound_precision')
    $r1Hash = (Get-FileHash "$PSScriptRoot\extra-$label\logs\native_behavior_probe-r1.stdout.log").Hash
    $r2Hash = (Get-FileHash "$PSScriptRoot\extra-$label\logs\native_behavior_probe-r2.stdout.log").Hash
    $results[$label] = [ordered]@{
        behavior_repeat_byte_identical = $r1Hash -eq $r2Hash
        behavior_r1_stdout_sha256 = $r1Hash.ToLowerInvariant()
        behavior_r2_stdout_sha256 = $r2Hash.ToLowerInvariant()
        behavior_stderr_empty_both_runs = (Get-Item "$PSScriptRoot\extra-$label\logs\native_behavior_probe-r1.stderr.log").Length -eq 0 -and (Get-Item "$PSScriptRoot\extra-$label\logs\native_behavior_probe-r2.stderr.log").Length -eq 0
        policy_repeat_byte_identical = (Get-FileHash "$PSScriptRoot\extra-$label\logs\native_policy_probe-r1.stdout.log").Hash -eq (Get-FileHash "$PSScriptRoot\extra-$label\logs\native_policy_probe-r2.stdout.log").Hash
        adapted_anchor_arrival_count = @($anchors | Where-Object arrival_seconds -ge 0).Count
        adapted_anchor_total = $anchors.Count
        adapted_anchor_results = @($anchors | Select-Object slot,declared_anchor,arrival_seconds,minimum_distance_m,seconds_within_1_8m,final_position)
        adapted_easy_defender_hearing_20m = @($data | Where-Object { $_.case -eq 'hearing' -and $_.difficulty -eq 'easy' -and $_.team -eq 1 -and $_.scenario -eq 'easy_bypass20' })
        adapted_damage_priority = @($data | Where-Object case -eq 'damage_priority')
        sound_precision_samples = ($precision | Measure-Object samples -Sum).Sum
        sound_precision_exact_samples = ($precision | Measure-Object exact_count -Sum).Sum
        sound_precision = $precision
        original_actor_contract = $contract
        original_elimination_contract = $elimination
        real_equipment_contract = $equipment
        equipment_pass_count = @($equipment | Where-Object passed).Count
        adapted_invalid_equipment_choices = @($data | Where-Object { $_.case -eq 'equipment' -and -not $_.choice_valid })
        additional_policy_observations = $policy
    }
    $results[$label] | ConvertTo-Json -Depth 30 | Set-Content "$PSScriptRoot\summary-$label.json" -Encoding utf8
}
$retained = @(Read-Records "$PSScriptRoot\runtime-north\logs\native_comparison_extended.stdout.log" 'AI_NATIVE_COMPARISON')
$results['retained_baseline_sweep'] = [ordered]@{
    conditions = $retained.Count
    two_round_conditions_completed = @($retained | Where-Object completed).Count
    rounds = ($retained | ForEach-Object { $_.rounds.Count } | Measure-Object -Sum).Sum
    plants = ($retained | Measure-Object plants -Sum).Sum
    defuses = ($retained | Measure-Object defuses -Sum).Sum
    note = 'Candidate could not parse the same sweep; no candidate comparative performance or objective claim is valid.'
    records = $retained
}
$results['retained_recovered_file_count'] = @(Get-ChildItem "$PSScriptRoot\retained-v2" -File).Count
$results | ConvertTo-Json -Depth 40 | Set-Content "$PSScriptRoot\comparison-summary.json" -Encoding utf8
foreach ($label in @('north','south')) {
    $r = $results[$label]
    Write-Output "$label arrival=$($r.adapted_anchor_arrival_count)/$($r.adapted_anchor_total) exact_sound=$($r.sound_precision_exact_samples)/$($r.sound_precision_samples) equipment=$($r.equipment_pass_count)/5 behavior_repeat_identical=$($r.behavior_repeat_byte_identical)"
}
Write-Output "V2 retained sweep: $($results.retained_baseline_sweep.conditions) conditions, $($results.retained_baseline_sweep.rounds) rounds, $($results.retained_baseline_sweep.plants) plants, $($results.retained_baseline_sweep.defuses) defuses."
