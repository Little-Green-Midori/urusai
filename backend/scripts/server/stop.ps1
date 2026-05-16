# urusai server stop: kill uvicorn (including multiprocessing children) and free port 8000.
#
# Usage:
#   .\scripts\urusai.ps1 server stop

$ErrorActionPreference = "Continue"

$round1 = Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
    Where-Object {
        $_.CommandLine -and $_.CommandLine -match 'uvicorn'
    }

if ($round1) {
    foreach ($proc in $round1) {
        $cmdline = $proc.CommandLine
        if ($cmdline.Length -gt 120) { $cmdline = $cmdline.Substring(0, 120) + "..." }
        Write-Host "Killing PID $($proc.ProcessId)  $cmdline"
        try {
            Stop-Process -Id $proc.ProcessId -Force -ErrorAction Stop
        } catch {
            Write-Warning "  failed: $_"
        }
    }
} else {
    Write-Host "No uvicorn python processes found."
}

Start-Sleep -Milliseconds 500

$allPython = Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue
foreach ($p in $allPython) {
    if (-not $p.CommandLine) { continue }
    if ($p.CommandLine -notmatch 'multiprocessing\.spawn') { continue }
    if ($p.CommandLine -notmatch 'parent_pid=(\d+)') { continue }
    $ppid = [int]$Matches[1]
    if (Get-Process -Id $ppid -ErrorAction SilentlyContinue) { continue }
    Write-Host "Killing orphan PID $($p.ProcessId)  parent_pid=$ppid (dead)"
    try {
        Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop
    } catch {
        Write-Warning "  failed: $_"
    }
}

$conns = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
foreach ($c in $conns) {
    try {
        Stop-Process -Id $c.OwningProcess -Force -ErrorAction Stop
        Write-Host "Freed port 8000 (killed PID $($c.OwningProcess))"
    } catch {
        Write-Warning "Port 8000 held by PID $($c.OwningProcess), cannot kill: $_"
    }
}

Write-Host "Done." -ForegroundColor Green
