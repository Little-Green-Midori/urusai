# Show urusai DB stack status (containers + Postgres + Milvus connectivity).
#
# Usage:
#   .\scripts\db-status.ps1
#   .\scripts\db-status.ps1 -NoPause

[CmdletBinding()]
param(
    [switch]$NoPause
)

$ErrorActionPreference = "Stop"
$global:UrusaiNoPause = [bool]$NoPause

. (Join-Path $PSScriptRoot "_db-common.ps1")

Wait-DockerReady | Out-Null

$cfg = Get-LauncherConfig
$envPython = Get-EnvPython $cfg
$root = Resolve-Path (Join-Path $PSScriptRoot "..")

Write-Host "=== Container status ===" -ForegroundColor Cyan
Push-Location $root
try {
    & docker compose -p urusai -f docker-compose.yml ps
} finally {
    Pop-Location
}

Write-Host ""
& $envPython -m urusai.scripts.db status
$rc = $LASTEXITCODE

Pause-OnExit
exit $rc
