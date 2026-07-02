# Judge-facing deployment checks.
[CmdletBinding()]
param(
  [string]$MnemosUrl = "http://127.0.0.1:8000",
  [string]$HarnessUrl = "http://127.0.0.1:3000",
  [string]$DemoUser = "demo-brain"
)

$ErrorActionPreference = "Stop"
$ConfigDir = Join-Path $env:USERPROFILE ".openclaw"
$UserFile = Join-Path $ConfigDir "mnemos-user-id.txt"
$Root = Split-Path -Parent $PSScriptRoot

function Get-DotEnvValue {
  param([string]$Name)
  $envFile = Join-Path $Root ".env"
  if (-not (Test-Path $envFile)) { return $null }
  foreach ($line in Get-Content $envFile) {
    if ($line -match "^\s*#") { continue }
    if ($line -match "^\s*$Name=(.*)$") { return $Matches[1].Trim() }
  }
  return $null
}

function Assert-Ok {
  param([bool]$Condition, [string]$Message)
  if (-not $Condition) { throw $Message }
  Write-Host "OK  $Message" -ForegroundColor Green
}

Write-Host "=== MnemOS Deploy Preflight ===" -ForegroundColor Cyan

$health = Invoke-RestMethod -Uri "$MnemosUrl/health" -TimeoutSec 10
Assert-Ok ($health.status -eq "ok") "MnemOS API is healthy"

$harness = Invoke-RestMethod -Uri "$HarnessUrl/health" -TimeoutSec 10
Assert-Ok ($harness.status -eq "ok") "Visualizer harness is healthy"

$judgeUser = if (Test-Path $UserFile) { (Get-Content $UserFile -Raw).Trim() } else { Get-DotEnvValue "MNEMOS_DEFAULT_USER_ID" }
Assert-Ok (-not [string]::IsNullOrWhiteSpace($judgeUser)) "Judge user id is configured"
Assert-Ok ($judgeUser -notin @($DemoUser, "demo-openclaw", "demo-fast-student", "default_user", "user", "user_123")) "Judge user id is isolated: $judgeUser"

$judgeDump = Invoke-RestMethod -Uri "$MnemosUrl/api/memory/dump/$judgeUser" -TimeoutSec 20
$judgeText = [string]$judgeDump.response
Assert-Ok ($judgeText -match "No memories stored yet") "Judge namespace starts empty"

$demoGraph = Invoke-RestMethod -Uri "$MnemosUrl/api/graph/$DemoUser" -TimeoutSec 20
$demoCount = @($demoGraph.beliefs).Count
Assert-Ok ($demoCount -ge 8) "Demo graph is populated ($demoCount beliefs)"

$probe = openclaw mcp probe mnemos --json 2>$null | ConvertFrom-Json
Assert-Ok (@($probe.tools).Count -eq 7) "OpenClaw sees 7 MnemOS MCP tools"

Write-Host ""
Write-Host "Deployment preflight passed." -ForegroundColor Green
Write-Host "Judge user_id: $judgeUser"
Write-Host "Judge visualizer: $HarnessUrl/?user=$judgeUser"
Write-Host "Demo visualizer:  $HarnessUrl/?user=$DemoUser"
