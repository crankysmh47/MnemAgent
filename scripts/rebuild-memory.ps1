# Force-rebuild MnemOS memory container with latest prompt/extraction code
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Push-Location $Root
docker compose build --no-cache mnemos-memory
docker compose up -d --force-recreate mnemos-memory
Start-Sleep -Seconds 8
$health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 30
Write-Host "Health: $($health | ConvertTo-Json -Compress)"
if ($health.prompt_version -ne "v4-dual-path-write") {
  Write-Warning "Expected prompt_version v4-dual-path-write, got $($health.prompt_version)"
}
Pop-Location
