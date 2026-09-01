# One-click: put project live on the web (no paid server)
# Run in PowerShell:  .\scripts\go-live.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

Write-Host "=== Gujarat Police Sentinel — Go Live ===" -ForegroundColor Cyan

# 1. Install cloudflared if missing
if (-not (Get-Command cloudflared -ErrorAction SilentlyContinue)) {
    Write-Host "Installing cloudflared..." -ForegroundColor Yellow
    winget install --id Cloudflare.cloudflared -e --accept-source-agreements --accept-package-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}

# 2. Start backend
Write-Host "Starting backend on :8000..." -ForegroundColor Green
$backend = Start-Process -PassThru -WindowStyle Minimized -FilePath "$Root\.venv\Scripts\python.exe" -ArgumentList "-m","uvicorn","backend.main:app","--host","127.0.0.1","--port","8000" -WorkingDirectory $Root

Start-Sleep -Seconds 4

# 3. Start frontend
Write-Host "Starting frontend on :3000..." -ForegroundColor Green
$frontend = Start-Process -PassThru -WindowStyle Minimized -FilePath "cmd.exe" -ArgumentList "/c","npm run dev" -WorkingDirectory "$Root\frontend"

Start-Sleep -Seconds 6

# 4. Public tunnel
Write-Host "Opening public tunnel (this is your LIVE web URL)..." -ForegroundColor Green
Write-Host ""
Write-Host "  Local:  http://localhost:3000" -ForegroundColor Gray
Write-Host "  Public URL will appear below in ~10 seconds:" -ForegroundColor Yellow
Write-Host ""

cloudflared tunnel --url http://localhost:3000

# Cleanup on exit
Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
Stop-Process -Id $frontend.Id -Force -ErrorAction SilentlyContinue
