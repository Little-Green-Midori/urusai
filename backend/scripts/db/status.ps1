# urusai db status: container status + Postgres + Milvus connectivity.
#
# Usage:
#   .\scripts\urusai.ps1 db status

[CmdletBinding()]
param([switch]$NoPause)

$ErrorActionPreference = "Stop"
$global:UrusaiNoPause = [bool]$NoPause

. (Join-Path $PSScriptRoot "..\_lib\common.ps1")

Wait-DockerReady | Out-Null

$cfg = Get-LauncherConfig
$envPython = Get-EnvPython $cfg

$compose = Join-Path $UrusaiBackendRoot "docker-compose.yml"
if (-not (Test-Path $compose)) {
    $compose = Join-Path (Split-Path -Parent $UrusaiBackendRoot) "docker-compose.yml"
}

Write-Host "=== Container status ===" -ForegroundColor Cyan
Push-Location $UrusaiBackendRoot
try {
    & docker compose -p urusai -f $compose ps
} finally {
    Pop-Location
}

Write-Host ""
& $envPython -m urusai.scripts.db status
$rc = $LASTEXITCODE

Pause-OnExit
exit $rc
