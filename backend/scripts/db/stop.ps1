# urusai db stop: docker compose stop / down / down-v.
#
# Usage:
#   .\scripts\urusai.ps1 db stop              # docker compose stop (containers preserved)
#   .\scripts\urusai.ps1 db stop -Down        # docker compose down (containers removed, volumes kept)
#   .\scripts\urusai.ps1 db stop -DownVolumes # docker compose down -v (DATA LOST)

[CmdletBinding()]
param(
    [switch]$Down,
    [switch]$DownVolumes,
    [switch]$NoPause
)

$ErrorActionPreference = "Stop"
$global:UrusaiNoPause = [bool]$NoPause

. (Join-Path $PSScriptRoot "..\_lib\common.ps1")

Wait-DockerReady | Out-Null

$compose = Join-Path $UrusaiBackendRoot "docker-compose.yml"
if (-not (Test-Path $compose)) {
    $compose = Join-Path (Split-Path -Parent $UrusaiBackendRoot) "docker-compose.yml"
}

$logsDir = Join-Path $UrusaiBackendRoot "logs"
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir | Out-Null
}
$outLog = Join-Path $logsDir "docker-compose-stop.out.log"
$errLog = Join-Path $logsDir "docker-compose-stop.err.log"
"" | Set-Content $outLog
"" | Set-Content $errLog

if ($DownVolumes) {
    $action = "down -v (containers + volumes removed; DATA LOST)"
    $dockerArgs = @("compose", "-p", "urusai", "-f", $compose, "--progress=quiet", "down", "-v")
    $color = "Yellow"
} elseif ($Down) {
    $action = "down (containers removed, volumes kept)"
    $dockerArgs = @("compose", "-p", "urusai", "-f", $compose, "--progress=quiet", "down")
    $color = "Cyan"
} else {
    $action = "stop (containers preserved)"
    $dockerArgs = @("compose", "-p", "urusai", "-f", $compose, "--progress=quiet", "stop")
    $color = "Cyan"
}

Write-Host ""
Write-Host "urusai DB stack: $action" -ForegroundColor $color

$proc = Start-Process -FilePath "docker" -ArgumentList $dockerArgs `
    -WorkingDirectory $UrusaiBackendRoot -NoNewWindow -PassThru `
    -RedirectStandardOutput $outLog `
    -RedirectStandardError $errLog

$spinner = @('|', '/', '-', '\')
$i = 0
$startedAt = Get-Date
while (-not $proc.HasExited) {
    $elapsed = ((Get-Date) - $startedAt).TotalSeconds.ToString("F1")
    Write-Host -NoNewline ("`r  {0} waiting... {1}s    " -f $spinner[$i % 4], $elapsed)
    Start-Sleep -Milliseconds 200
    $i++
}
$elapsed = ((Get-Date) - $startedAt).TotalSeconds.ToString("F1")
Write-Host -NoNewline "`r"
Write-Host ("  done in {0}s                                                " -f $elapsed) -ForegroundColor Green

foreach ($f in @($outLog, $errLog)) {
    if (Test-Path $f) {
        Get-Content $f | Where-Object { $_ -and $_.Trim() } | ForEach-Object {
            Write-Host "  $_"
        }
    }
}

$rc = $proc.ExitCode
if ($rc -ne 0) {
    Write-Host ""
    Write-Host "docker compose exited with code $rc" -ForegroundColor Red
}

Pause-OnExit
exit $rc
