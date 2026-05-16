# Shared helpers for urusai launcher scripts.
# Dot-source via:
#   . (Join-Path $PSScriptRoot "..\_lib\common.ps1")
#
# After sourcing, $UrusaiScriptsRoot is set to backend/scripts/ regardless of
# which subdirectory called it.

$_thisLibDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$global:UrusaiScriptsRoot = Split-Path -Parent $_thisLibDir
$global:UrusaiBackendRoot = Split-Path -Parent $global:UrusaiScriptsRoot

function Pause-OnExit {
    if ($global:UrusaiNoPause) { return }
    Write-Host ""
    Write-Host "Press Enter to close..." -ForegroundColor DarkGray
    [void](Read-Host)
}

function Test-DockerAvailable {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        return $false
    }
    try {
        $null = & docker info 2>&1
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Wait-DockerReady {
    if (Test-DockerAvailable) { return $true }

    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Host ""
        Write-Host "docker CLI not found on PATH." -ForegroundColor Red
        Write-Host "Install Docker Desktop first: https://www.docker.com/products/docker-desktop/"
        Pause-OnExit
        exit 1
    }

    Write-Host ""
    Write-Host "Docker daemon not reachable." -ForegroundColor Yellow
    Write-Host "Please start Docker Desktop and wait until the whale icon is ready"
    Write-Host "(first launch typically takes 30-60 seconds)."
    Write-Host "Press Enter to retry (Ctrl+C to abort)..."

    while ($true) {
        [void](Read-Host)
        if (Test-DockerAvailable) {
            Write-Host "Docker ready." -ForegroundColor Green
            return $true
        }
        Write-Host "  still not reachable, press Enter to retry..." -ForegroundColor Yellow
    }
}

function Get-LauncherConfigPath {
    Join-Path $global:UrusaiScriptsRoot ".urusai-launcher.json"
}

function Test-LauncherConfig {
    Test-Path (Get-LauncherConfigPath)
}

function Get-LauncherConfig {
    $configFile = Get-LauncherConfigPath
    if (-not (Test-Path $configFile)) {
        Write-Host "Launcher config missing: $configFile" -ForegroundColor Red
        Write-Host "Run .\scripts\urusai.ps1 env install first to complete setup." -ForegroundColor Yellow
        Pause-OnExit
        exit 1
    }
    return Get-Content $configFile -Raw | ConvertFrom-Json
}

function Save-LauncherConfig {
    param($cfg)
    $cfg | ConvertTo-Json | Set-Content (Get-LauncherConfigPath) -Encoding UTF8
}

function Get-EnvPython {
    param($cfg)
    $py = Join-Path $cfg.conda_root "envs\$($cfg.env_name)\python.exe"
    if (-not (Test-Path $py)) {
        Write-Host "Env python not found: $py" -ForegroundColor Red
        Write-Host "Run .\scripts\urusai.ps1 env install to provision the environment." -ForegroundColor Yellow
        Pause-OnExit
        exit 1
    }
    return $py
}

function Find-CondaCandidates {
    @(
        "$env:USERPROFILE\miniconda3",
        "$env:USERPROFILE\anaconda3",
        "$env:USERPROFILE\miniforge3",
        "C:\ProgramData\miniconda3",
        "C:\ProgramData\anaconda3"
    ) | Where-Object { Test-Path (Join-Path $_ "Scripts\conda.exe") }
}
