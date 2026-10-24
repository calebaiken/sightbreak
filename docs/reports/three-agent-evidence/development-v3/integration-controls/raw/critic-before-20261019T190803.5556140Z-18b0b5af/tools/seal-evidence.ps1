param([Parameter(Mandatory = $true)][string]$EvidenceRoot)

# Hash saved evidence only. Does not execute archived commands or access live source.
$ErrorActionPreference = 'Stop'
$EvidenceRoot = [System.IO.Path]::GetFullPath($EvidenceRoot)
$destination = Join-Path $EvidenceRoot 'SHA256SUMS.txt'
if (Test-Path -LiteralPath $destination) { throw 'Refusing to replace an existing integrity manifest.' }
$files = @(Get-ChildItem -LiteralPath $EvidenceRoot -File -Recurse -Force | Sort-Object FullName)
$records = foreach ($file in $files) {
    [pscustomobject]@{
        path = $file.FullName
        relative = [System.IO.Path]::GetRelativePath($EvidenceRoot, $file.FullName).Replace('\', '/')
        sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}
$text = (($records | ForEach-Object { "$($_.sha256)  $($_.relative)" }) -join "`n") + "`n"
$bytes = [System.Text.UTF8Encoding]::new($false).GetBytes($text)
$stream = [System.IO.FileStream]::new($destination, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write)
try { $stream.Write($bytes, 0, $bytes.Length) } finally { $stream.Dispose() }
foreach ($record in $records) {
    $actual = (Get-FileHash -LiteralPath $record.path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $record.sha256) { throw "Evidence changed during sealing: $($record.relative)" }
}
Write-Output "EVIDENCE_FILES_HASHED_AND_RECHECKED=$($records.Count)"
Write-Output "INTEGRITY_MANIFEST=$destination"
Write-Output "INTEGRITY_MANIFEST_SHA256=$((Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant())"
