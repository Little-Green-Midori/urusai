# Initialize urusai DB: verify Postgres + Milvus connectivity.
#
# Usage:
#   .\scripts\db-init.ps1
#   .\scripts\db-init.ps1 -NoPause

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

& $envPython -m urusai.scripts.db init
$rc = $LASTEXITCODE

Pause-OnExit
exit $rc
