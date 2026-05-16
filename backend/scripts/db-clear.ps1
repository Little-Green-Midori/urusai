# Truncate all Postgres tables (schema preserved). Milvus collections untouched (use db-rebuild for that).
#
# Usage:
#   .\scripts\db-clear.ps1
#   .\scripts\db-clear.ps1 -NoPause

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

& $envPython -m urusai.scripts.db clear
$rc = $LASTEXITCODE

Pause-OnExit
exit $rc
