# Shared helpers for db-*.ps1 scripts. Dot-source via:
#   . (Join-Path $PSScriptRoot "_db-common.ps1")

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

function Get-LauncherConfig {
    $configFile = Join-Path $PSScriptRoot ".urusai-launcher.json"
    if (-not (Test-Path $configFile)) {
        Write-Host "Launcher config missing: $configFile" -ForegroundColor Red
        Write-Host "Run .\scripts\start.ps1 first to complete setup." -ForegroundColor Yellow
        Pause-OnExit
        exit 1
    }
    return Get-Content $configFile -Raw | ConvertFrom-Json
}

function Get-EnvPython {
    param($cfg)
    $py = Join-Path $cfg.conda_root "envs\$($cfg.env_name)\python.exe"
    if (-not (Test-Path $py)) {
        Write-Host "Env python not found: $py" -ForegroundColor Red
        Pause-OnExit
        exit 1
    }
    return $py
}
