param(
    [Parameter(Mandatory)][ValidateSet('north','south')][string]$Label,
    [Parameter(Mandatory)][string]$Probe,
    [string]$Run = 'r1',
    [int]$Seconds = 240
)
. "$PSScriptRoot\Invoke-Recorded.ps1"
$script:EvidenceRoot = Join-Path $PSScriptRoot "extra-$Label"
[IO.Directory]::CreateDirectory($script:EvidenceRoot) | Out-Null
$godot = 'C:\Users\blith\AppData\Local\Temp\opencode\godot\Godot_v4.7.2-stable_win64.exe'
$tree = "C:\Users\blith\AppData\Local\Temp\opencode\sol-ai-$Label-20261019"
$probePath = if ($Probe.StartsWith('res://')) { $Probe } else { Join-Path $PSScriptRoot $Probe }
$name = [IO.Path]::GetFileNameWithoutExtension($Probe) + '-' + $Run
Invoke-Recorded -Name $name -Executable $godot -Arguments @('--headless','--path',"$tree\game",'--fixed-fps','60','--script',$probePath) -WorkingDirectory $tree -TimeoutSeconds $Seconds -AllowFailure | Select-Object name,exit_code,timed_out
