# Seed demo-brain memories for the visualizer (~62 beliefs, hub-linked edges)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Harness = "http://127.0.0.1:3000"

Write-Host "Seeding demo-brain via harness ..." -ForegroundColor Cyan
for ($i = 0; $i -lt 30; $i++) {
  try {
    $h = Invoke-RestMethod -Uri "$Harness/health" -TimeoutSec 5
    if ($h.status -eq "ok") { break }
  } catch { Start-Sleep -Seconds 2 }
}

$result = Invoke-RestMethod -Uri "$Harness/api/demo/seed" -Method POST `
  -ContentType "application/json" -Body '{"force":false}' -TimeoutSec 180

Write-Host "  User:    $($result.user_id)" -ForegroundColor Green
Write-Host "  Beliefs: $($result.beliefs)" -ForegroundColor Green
Write-Host "  Edges:   $($result.edges)" -ForegroundColor Green
Write-Host "  Open:    http://localhost:3000?user=demo-brain" -ForegroundColor Yellow
