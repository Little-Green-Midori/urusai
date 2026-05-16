# Drop all Postgres tables + Milvus collections.
#
# Usage:
#   .\scripts\db-rebuild.ps1
#   .\scripts\db-rebuild.ps1 -NoPause
# WARNING: this drops all data. Use db-clear.ps1 to truncate but keep schema.

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

& $envPython -m urusai.scripts.db rebuild
$rc = $LASTEXITCODE

Pause-OnExit
exit $rc
