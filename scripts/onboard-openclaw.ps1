# Full OpenClaw + MnemOS onboarding (Windows)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$ConfigDir = Join-Path $env:USERPROFILE ".openclaw"
$WorkspaceDir = Join-Path $ConfigDir "workspace"
$McpJs = (Join-Path $Root "mcp-server\src\index.js") -replace "\\", "/"

function Get-DotEnvValue([string]$Name) {
  $envFile = Join-Path $Root ".env"
  if (-not (Test-Path $envFile)) { return $null }
  foreach ($line in Get-Content $envFile) {
    if ($line -match "^\s*#") { continue }
    if ($line -match "^\s*$Name=(.*)$") { return $Matches[1].Trim() }
  }
  return $null
}

Write-Host "=== OpenClaw + MnemOS Onboarding ===" -ForegroundColor Cyan

$apiKey = Get-DotEnvValue "QWEN_API_KEY"
$baseUrl = Get-DotEnvValue "QWEN_BASE_URL"
$modelId = Get-DotEnvValue "QWEN_MODEL"
if (-not $apiKey) { throw "QWEN_API_KEY missing in .env" }
if (-not $baseUrl) { $baseUrl = "https://openrouter.ai/api/v1" }
# OpenClaw: free router + fallbacks (see config/openclaw/free-models.patch.json)
$onboardModel = "openrouter/free"
$freePatch = Join-Path $Root "config\openclaw\free-models.patch.json"

Write-Host "LLM: OpenRouter free bundle via $baseUrl"

# MnemOS stack
Write-Host "Starting MnemOS Docker stack..."
Push-Location $Root
docker compose up -d --build | Out-Null
Pop-Location
for ($i = 0; $i -lt 40; $i++) {
  try {
    $h = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 3
    if ($h.status -eq "ok") { Start-Sleep -Seconds 3; break }
  } catch { Start-Sleep -Seconds 2 }
}

Push-Location (Join-Path $Root "mcp-server")
npm install --silent 2>$null
Pop-Location

function Write-Utf8JsonFile([string]$Path, $Object, [int]$Depth = 6) {
  $utf8NoBom = New-Object System.Text.UTF8Encoding $false
  $json = $Object | ConvertTo-Json -Depth $Depth
  [System.IO.File]::WriteAllText($Path, $json, $utf8NoBom)
}

# Workspace
New-Item -ItemType Directory -Force -Path (Join-Path $WorkspaceDir "skills\mnemos-memory") | Out-Null
Copy-Item (Join-Path $Root "config\workspace\*") $WorkspaceDir -Recurse -Force
$mcpWs = @{
  mcp = @{
    servers = @{
      mnemos = @{
        command = "node"
        args = @($McpJs, "--transport", "stdio")
        env = @{ MNEMOS_URL = "http://localhost:8000" }
      }
    }
  }
}
Write-Utf8JsonFile (Join-Path $WorkspaceDir ".mcp.json") $mcpWs 6

# OpenClaw onboard
$configFile = Join-Path $ConfigDir "openclaw.json"
if (-not (Test-Path $configFile)) {
  Write-Host "Running openclaw onboard..."
  openclaw onboard `
    --non-interactive `
    --accept-risk `
    --flow quickstart `
    --auth-choice custom-api-key `
    --custom-api-key $apiKey `
    --custom-base-url $baseUrl `
    --custom-model-id $onboardModel `
    --custom-compatibility openai `
    --custom-provider-id openrouter `
    --skip-channels `
    --skip-skills `
    --skip-search `
    --skip-hooks `
    --install-daemon `
    --gateway-bind loopback `
    --gateway-port 18789
  if ($LASTEXITCODE -ne 0) { throw "openclaw onboard failed" }
} else {
  Write-Host "openclaw.json exists - skipping onboard"
}

# Free model bundle + local gateway auth
if (Test-Path $freePatch) {
  Get-Content $freePatch -Raw | openclaw config patch --stdin
}
openclaw config set gateway.auth.mode none 2>$null

# MnemOS MCP (stdio -> spawns mcp-server -> MnemOS :8000)
Write-Host "Registering MnemOS MCP..."
openclaw mcp unset mnemos 2>$null | Out-Null
openclaw mcp add mnemos `
  --command node `
  --arg $McpJs `
  --arg "--transport" `
  --arg "stdio" `
  --env "MNEMOS_URL=http://localhost:8000" `
  --timeout 120 `
  --connect-timeout 30
if ($LASTEXITCODE -ne 0) { throw "openclaw mcp add mnemos failed" }

$UserFile = Join-Path $ConfigDir "mnemos-user-id.txt"
if (-not (Test-Path $UserFile)) {
  [guid]::NewGuid().ToString() | Set-Content $UserFile
}

openclaw gateway restart --force | Out-Null
Start-Sleep -Seconds 5

# First agent connect may create CLI pairing with read-only scopes; fix that
& (Join-Path $PSScriptRoot "fix-openclaw-device-scopes.ps1")
openclaw gateway restart --force | Out-Null
Start-Sleep -Seconds 4

Write-Host ""
openclaw gateway health
openclaw mcp list
openclaw mcp probe mnemos

Write-Host ""
Write-Host "=== OpenClaw Ready ===" -ForegroundColor Green
Write-Host "  Dashboard:     openclaw dashboard"
Write-Host "  Chat (CLI):    openclaw agent --agent main --message `"Hello`""
Write-Host "  Proof script:  .\scripts\prove-openclaw.ps1"
Write-Host "  MnemOS user:   $(Get-Content $UserFile)"
Write-Host ""
Write-Host "Architecture:"
Write-Host "  You -> OpenClaw Gateway (:18789) -> Agent + mnemos MCP tools"
Write-Host "       -> mcp-server (stdio) -> MnemOS API (:8000) -> SQLite memory"
