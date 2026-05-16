# urusai db clear: truncate all Postgres tables (schema preserved; Milvus untouched).
#
# Usage:
#   .\scripts\urusai.ps1 db clear

[CmdletBinding()]
param([switch]$NoPause)

$ErrorActionPreference = "Stop"
$global:UrusaiNoPause = [bool]$NoPause

. (Join-Path $PSScriptRoot "..\_lib\common.ps1")

Wait-DockerReady | Out-Null

$cfg = Get-LauncherConfig
$envPython = Get-EnvPython $cfg

& $envPython -m urusai.scripts.db clear
$rc = $LASTEXITCODE

Pause-OnExit
exit $rc
