param(
    [Parameter(Mandatory = $true)][string]$Repository,
    [Parameter(Mandatory = $true)][string]$EvidenceRoot
)

# Preservation only: exact immutable Git object reads, no current source-file reads,
# no tests, no Godot, no Git writes. All generated files live under EvidenceRoot.
$ErrorActionPreference = 'Stop'
$utf8 = [System.Text.UTF8Encoding]::new($false)
$EvidenceRoot = [System.IO.Path]::GetFullPath($EvidenceRoot)
$baselineRoot = Join-Path $EvidenceRoot 'sources/immutable-baseline'
$reconstructedRoot = Join-Path $EvidenceRoot 'sources/reconstructed-reviewed'
$objectLogRoot = Join-Path $EvidenceRoot 'sources/immutable-object-read-logs'
$reportPath = Join-Path $EvidenceRoot 'sources/source-evidence.json'

foreach ($path in @($baselineRoot, $reconstructedRoot, $objectLogRoot, $reportPath)) {
    if (Test-Path -LiteralPath $path) { throw "Refusing to overwrite prior preservation material: $path" }
}

function Write-NewUtf8([string]$Path, [string]$Text) {
    $bytes = $utf8.GetBytes($Text)
    $stream = [System.IO.FileStream]::new($Path, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write)
    try { $stream.Write($bytes, 0, $bytes.Length) } finally { $stream.Dispose() }
}

function Get-GitBlobId([string]$Path) {
    $bytes = [System.IO.File]::ReadAllBytes($Path)
    $header = [System.Text.Encoding]::ASCII.GetBytes("blob $($bytes.Length)`0")
    $hash = [System.Security.Cryptography.IncrementalHash]::CreateHash([System.Security.Cryptography.HashAlgorithmName]::SHA1)
    try {
        $hash.AppendData($header)
        $hash.AppendData($bytes)
        return [System.Convert]::ToHexString($hash.GetHashAndReset()).ToLowerInvariant()
    } finally { $hash.Dispose() }
}

function Invoke-GitCapture([string[]]$Arguments, [string]$WorkingDirectory, [string]$StdoutPath, [string]$StderrPath) {
    foreach ($path in @($StdoutPath, $StderrPath)) {
        if (Test-Path -LiteralPath $path) { throw "Refusing to overwrite a captured Git result: $path" }
    }
    $start = [System.Diagnostics.ProcessStartInfo]::new()
    $start.FileName = 'git'
    $start.WorkingDirectory = $WorkingDirectory
    $start.UseShellExecute = $false
    $start.RedirectStandardOutput = $true
    $start.RedirectStandardError = $true
    $start.Environment['GIT_NO_LAZY_FETCH'] = '1'
    foreach ($name in @('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR')) {
        [void]$start.Environment.Remove($name)
    }
    foreach ($argument in $Arguments) { [void]$start.ArgumentList.Add($argument) }
    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $start
    $stream = [System.IO.FileStream]::new($StdoutPath, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write)
    try {
        [void]$process.Start()
        $errorTask = $process.StandardError.ReadToEndAsync()
        $process.StandardOutput.BaseStream.CopyTo($stream)
        $process.WaitForExit()
        $errorText = $errorTask.GetAwaiter().GetResult()
        Write-NewUtf8 $StderrPath $errorText
        return [pscustomobject]@{ exit_code = $process.ExitCode; stderr = $errorText }
    } finally {
        $stream.Dispose()
        $process.Dispose()
    }
}

[void][System.IO.Directory]::CreateDirectory($baselineRoot)
[void][System.IO.Directory]::CreateDirectory($objectLogRoot)
$observed = Import-Csv -LiteralPath (Join-Path $EvidenceRoot 'sources/observed-index-blobs.tsv') -Delimiter "`t"
$baselineRecords = [System.Collections.Generic.List[object]]::new()
foreach ($item in $observed) {
    if ($item.git_blob_sha1 -notmatch '^[a-f0-9]{40}$') { throw "Invalid transcribed object ID: $($item.git_blob_sha1)" }
    $destination = Join-Path $baselineRoot $item.path
    [void][System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($destination))
    $stderrPath = Join-Path $objectLogRoot "$($item.git_blob_sha1).stderr.txt"
    $run = Invoke-GitCapture @('cat-file', 'blob', $item.git_blob_sha1) $Repository $destination $stderrPath
    $actualBlobId = Get-GitBlobId $destination
    $verified = $run.exit_code -eq 0 -and $actualBlobId -eq $item.git_blob_sha1
    $baselineRecords.Add([pscustomobject]@{
        path = $item.path
        observed_index_mode = $item.mode
        observed_index_git_blob_sha1 = $item.git_blob_sha1
        observed_id_provenance = 'Original review git ls-files -s tool output; not a current index read'
        recovery_method = 'git cat-file blob with exact observed immutable ID and lazy fetch disabled'
        recovery_git_exit_code = $run.exit_code
        recovered_blob_verified = $verified
        recovered_git_blob_sha1 = $actualBlobId
        recovered_blob_sha256 = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant()
        original_worktree_sha256 = $null
    })
    Write-Output "IMMUTABLE_BLOB $($item.path) verified=$verified observed=$($item.git_blob_sha1)"
}

