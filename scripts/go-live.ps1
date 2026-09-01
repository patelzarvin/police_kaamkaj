# One-click: full project live on the web (no card, no Render paid plan)
# Identical to localhost — live RTSP, YOLO, journey search, everything.
# Run: double-click GO-LIVE.bat  OR  .\scripts\go-live.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

Write-Host ""
Write-Host "=== Gujarat Police Sentinel — Go Live (Full Stack) ===" -ForegroundColor Cyan
Write-Host ""

function Resolve-Python {
    $venvPy = Join-Path $Root ".venv\Scripts\python.exe"
    if (Test-Path $venvPy) { return $venvPy }
    foreach ($cmd in @("py", "python", "python3")) {
        if (Get-Command $cmd -ErrorAction SilentlyContinue) { return $cmd }
    }
    throw "Python not found. Install Python 3.11+ or run: py -m venv .venv"
}

function Resolve-PythonArgs([string]$exe) {
    if ($exe -eq "py") { return @("-3.11") }
    return @()
}

$python = Resolve-Python
$pyArgs = Resolve-PythonArgs $python

Write-Host "[1/5] Checking Python dependencies..." -ForegroundColor Yellow
& $python @pyArgs -c "import fastapi, cv2, ultralytics" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "      Installing backend requirements (first run may take a few minutes)..." -ForegroundColor Gray
    & $python @pyArgs -m pip install -r requirements.txt -q
    if ($LASTEXITCODE -ne 0) { throw "pip install failed" }
}

Write-Host "[2/5] Checking cloudflared tunnel..." -ForegroundColor Yellow
if (-not (Get-Command cloudflared -ErrorAction SilentlyContinue)) {
    Write-Host "      Installing cloudflared via winget..." -ForegroundColor Gray
    winget install --id Cloudflare.cloudflared -e --accept-source-agreements --accept-package-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}

Write-Host "[3/5] Starting backend on :8000..." -ForegroundColor Green
$env:RENDER_DEMO_MODE = "false"
$env:ENABLE_LIVE_PIPELINE = "true"
$backend = Start-Process -PassThru -WindowStyle Minimized -FilePath $python -ArgumentList (@pyArgs + @("-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000")) -WorkingDirectory $Root
Start-Sleep -Seconds 5

Write-Host "[4/5] Starting frontend on :3000..." -ForegroundColor Green
if (-not (Test-Path "$Root\frontend\node_modules")) {
    Write-Host "      Running npm install..." -ForegroundColor Gray
    Push-Location "$Root\frontend"
    npm install --silent
    Pop-Location
}
$frontend = Start-Process -PassThru -WindowStyle Minimized -FilePath "cmd.exe" -ArgumentList "/c", "npm run dev" -WorkingDirectory "$Root\frontend"
Start-Sleep -Seconds 8

Write-Host "[5/5] Opening public tunnel..." -ForegroundColor Green
Write-Host ""
Write-Host "  Local dashboard:  http://localhost:3000" -ForegroundColor White
Write-Host "  Share this URL (appears below in ~10 sec):" -ForegroundColor Yellow
Write-Host "  Keep this window OPEN during your demo." -ForegroundColor Red
Write-Host ""

try {
    cloudflared tunnel --url http://localhost:3000
} finally {
    Write-Host "Shutting down..." -ForegroundColor Gray
    Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $frontend.Id -Force -ErrorAction SilentlyContinue
}
