# Start stack and seed a stable demo user for web chat
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Uid = "demo-fast-student"
$Base = "http://127.0.0.1:8000"

Write-Host "Starting MnemOS stack..." -ForegroundColor Cyan
Push-Location $Root
docker compose up -d --build
Pop-Location

Write-Host "Waiting for health..." -ForegroundColor Yellow
for ($i = 0; $i -lt 30; $i++) {
  try {
    $h = Invoke-RestMethod -Uri "$Base/health" -TimeoutSec 3
    if ($h.status -eq "ok") { Start-Sleep -Seconds 5; break }
  } catch { Start-Sleep -Seconds 2 }
}

function Store-Fact($entity, $relation, $value, $category = "preference") {
  $body = @{
    user_id = $Uid
    entity = $entity
    relation = $relation
    value = $value
    category = $category
    conviction = 1.0
  } | ConvertTo-Json -Compress
  Invoke-RestMethod -Uri "$Base/api/memory/store" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 120 | Out-Null
  Start-Sleep -Seconds 4
}

Write-Host "Seeding demo memories for $Uid ..."
Store-Fact "backend_language" "prefers" "Python"
Store-Fact "user" "affiliated_with" "FAST" "persona"
Store-Fact "favorite_ide" "is" "VS Code" "preference"

$dump = Invoke-RestMethod -Uri "$Base/api/memory/dump/${Uid}?format=markdown" -TimeoutSec 30
Write-Host $dump.response
Write-Host ""
Write-Host "Ready!" -ForegroundColor Green
Write-Host "  Chat:        http://localhost:3000"
Write-Host "  Visualizer:  http://localhost:3000/visualizer?user=$Uid"
Write-Host ""
Write-Host "In the web chat, set User ID to: $Uid"
Write-Host "Try: 'What language should I use for our backend API?'"
Write-Host "Try: 'I am a FAST student looking for hackathons'"
Write-Host ""
Write-Host "Terminal proof: .\scripts\prove-memory.ps1"