$reconstructionStatus = 'not_attempted_missing_or_unverified_baseline'
$reconstructedRecords = [System.Collections.Generic.List[object]]::new()
if (@($baselineRecords | Where-Object { -not $_.recovered_blob_verified }).Count -eq 0) {
    [void][System.IO.Directory]::CreateDirectory($reconstructedRoot)
    foreach ($item in $observed) {
        $destination = Join-Path $reconstructedRoot $item.path
        [void][System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($destination))
        [System.IO.File]::Copy((Join-Path $baselineRoot $item.path), $destination, $false)
    }
    $patchPath = Join-Path $EvidenceRoot 'sources/observed-working-tree.diff'
    $apply = Invoke-GitCapture @('-c', 'core.autocrlf=false', 'apply', '--whitespace=nowarn', $patchPath) $reconstructedRoot (Join-Path $EvidenceRoot 'sources/reconstruction-git-apply.stdout.txt') (Join-Path $EvidenceRoot 'sources/reconstruction-git-apply.stderr.txt')
    if ($apply.exit_code -eq 0) {
        $newWorkflow = Join-Path $reconstructedRoot '.github/workflows/v3-development.yml'
        [System.IO.File]::Copy((Join-Path $EvidenceRoot 'sources/observed-new-v3-development.yml'), $newWorkflow, $false)
        $observedPrefixes = @{
            '.github/workflows/engineering.yml' = 'bfe82ec'
            'game/export_presets.cfg' = '468a8a1'
            'scripts/build_manifest.py' = 'b1a034a'
            'scripts/test_build_manifest.py' = 'dd87fd9'
            'scripts/verify_builds.py' = '273b6bb'
            'scripts/verify_integration_export.py' = '23d89d4'
            'scripts/verify_offline_export.py' = '988f962'
        }
        $reconstructionStatus = 'derived_git_normalized_source_reconstructed_no_controls_executed'
        foreach ($file in (Get-ChildItem -LiteralPath $reconstructedRoot -File -Recurse -Force | Sort-Object FullName)) {
            $relative = [System.IO.Path]::GetRelativePath($reconstructedRoot, $file.FullName).Replace('\', '/')
            $blobId = Get-GitBlobId $file.FullName
            $prefix = $observedPrefixes[$relative]
            $prefixMatches = if ($null -eq $prefix) { $null } else { $blobId.StartsWith($prefix) }
            $reconstructedRecords.Add([pscustomobject]@{
                path = $relative
                provenance = 'Derived from exact recovered baseline plus conversation-retained pre-fix diff, or retained new-workflow text'
                derived_git_blob_sha1 = $blobId
                derived_file_sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
                observed_diff_new_blob_prefix = $prefix
                observed_diff_new_blob_prefix_matches = $prefixMatches
                original_worktree_sha256 = $null
                original_worktree_byte_exact_capture = $false
            })
            Write-Output "DERIVED_SOURCE $relative blob=$blobId observed-prefix-match=$prefixMatches"
        }
    } else {
        $reconstructionStatus = 'git_apply_failed_original_retained_diff_and_baselines_preserved'
    }
}

$report = [ordered]@{
    preservation_time_utc = [DateTime]::UtcNow.ToString('o')
    original_execution_time_utc = $null
    original_reviewed_commit_not_collected = $true
    original_worktree_byte_hashes_not_collected = $true
    original_temporary_control_artifacts_unavailable = $true
    controls_rerun_during_preservation = $false
    active_worktree_source_files_read_during_preservation = $false
    baseline_recovery = @($baselineRecords.ToArray())
    reconstruction_status = $reconstructionStatus
    reconstruction_line_ending_caveat = 'Derived Git-normalized text is not a byte-exact capture of the original mixed/CRLF working tree. Hashes here describe saved baseline or derived bytes only.'
    reconstructed_sources = @($reconstructedRecords.ToArray())
}
Write-NewUtf8 $reportPath (($report | ConvertTo-Json -Depth 12) + "`n")
Write-Output "SOURCE_EVIDENCE_REPORT $reportPath"
Write-Output "RECONSTRUCTION_STATUS $reconstructionStatus"
if (@($baselineRecords | Where-Object { -not $_.recovered_blob_verified }).Count -ne 0) {
    throw 'Some immutable baseline recovery failed; partial evidence and status were retained without replacement.'
}
if ($reconstructionStatus -ne 'derived_git_normalized_source_reconstructed_no_controls_executed') {
    throw 'Reconstruction did not succeed; original retained diff and immutable baseline evidence remain available.'
}
if (@($reconstructedRecords | Where-Object { $_.observed_diff_new_blob_prefix_matches -eq $false }).Count -ne 0) {
    throw 'A reconstructed blob disagrees with the originally observed diff prefix; discrepancy is retained in the report.'
}
