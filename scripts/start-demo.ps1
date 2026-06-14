# Start stack and seed demo-brain for the memory visualizer
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Uid = "demo-brain"
$Harness = "http://127.0.0.1:3000"

Write-Host "Starting MnemOS stack..." -ForegroundColor Cyan
Push-Location $Root
docker compose up -d --build
Pop-Location

Write-Host "Waiting for harness health..." -ForegroundColor Yellow
for ($i = 0; $i -lt 40; $i++) {
  try {
    $h = Invoke-RestMethod -Uri "$Harness/health" -TimeoutSec 5
    if ($h.status -eq "ok") { break }
  } catch { Start-Sleep -Seconds 3 }
}

Write-Host "Seeding demo memories for $Uid ..."
$result = Invoke-RestMethod -Uri "$Harness/api/demo/seed" -Method POST `
  -ContentType "application/json" -Body '{"force":false}' -TimeoutSec 180

Write-Host ""
Write-Host "Ready!" -ForegroundColor Green
Write-Host "  Beliefs:     $($result.beliefs)"
Write-Host "  Edges:       $($result.edges)"
Write-Host "  Visualizer:  http://localhost:3000?user=$Uid"
Write-Host ""
Write-Host "Try OpenClaw: openclaw agent --agent main --message \"Remember I prefer Python for APIs\""
Write-Host "Terminal proof: .\scripts\prove-memory.ps1"
