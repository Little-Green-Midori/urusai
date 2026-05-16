# urusai server start: launch uvicorn for the FastAPI app.
#
# Usage:
#   .\scripts\urusai.ps1 server start

[CmdletBinding()]
param([switch]$NoPause)

$ErrorActionPreference = "Stop"
$global:UrusaiNoPause = [bool]$NoPause

. (Join-Path $PSScriptRoot "..\_lib\common.ps1")

$cfg = Get-LauncherConfig
$envPython = Get-EnvPython $cfg

$logsDir = Join-Path $UrusaiBackendRoot "logs"
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir | Out-Null
}
$uvOut = Join-Path $logsDir "uvicorn.out.log"
$uvErr = Join-Path $logsDir "uvicorn.err.log"
foreach ($f in @($uvOut, $uvErr)) { "" | Set-Content $f }

Write-Host ""
Write-Host "Starting urusai uvicorn (logs in $logsDir)..." -ForegroundColor Cyan

$uv = Start-Process -FilePath $envPython -ArgumentList @(
    "-m", "uvicorn", "urusai.api.main:app",
    "--reload", "--host", "127.0.0.1", "--port", "8000"
) -WorkingDirectory $UrusaiBackendRoot -PassThru -WindowStyle Hidden `
    -RedirectStandardOutput $uvOut `
    -RedirectStandardError $uvErr

Start-Sleep -Seconds 4
$uvAlive = -not $uv.HasExited

function Show-LogTail {
    param([string]$Label, [string]$OutPath, [string]$ErrPath, [int]$N = 20)
    Write-Host "  --- ${Label}: last $N lines ---" -ForegroundColor DarkGray
    foreach ($p in @($OutPath, $ErrPath)) {
        if ((Test-Path $p) -and ((Get-Item $p).Length -gt 0)) {
            Get-Content $p -Tail $N | ForEach-Object { Write-Host "    $_" }
        }
    }
}

Write-Host ""
if ($uvAlive) {
    Write-Host "  uvicorn   running (PID $($uv.Id))   http://127.0.0.1:8000" -ForegroundColor Green
    Show-LogTail -Label "uvicorn" -OutPath $uvOut -ErrPath $uvErr
} else {
    Write-Host "  uvicorn   FAILED — see $uvOut / $uvErr" -ForegroundColor Red
    Show-LogTail -Label "uvicorn (FAILED)" -OutPath $uvOut -ErrPath $uvErr
}

Write-Host ""
Write-Host "Live tail logs:" -ForegroundColor Cyan
Write-Host "  Get-Content $uvOut -Wait -Tail 0    # uvicorn stdout"

Write-Host ""
Write-Host "Stop:    .\scripts\urusai.ps1 server stop" -ForegroundColor Yellow
Write-Host "Status:  .\scripts\urusai.ps1 db status"

Pause-OnExit
