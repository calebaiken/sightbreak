param([Parameter(Mandatory)][ValidateSet('north','south')][string]$Label)
. "$PSScriptRoot\Invoke-Recorded.ps1"
$script:EvidenceRoot = Join-Path $PSScriptRoot "runtime-$Label"
[IO.Directory]::CreateDirectory($script:EvidenceRoot) | Out-Null
$godot = 'C:\Users\blith\AppData\Local\Temp\opencode\godot\Godot_v4.7.2-stable_win64.exe'
$trees = Get-Content "$PSScriptRoot\neutral-worktrees.json" -Raw | ConvertFrom-Json
$tree = $trees | Where-Object label -eq $Label
foreach ($name in @('north','south')) {
    $import = Get-Content "$PSScriptRoot\logs\$name-import.stdout.log" -Raw
    $err = Get-Content "$PSScriptRoot\logs\$name-import.stderr.log" -Raw
    if ($import -match '(?im)SCRIPT ERROR:|ERROR:' -or $err -match '(?im)SCRIPT ERROR:|ERROR:') {
        throw "Import for $name contains errors: inspect before running probes."
    }
}
$entries = Get-Content "$PSScriptRoot\commands.jsonl" | ForEach-Object { $_ | ConvertFrom-Json }
foreach ($name in @('north-import','south-import')) {
    $entry = $entries | Where-Object name -eq $name | Select-Object -Last 1
    if ($entry.exit_code -ne 0 -or $entry.timed_out) { throw "Import $name did not finish cleanly." }
}
foreach ($probe in @('module_probe','authority_contract_probe','integration_controls','objective_controls','native_comparison_extended')) {
    $args = @('--headless','--path',"$($tree.path)\game",'--fixed-fps','60','--script',"$PSScriptRoot\retained-v2\$probe.gd")
    $result = Invoke-Recorded -Name $probe -Executable $godot -Arguments $args -WorkingDirectory $tree.path -TimeoutSeconds 600 -AllowFailure
    Write-Output "$Label $probe exit=$($result.exit_code) timeout=$($result.timed_out)"
}
Write-Output "$Label retained native runs finished."
