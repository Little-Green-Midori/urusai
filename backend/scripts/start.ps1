# urusai launcher: first-time interactive setup, then start uvicorn.
#
# Usage:
#   .\scripts\start.ps1                 # normal launch
#   .\scripts\start.ps1 -Reconfigure    # redo first-run prompts
#   .\scripts\start.ps1 -Recreate       # drop conda env and rebuild from environment.yml
#   .\scripts\start.ps1 -NoLaunch       # only ensure env, don't start uvicorn
#
# Saves config to scripts\.urusai-launcher.json (gitignored).
# Spawned uvicorn logs to logs\uvicorn.{out,err}.log.

[CmdletBinding()]
param(
    [switch]$Reconfigure,
    [switch]$Recreate,
    [switch]$NoLaunch
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$configFile = Join-Path $PSScriptRoot ".urusai-launcher.json"
$envYaml = Join-Path $root "environment.yml"
$logsDir = Join-Path $root "logs"


function Find-CondaCandidates {
    @(
        "$env:USERPROFILE\miniconda3",
        "$env:USERPROFILE\anaconda3",
        "$env:USERPROFILE\miniforge3",
        "C:\ProgramData\miniconda3",
        "C:\ProgramData\anaconda3"
    ) | Where-Object { Test-Path (Join-Path $_ "Scripts\conda.exe") }
}


function Run-Setup {
    Write-Host ""
    Write-Host "=== urusai launcher: first-time setup ===" -ForegroundColor Cyan
    Write-Host ""

    $candidates = @(Find-CondaCandidates)
    $condaRoot = $null

    if ($candidates.Count -gt 0) {
        Write-Host "Detected conda installations:"
        for ($i = 0; $i -lt $candidates.Count; $i++) {
            Write-Host ("  [{0}] {1}" -f ($i + 1), $candidates[$i])
        }
        Write-Host "  [m] enter manually"
        Write-Host ""
        $sel = Read-Host "Pick [1]"
        if ($sel -eq "") { $sel = "1" }
        if ($sel -match "^\d+$" -and [int]$sel -ge 1 -and [int]$sel -le $candidates.Count) {
            $condaRoot = $candidates[[int]$sel - 1]
        }
    }

    while (-not $condaRoot) {
        Write-Host ""
        $entered = Read-Host "Enter conda root path (e.g. C:\Users\You\miniconda3)"
        if (Test-Path (Join-Path $entered "Scripts\conda.exe")) {
            $condaRoot = $entered
        } else {
            Write-Host ("  Not found: {0}\Scripts\conda.exe" -f $entered) -ForegroundColor Red
        }
    }

    Write-Host ""
    $envName = Read-Host "Env name [urusai]"
    if ($envName -eq "") { $envName = "urusai" }

    $cfg = [ordered]@{
        conda_root = $condaRoot
        env_name   = $envName
    }
    $cfg | ConvertTo-Json | Set-Content $configFile -Encoding UTF8

    Write-Host ""
    Write-Host "Saved: $configFile" -ForegroundColor Green
    return $cfg
}


function Read-Config {
    Get-Content $configFile -Raw | ConvertFrom-Json
}


function Get-EnvPython($cfg) {
    Join-Path $cfg.conda_root "envs\$($cfg.env_name)\python.exe"
}


function Ensure-Env($cfg) {
    $conda = Join-Path $cfg.conda_root "Scripts\conda.exe"
    $envPython = Get-EnvPython $cfg

    if ($Recreate -and (Test-Path $envPython)) {
        Write-Host ""
        Write-Host "Removing existing env '$($cfg.env_name)'..." -ForegroundColor Yellow
        & $conda env remove -n $cfg.env_name -y
    }

    if (-not (Test-Path $envPython)) {
        Write-Host ""
        Write-Host "Creating env '$($cfg.env_name)' from environment.yml..." -ForegroundColor Yellow
        & $conda env create -f $envYaml -n $cfg.env_name
        if (-not (Test-Path $envPython)) {
            Write-Error "Env creation failed."
            exit 1
        }

        Write-Host ""
        Write-Host "Installing torch (cu128 wheel)..." -ForegroundColor Yellow
        & $envPython -m pip install --extra-index-url https://download.pytorch.org/whl/cu128 torch

        Write-Host ""
        Write-Host "Installing urusai (editable)..." -ForegroundColor Yellow
        Push-Location $root
        try {
            & $envPython -m pip install -e ".[dev]"
        } finally {
            Pop-Location
        }
    }

    # Verify import.
    $check = & $envPython -c "from urusai.api.main import app" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "urusai not importable. Reinstalling..." -ForegroundColor Yellow
        Push-Location $root
        try {
            & $envPython -m pip install -e ".[dev]"
        } finally {
            Pop-Location
        }
        $check = & $envPython -c "from urusai.api.main import app" 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Still failing:" -ForegroundColor Red
            Write-Host $check
            exit 1
        }
    }

    return $envPython
}


# === Main ===

if ($Reconfigure -or -not (Test-Path $configFile)) {
    $cfg = Run-Setup
} else {
    $cfg = Read-Config
    Write-Host "Config: conda=$($cfg.conda_root)  env=$($cfg.env_name)" -ForegroundColor DarkGray
}

$envPython = Ensure-Env $cfg

if ($NoLaunch) {
    Write-Host ""
    Write-Host "Setup OK. Not launching (-NoLaunch)." -ForegroundColor Green
    return
}

# Prepare logs dir
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
) -WorkingDirectory $root -PassThru -WindowStyle Hidden `
    -RedirectStandardOutput $uvOut `
    -RedirectStandardError $uvErr

# Give uvicorn a few seconds to start (or to fail).
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
Write-Host "Stop:         .\scripts\kill.ps1" -ForegroundColor Yellow
Write-Host "Reconfigure:  .\scripts\start.ps1 -Reconfigure"
Write-Host "Recreate env: .\scripts\start.ps1 -Recreate"
Write-Host "Logs:         $logsDir"
Write-Host ""
Write-Host "Press Enter to close this launcher (uvicorn keeps running if alive)."
Read-Host | Out-Null
