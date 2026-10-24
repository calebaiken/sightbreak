Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:EvidenceRoot = $PSScriptRoot

function Invoke-Recorded {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][string]$Executable,
        [string[]]$Arguments = @(),
        [string]$WorkingDirectory = $script:EvidenceRoot,
        [int]$TimeoutSeconds = 180,
        [switch]$AllowFailure,
        [string]$StdoutPath
    )
    $logDir = Join-Path $script:EvidenceRoot 'logs'
    [IO.Directory]::CreateDirectory($logDir) | Out-Null
    if (-not $StdoutPath) { $StdoutPath = Join-Path $logDir "$Name.stdout.log" }
    [IO.Directory]::CreateDirectory((Split-Path $StdoutPath)) | Out-Null
    $stderrPath = Join-Path $logDir "$Name.stderr.log"
    $info = [Diagnostics.ProcessStartInfo]::new()
    $info.FileName = $Executable
    $info.WorkingDirectory = $WorkingDirectory
    $info.UseShellExecute = $false
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    $info.CreateNoWindow = $true
    foreach ($arg in $Arguments) { $info.ArgumentList.Add($arg) }
    $entry = [ordered]@{
        name = $Name; started_utc = [DateTime]::UtcNow.ToString('o')
        executable = $Executable; arguments = $Arguments
        working_directory = $WorkingDirectory; timeout_seconds = $TimeoutSeconds
        stdout = $StdoutPath; stderr = $stderrPath
    }
    $entry | ConvertTo-Json -Compress -Depth 10 | Add-Content (Join-Path $script:EvidenceRoot 'commands-started.jsonl') -Encoding utf8
    $process = [Diagnostics.Process]::new()
    $process.StartInfo = $info
    $stdoutStream = [IO.File]::Create($StdoutPath)
    $stderrStream = [IO.File]::Create($stderrPath)
    try {
        $process.Start() | Out-Null
        $copyOut = $process.StandardOutput.BaseStream.CopyToAsync($stdoutStream)
        $copyErr = $process.StandardError.BaseStream.CopyToAsync($stderrStream)
        $timedOut = -not $process.WaitForExit($TimeoutSeconds * 1000)
        if ($timedOut) { $process.Kill($true); $process.WaitForExit() }
        [Threading.Tasks.Task]::WaitAll(@($copyOut, $copyErr))
        $entry['finished_utc'] = [DateTime]::UtcNow.ToString('o')
        $entry['exit_code'] = $process.ExitCode
        $entry['timed_out'] = $timedOut
    } finally {
        $stdoutStream.Dispose(); $stderrStream.Dispose(); $process.Dispose()
    }
    $entry['stdout_sha256'] = (Get-FileHash $StdoutPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $entry['stderr_sha256'] = (Get-FileHash $stderrPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $entry | ConvertTo-Json -Compress -Depth 10 | Add-Content (Join-Path $script:EvidenceRoot 'commands.jsonl') -Encoding utf8
    if (($entry.exit_code -ne 0 -or $entry.timed_out) -and -not $AllowFailure) {
        throw "Recorded command $Name failed: exit=$($entry.exit_code), timed_out=$($entry.timed_out). See $stderrPath and $StdoutPath"
    }
    return [pscustomobject]$entry
}
