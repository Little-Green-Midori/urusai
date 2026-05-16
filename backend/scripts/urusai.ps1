# URUSAI unified launcher (Windows / PowerShell).
#
# Usage:
#   .\scripts\urusai.ps1 <category> <action> [args...]
#
# Categories and actions:
#   env       install | uninstall | reinstall
#   server    start | stop
#   db        start | stop | status | init | clear | rebuild
#   models    download
#   help
#
# Examples:
#   .\scripts\urusai.ps1 env install
#   .\scripts\urusai.ps1 db start
#   .\scripts\urusai.ps1 db stop -Down
#   .\scripts\urusai.ps1 server start
#   .\scripts\urusai.ps1 server stop
#   .\scripts\urusai.ps1 models download
#   .\scripts\urusai.ps1 help

[CmdletBinding(PositionalBinding=$false)]
param(
    [Parameter(Position=0)][string]$Category,
    [Parameter(Position=1)][string]$Action,
    [Parameter(Position=2, ValueFromRemainingArguments=$true)]$Args
)

$ErrorActionPreference = "Stop"

$VALID = @{
    env    = @("install", "uninstall", "reinstall")
    server = @("start", "stop")
    db     = @("start", "stop", "status", "init", "clear", "rebuild")
    models = @("download")
}

function Show-Help {
    Write-Host ""
    Write-Host "URUSAI launcher" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\scripts\urusai.ps1 <category> <action> [args...]"
    Write-Host ""
    Write-Host "Categories:" -ForegroundColor Yellow
    foreach ($cat in @("env", "server", "db", "models")) {
        $actions = $VALID[$cat] -join " | "
        Write-Host ("  {0,-8} {1}" -f $cat, $actions)
    }
    Write-Host ""
    Write-Host "Common flows:" -ForegroundColor Yellow
    Write-Host "  First time:        .\scripts\urusai.ps1 env install"
    Write-Host "  Start everything:  .\scripts\urusai.ps1 db start ; .\scripts\urusai.ps1 server start"
    Write-Host "  Health check:      .\scripts\urusai.ps1 db status"
    Write-Host "  Stop everything:   .\scripts\urusai.ps1 server stop ; .\scripts\urusai.ps1 db stop"
    Write-Host ""
}

if (-not $Category -or $Category -in @("help", "-h", "--help", "/?")) {
    Show-Help
    exit 0
}

if (-not $VALID.ContainsKey($Category)) {
    Write-Host "Unknown category: $Category" -ForegroundColor Red
    Show-Help
    exit 1
}

if (-not $Action) {
    Write-Host "Missing action for category '$Category'. Valid: $($VALID[$Category] -join ', ')" -ForegroundColor Red
    exit 1
}

if ($Action -notin $VALID[$Category]) {
    Write-Host "Unknown action '$Action' for category '$Category'. Valid: $($VALID[$Category] -join ', ')" -ForegroundColor Red
    exit 1
}

$target = Join-Path $PSScriptRoot "$Category\$Action.ps1"
if (-not (Test-Path $target)) {
    Write-Host "Action script missing: $target" -ForegroundColor Red
    exit 1
}

& $target @Args
exit $LASTEXITCODE
