# Wait for GitHub rate limit reset then run portfolio deep evidence
$venvPython = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
$logFile = Join-Path $PSScriptRoot "..\.freebuff\deep-evidence-retry.log"
$errFile = Join-Path $PSScriptRoot "..\.freebuff\deep-evidence-retry.log.err"

function Write-Log($msg) {
    $ts = Get-Date -Format "HH:mm:ss"
    $line = "[$ts] $msg"
    Write-Host $line
    Add-Content -Path $logFile -Value $line
}

# Clear old logs
Set-Content -Path $logFile -Value ""
Set-Content -Path $errFile -Value ""

# Check rate limit
$resp = Invoke-RestMethod -Uri "https://api.github.com/rate_limit" -Headers @{"Accept"="application/vnd.github+json"; "User-Agent"="GrowthOS/0.1"} -ErrorAction SilentlyContinue
$remaining = $resp.resources.core.remaining
$resetTs = $resp.resources.core.reset
$now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$secsLeft = [Math]::Max(0, $resetTs - $now)

Write-Log "GitHub rate limit: $remaining/60, resets in $([Math]::Floor($secsLeft/60))m $($secsLeft % 60)s"

if ($remaining -lt 10) {
    $waitTime = $secsLeft + 15
    Write-Log "Waiting $([Math]::Floor($waitTime/60))m $($waitTime % 60)s for rate limit reset..."
    Start-Sleep -Seconds $waitTime
    Write-Log "Wait complete. Running deep evidence pass..."
}

Write-Log "Starting portfolio-deep-evidence --run..."
$proc = Start-Process -FilePath $venvPython -ArgumentList "-m","growthos.cli.main","portfolio-deep-evidence","--run" `
    -RedirectStandardOutput $logFile -RedirectStandardError $errFile `
    -NoNewWindow -PassThru -Wait

Write-Log "Process exited with code $($proc.ExitCode)"
Write-Log "Done."
