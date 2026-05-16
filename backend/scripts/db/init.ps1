# urusai db init: verify Postgres + Milvus connectivity.
#
# Usage:
#   .\scripts\urusai.ps1 db init

[CmdletBinding()]
param([switch]$NoPause)

$ErrorActionPreference = "Stop"
$global:UrusaiNoPause = [bool]$NoPause

. (Join-Path $PSScriptRoot "..\_lib\common.ps1")

Wait-DockerReady | Out-Null

$cfg = Get-LauncherConfig
$envPython = Get-EnvPython $cfg

& $envPython -m urusai.scripts.db init
$rc = $LASTEXITCODE

Pause-OnExit
exit $rc
