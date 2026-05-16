# Start urusai DB stack (Postgres + Milvus + etcd + minio + attu) via docker compose.
#
# Usage:
#   .\scripts\db-start.ps1
#   .\scripts\db-start.ps1 -NoPause   # don't wait Enter at end

[CmdletBinding()]
param(
    [switch]$NoPause
)

$ErrorActionPreference = "Stop"
$global:UrusaiNoPause = [bool]$NoPause

. (Join-Path $PSScriptRoot "_db-common.ps1")

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$compose = Join-Path $root "docker-compose.yml"
$logsDir = Join-Path $root "logs"

if (-not (Test-Path $compose)) {
    Write-Host "docker-compose.yml not found at $compose" -ForegroundColor Red
    Pause-OnExit
    exit 1
}

Wait-DockerReady | Out-Null

if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir | Out-Null
}
$outLog = Join-Path $logsDir "docker-compose-up.out.log"
$errLog = Join-Path $logsDir "docker-compose-up.err.log"
"" | Set-Content $outLog
"" | Set-Content $errLog

Write-Host ""
Write-Host "Starting urusai DB stack..." -ForegroundColor Cyan

$proc = Start-Process -FilePath "docker" -ArgumentList @(
    "compose", "-p", "urusai", "-f", $compose,
    "--progress=quiet", "up", "-d"
) -WorkingDirectory $root -NoNewWindow -PassThru `
    -RedirectStandardOutput $outLog `
    -RedirectStandardError $errLog

# Spinner — single line in-place refresh
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

# Replay captured output
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
    Write-Host "docker compose up exited with code $rc" -ForegroundColor Red
    Write-Host "Logs: $outLog / $errLog"
    Pause-OnExit
    exit $rc
}

Write-Host ""
Write-Host "Endpoints (host):" -ForegroundColor Green
Write-Host "  Postgres : localhost:5433"
Write-Host "  Milvus   : localhost:19531 (gRPC) / localhost:9092 (health)"
Write-Host "  MinIO    : localhost:9100 (API) / http://localhost:9101 (console)"
Write-Host "  Attu     : http://localhost:3001"
Write-Host ""
Write-Host "Status: .\scripts\db-status.ps1" -ForegroundColor Yellow
Write-Host "Stop:   .\scripts\db-stop.ps1"

Pause-OnExit
