# Run this AFTER you add your card on Render (hackathon credits apply).
# .\scripts\card-ready-deploy.ps1

Write-Host ""
Write-Host "=== Render Full Deploy — Card Ready Checklist ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Everything is already pushed to GitHub. When your card is connected:" -ForegroundColor White
Write-Host ""
Write-Host "  1. Go to  https://dashboard.render.com/billing  → add card" -ForegroundColor Yellow
Write-Host "  2. New → Blueprint → connect  patelzarvin/police_kaamkaj" -ForegroundColor Yellow
Write-Host "  3. Apply  (creates service: police-kaamkaj, Standard plan)" -ForegroundColor Yellow
Write-Host "  4. Wait 15-25 min for Docker build (PyTorch + YOLO download)" -ForegroundColor Yellow
Write-Host "  5. Open  https://police-kaamkaj.onrender.com" -ForegroundColor Green
Write-Host "  6. Wait 30 sec for live camera feeds to connect" -ForegroundColor Gray
Write-Host ""
Write-Host "You can delete old demo services after:" -ForegroundColor Gray
Write-Host "  - police-kaamkaj-api" -ForegroundColor Gray
Write-Host "  - police-kaamkaj-web" -ForegroundColor Gray
Write-Host ""
Write-Host "Config files (already in repo):" -ForegroundColor White
Write-Host "  - Dockerfile                  full stack image" -ForegroundColor Gray
Write-Host "  - render.yaml                 Blueprint (Standard, live AI)" -ForegroundColor Gray
Write-Host "  - render-free-demo.yaml       free demo backup (no card)" -ForegroundColor Gray
Write-Host ""
Write-Host "Until card is ready — use GO-LIVE.bat for full demo (laptop must stay on)." -ForegroundColor Cyan
Write-Host ""

$open = Read-Host "Open Render dashboard now? (y/n)"
if ($open -eq "y") { Start-Process "https://dashboard.render.com" }
