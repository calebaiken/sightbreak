$ErrorActionPreference = 'Stop'
$Repo = 'C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3'
$Root = $PSScriptRoot
$Revisions = [ordered]@{
    candidate = '4a8e9ea73aa8b286d9f1751b0a6b485479737294'
    pr16 = 'd2439acdd5f73df7bae5ada62ee1e3dec2cf30db'
    v2 = '701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd'
}
$Utf8 = [Text.UTF8Encoding]::new($false)
$Commands = [Collections.Generic.List[object]]::new()

function Get-Sha256([byte[]] $Bytes) {
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($Bytes)).ToLowerInvariant()
}

function Invoke-GitRead([string[]] $GitArguments) {
    $Info = [Diagnostics.ProcessStartInfo]::new()
    $Info.FileName = 'git'
    $Info.WorkingDirectory = $Repo
    $Info.UseShellExecute = $false
    $Info.RedirectStandardOutput = $true
    $Info.RedirectStandardError = $true
    $Info.Environment['GIT_OPTIONAL_LOCKS'] = '0'
    $Info.ArgumentList.Add('--no-pager')
    foreach ($Argument in $GitArguments) { $Info.ArgumentList.Add($Argument) }
    $Process = [Diagnostics.Process]::new()
    $Process.StartInfo = $Info
    [void] $Process.Start()
    $Buffer = [IO.MemoryStream]::new()
    $Process.StandardOutput.BaseStream.CopyTo($Buffer)
    $Stderr = $Process.StandardError.ReadToEnd()
    $Process.WaitForExit()
    $Bytes = $Buffer.ToArray()
    $Commands.Add([ordered]@{
        utc = [DateTime]::UtcNow.ToString('o')
        argv = @('git', '--no-pager') + $GitArguments
        cwd = $Repo
        returncode = $Process.ExitCode
        stdout_sha256 = Get-Sha256 $Bytes
        stdout_bytes = $Bytes.Length
        stderr = $Stderr
    })
    if ($Process.ExitCode -ne 0) { throw "Git failed: $GitArguments / $Stderr" }
    $Process.Dispose()
    $Buffer.Dispose()
    return ,$Bytes
}

function Write-NewBytes([string] $Name, [byte[]] $Bytes) {
    $Handle = [IO.File]::Open((Join-Path $Root $Name), [IO.FileMode]::CreateNew)
    try { $Handle.Write($Bytes) } finally { $Handle.Dispose() }
}

function Write-NewText([string] $Name, [string] $Text) {
    Write-NewBytes $Name ($Utf8.GetBytes($Text))
}

function Select-Definitions([string] $Source, [string[]] $Names, [bool] $Numbered = $true) {
    $Lines = $Source.Replace("`r`n", "`n").Split("`n")
    $Output = [Collections.Generic.List[string]]::new()
    for ($Index = 0; $Index -lt $Lines.Length; $Index++) {
        if ($Lines[$Index] -match '^(?:def|class) ([A-Za-z_][A-Za-z0-9_]*)\b' -and $Matches[1] -cin $Names) {
            $Start = $Index
            while ($Start -gt 0 -and $Lines[$Start - 1].StartsWith('@')) { $Start-- }
            $End = $Index + 1
            while ($End -lt $Lines.Length -and ($Lines[$End] -match '^\s' -or $Lines[$End] -eq '' -or $Lines[$End].StartsWith('#'))) { $End++ }
            for ($Line = $Start; $Line -lt $End; $Line++) {
                $Output.Add($(if ($Numbered) { '{0}: {1}' -f ($Line + 1), $Lines[$Line] } else { $Lines[$Line] }))
            }
        }
    }
    return ($Output -join "`n") + "`n"
}

$Manifest = [ordered]@{ repository = $Repo; collector = 'PowerShell source extraction only; no application/fixture execution'; revisions = [ordered]@{} }
$ContractNames = @('transaction', 'authenticated', 'item_json', 'owned', 'get_trade', 'new_trade', 'offer', 'confirm', 'cancel_trade', 'market_buy', 'replay', 'MarketBuy')
foreach ($Pair in $Revisions.GetEnumerator()) {
    $Label = $Pair.Key
    $Revision = $Pair.Value
    $Commit = $Utf8.GetString((Invoke-GitRead @('show', '-s', '--format=%H%n%P%n%s', $Revision)))
    $Raw = Invoke-GitRead @('show', "${Revision}:backend/app.py")
    $Source = $Utf8.GetString($Raw)
    $Slice = Select-Definitions $Source @('trade_json', 'trades')
    Write-NewText "$Label-app-trade-slice.txt" $Slice
    $Contracts = [ordered]@{}
    foreach ($Name in $ContractNames) {
        $Body = Select-Definitions $Source @($Name) $false
        $Contracts[$Name] = Get-Sha256 ($Utf8.GetBytes($Body))
    }
    $Manifest.revisions[$Label] = [ordered]@{
        revision = $Revision
        commit = $Commit
        app_blob = $Utf8.GetString((Invoke-GitRead @('rev-parse', "${Revision}:backend/app.py"))).Trim()
        app_sha256 = Get-Sha256 $Raw
        trade_slice_sha256 = Get-Sha256 ($Utf8.GetBytes($Slice))
        model_blob = $Utf8.GetString((Invoke-GitRead @('rev-parse', "${Revision}:backend/models.py"))).Trim()
        contract_definition_sha256 = $Contracts
    }
    if ($Label -eq 'candidate') {
        Write-NewText 'candidate-app-contract-context.txt' (Select-Definitions $Source $ContractNames)
    }
}
$AuthorizedPaths = @('backend/app.py', 'backend/tests/test_trade_reads.py', 'scripts/benchmark_trade_reads.py')
$Diff = Invoke-GitRead (@('diff', '--no-ext-diff', '--no-textconv', '--no-renames', '--unified=3', $Revisions.pr16, $Revisions.candidate, '--') + $AuthorizedPaths)
Write-NewBytes 'pr16-to-candidate-authorized.diff' $Diff
$Manifest.authorized_diff_sha256 = Get-Sha256 $Diff
foreach ($Item in @(
    @{ Path = 'backend/tests/test_trade_reads.py'; Name = 'candidate-test_trade_reads.py.txt' },
    @{ Path = 'scripts/benchmark_trade_reads.py'; Name = 'candidate-benchmark_trade_reads.py.txt' }
)) {
    $Raw = Invoke-GitRead @('show', "$($Revisions.candidate):$($Item.Path)")
    $Lines = $Utf8.GetString($Raw).TrimEnd("`n").Split("`n")
    $Numbered = for ($Index = 0; $Index -lt $Lines.Length; $Index++) { '{0}: {1}' -f ($Index + 1), $Lines[$Index] }
    Write-NewText $Item.Name (($Numbered -join "`n") + "`n")
    $Manifest[$Item.Path] = [ordered]@{
        blob = $Utf8.GetString((Invoke-GitRead @('rev-parse', "$($Revisions.candidate):$($Item.Path)"))).Trim()
        sha256 = Get-Sha256 $Raw
    }
}
$ModelRaw = Invoke-GitRead @('show', "$($Revisions.candidate):backend/models.py")
Write-NewText 'candidate-model-contract-context.txt' (Select-Definitions ($Utf8.GetString($ModelRaw)) @('Player', 'Session', 'Item', 'Trade'))
Write-NewText 'manifest.json' (($Manifest | ConvertTo-Json -Depth 20) + "`n")
Write-NewText 'git-commands.json' (($Commands | ConvertTo-Json -Depth 10) + "`n")
$Manifest | ConvertTo-Json -Depth 20
