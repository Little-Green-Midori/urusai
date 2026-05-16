# urusai db rebuild: drop all Postgres tables + Milvus collections.
#
# Usage:
#   .\scripts\urusai.ps1 db rebuild
#
# WARNING: this drops all data. Use db clear to truncate but keep schema.

[CmdletBinding()]
param([switch]$NoPause)

$ErrorActionPreference = "Stop"
$global:UrusaiNoPause = [bool]$NoPause

. (Join-Path $PSScriptRoot "..\_lib\common.ps1")

Wait-DockerReady | Out-Null

$cfg = Get-LauncherConfig
$envPython = Get-EnvPython $cfg

& $envPython -m urusai.scripts.db rebuild
$rc = $LASTEXITCODE

Pause-OnExit
exit $rc
