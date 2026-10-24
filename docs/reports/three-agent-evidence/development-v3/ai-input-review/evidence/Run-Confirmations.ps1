param([Parameter(Mandatory)][ValidateSet('north','south')][string]$Label)
& "$PSScriptRoot\Run-Probe.ps1" -Label $Label -Probe native_behavior_probe.gd -Run r2 -Seconds 300
& "$PSScriptRoot\Run-Probe.ps1" -Label $Label -Probe native_policy_probe.gd -Run r1
& "$PSScriptRoot\Run-Probe.ps1" -Label $Label -Probe native_contract_probe.gd -Run r2
& "$PSScriptRoot\Run-Probe.ps1" -Label $Label -Probe native_equipment_contract.gd -Run r2
