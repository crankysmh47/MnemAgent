# MnemAgent + OpenClaw setup (Windows)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Harness = $PSScriptRoot
$ConfigDir = if ($env:OPENCLAW_CONFIG_DIR) { $env:OPENCLAW_CONFIG_DIR } else { Join-Path $env:USERPROFILE ".openclaw" }

Write-Host "=== MnemAgent OpenClaw Setup ===" -ForegroundColor Cyan

# 1. OpenClaw CLI
$openclaw = Get-Command openclaw -ErrorAction SilentlyContinue
if (-not $openclaw) {
  Write-Host "OpenClaw not found. Install with: npm install -g openclaw" -ForegroundColor Yellow
  Write-Host "Or see https://docs.qwencloud.com/coding-plan/tools/openclaw"
} else {
  openclaw --version
}

# 2. Config directory
New-Item -ItemType Directory -Force -Path $ConfigDir | Out-Null
Copy-Item (Join-Path $Harness "openclaw-config\mnemos.config.json") (Join-Path $ConfigDir "mnemos.config.json") -Force
Write-Host "Copied mnemos.config.json -> $ConfigDir"

# 3. Shared user id for TUI + web UI
$UserFile = Join-Path $ConfigDir "mnemos-user-id.txt"
if (-not (Test-Path $UserFile)) {
  # Resolve canonical user_id from MnemAgent so visualizer and agent share the same ID
  try {
    $body = '{"channel":"openclaw","sender_id":"main"}'
    $canonical = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/user/bind" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 10
    if ($canonical.user_id) {
      $canonical.user_id | Set-Content $UserFile
    } else {
      throw "No user_id in response"
    }
  } catch {
    [guid]::NewGuid().ToString() | Set-Content $UserFile
  }
}
$UserId = Get-Content $UserFile
Write-Host "Shared user_id: $UserId (use in chat UI localStorage: mnemos_user_id)"

# 4. npm install
Push-Location (Join-Path $Harness "mcp-adapter")
npm install
Pop-Location
Push-Location $Harness
npm install
Pop-Location

# 5. Start services (background jobs)
Write-Host "Starting MnemAgent backend on :8000..."
Start-Process -FilePath "$Root\.venv\Scripts\uvicorn.exe" -ArgumentList "main:app","--host","0.0.0.0","--port","8000" -WorkingDirectory (Join-Path $Root "mcp-memory-server\src") -WindowStyle Hidden

Start-Sleep -Seconds 2
Write-Host "Starting MCP adapter on :8001..."
Start-Process -FilePath "node" -ArgumentList "server.js" -WorkingDirectory (Join-Path $Harness "mcp-adapter") -WindowStyle Hidden

Start-Sleep -Seconds 1
Write-Host "Starting harness UI on :3000..."
Start-Process -FilePath "node" -ArgumentList "src\index.js" -WorkingDirectory $Harness -WindowStyle Hidden

Write-Host ""
Write-Host "Services:" -ForegroundColor Green
Write-Host "  Chat UI:      http://localhost:3000"
Write-Host "  Visualizer:   http://localhost:3000/visualizer"
Write-Host "  MnemAgent API:   http://localhost:8000"
Write-Host "  MCP Adapter:  http://localhost:8001"
Write-Host "  OpenClaw TUI: openclaw gateway && openclaw tui"
Write-Host ""
Write-Host "Set localStorage mnemos_user_id to $UserId in browser for shared memory."
