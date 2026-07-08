# Full OpenClaw + MnemAgent onboarding (Windows)
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

function Ensure-MnemosUserId {
  $UserFile = Join-Path $ConfigDir "mnemos-user-id.txt"
  if (Test-Path $UserFile) {
    return (Get-Content $UserFile -Raw).Trim()
  }

  try {
    $body = '{"channel":"openclaw","sender_id":"main"}'
    $canonical = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/user/bind" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 10
    if ($canonical.user_id) {
      $canonical.user_id | Set-Content $UserFile
      Write-Host "Canonical user_id resolved: $($canonical.user_id)"
      return $canonical.user_id
    }
    throw "No user_id in response"
  } catch {
    Write-Host "WARNING: Could not resolve canonical user_id - using random GUID" -ForegroundColor Yellow
    $fallback = [guid]::NewGuid().ToString()
    $fallback | Set-Content $UserFile
    return $fallback
  }
}

Write-Host "=== OpenClaw + MnemAgent Onboarding ===" -ForegroundColor Cyan
Write-Host ""

# --------- Pre-flight warnings ---------
Write-Host "Pre-flight checks:" -ForegroundColor DarkGray

# Port 3000 clash: OpenClaw OAuth callback uses localhost:3000, but our
# visualizer also binds port 3000.  The OAuth flow will fail with
# "Cannot GET /openrouter-oauth/callback" if the visualizer is still running.
$port3000InUse = $false
try {
    $conn = [System.Net.Sockets.TcpClient]::new("127.0.0.1", 3000)
    $port3000InUse = $true
    $conn.Close()
} catch { }
if ($port3000InUse) {
    Write-Host "  WARNING: Port 3000 is in use (probably the MnemAgent visualizer container)." -ForegroundColor Yellow
    Write-Host "  If this script needs to run an OAuth login flow, the callback will FAIL" -ForegroundColor Yellow
    Write-Host "  because OpenClaw also redirects to localhost:3000.  To fix:" -ForegroundColor Yellow
    Write-Host "    1. docker compose stop openclaw-harness" -ForegroundColor DarkGray
    Write-Host "    2. Complete the login in your browser" -ForegroundColor DarkGray
    Write-Host "    3. docker compose start openclaw-harness" -ForegroundColor DarkGray
    Write-Host ""
}

# API key: OpenClaw uses its own credential store (openclaw.json), NOT .env.
# The .env file is only read by the MnemAgent Python server.  Editing .env
# without also configuring OpenClaw has no effect on the agent's model.
Write-Host "  Note: API keys go through 'openclaw' auth, not just .env" -ForegroundColor DarkGray
Write-Host "        This script handles both for you." -ForegroundColor DarkGray
Write-Host ""

$provider = Get-DotEnvValue "LLM_PROVIDER"
$apiKey = Get-DotEnvValue "LLM_API_KEY"
$baseUrl = Get-DotEnvValue "LLM_BASE_URL"
$modelId = Get-DotEnvValue "LLM_MODEL"
if (-not $apiKey) { $apiKey = Get-DotEnvValue "QWEN_API_KEY" }
if (-not $baseUrl) { $baseUrl = Get-DotEnvValue "QWEN_BASE_URL" }
if (-not $modelId) { $modelId = Get-DotEnvValue "QWEN_MODEL" }
if ($provider -eq "anthropic") {
    $anthropicKey = Get-DotEnvValue "ANTHROPIC_API_KEY"
    if ($anthropicKey) { $apiKey = $anthropicKey }
    if (-not $baseUrl) { $baseUrl = "https://api.anthropic.com" }
}
if (-not $apiKey) { throw "LLM_API_KEY missing in .env" }
if (-not $baseUrl) { $baseUrl = "https://openrouter.ai/api/v1" }

# Smart default: if the user has a DashScope key, use qwen-turbo directly
# (free OpenRouter models stall for 2---6 minutes --- unacceptable default experience).
$isAlibabaKey = ($apiKey -match "^sk-ws-") -or ($apiKey -match "^sk-[a-f0-9]" -and $apiKey -notmatch "^sk-or-v1")
$isOpenRouterKey = $apiKey -match "^sk-or-v1"
$isPlaceholderKey = $apiKey -match "^sk-or-v1-xxxxxxxxxxxx" -or $apiKey -match "^sk-xxxxxxxxxxxx"

if ($isPlaceholderKey) {
    Write-Host "WARNING: LLM_API_KEY is still the placeholder value." -ForegroundColor Yellow
    Write-Host "  Edit .env and replace LLM_API_KEY with your real API key, then re-run this script." -ForegroundColor Yellow
    Write-Host "  Get a free key at https://openrouter.ai/keys or https://dashscope.aliyuncs.com" -ForegroundColor Yellow
    throw "Placeholder API key --- add your real key to .env"
}

if ($provider -eq "anthropic") {
    $onboardModel = if ($modelId) { $modelId } else { "claude-sonnet-4-20250514" }
    $providerId = "anthropic"
    Write-Host "LLM: Anthropic $onboardModel via $baseUrl"
} elseif ($isAlibabaKey) {
    # Use DashScope directly --- fast, reliable, hackathon target
    if (-not $baseUrl) { $baseUrl = "https://dashscope.aliyuncs.com/compatible-mode/v1" }
    if (-not $modelId -or $modelId -match ":free$") {
        $modelId = "qwen-turbo"
    }
    $onboardModel = $modelId
    $providerId = "dashscope"
    Write-Host "LLM: Alibaba Qwen $modelId via $baseUrl"
} elseif ($isOpenRouterKey) {
    # OpenRouter key --- use the model from .env, fall back to free bundle with warning
    $onboardModel = if ($modelId -and $modelId -notmatch ":free$") { $modelId } else { "openrouter/free" }
    $providerId = "openrouter"
    Write-Host "LLM: OpenRouter $onboardModel"
    if ($onboardModel -eq "openrouter/free") {
        Write-Host "  WARNING: Free models may stall for 2---6 minutes per reply." -ForegroundColor Yellow
        Write-Host "  For a usable experience, set LLM_MODEL=qwen-flash and use a DashScope key." -ForegroundColor Yellow
    }
} else {
    # Unknown key format --- try as custom provider
    $onboardModel = if ($modelId) { $modelId } else { "qwen-turbo" }
    $providerId = "custom"
    Write-Host "LLM: Custom provider --- $onboardModel"
}
$freePatch = Join-Path $Root "config\openclaw\free-models.patch.json"

# MnemAgent stack
Write-Host "Starting MnemAgent Docker stack..."
Push-Location $Root
docker compose up -d --build | Out-Null
Pop-Location
for ($i = 0; $i -lt 40; $i++) {
  try {
    $h = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 3
    if ($h.status -eq "ok") { Start-Sleep -Seconds 3; break }
  } catch { Start-Sleep -Seconds 2 }
}

$MnemosUserId = Ensure-MnemosUserId

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
        env = @{
          MNEMOS_URL = "http://localhost:8000"
          MNEMOS_DEFAULT_USER_ID = $MnemosUserId
        }
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
    --custom-provider-id $providerId `
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
if ((-not $isAlibabaKey) -and (Test-Path $freePatch)) {
  Get-Content $freePatch -Raw | openclaw config patch --stdin
}
openclaw config set gateway.auth.mode none 2>$null
openclaw plugins disable memory-core 2>$null | Out-Null
if ($isAlibabaKey) {
  openclaw config set agents.defaults.model.primary "dashscope/qwen-flash" 2>$null | Out-Null
}

# MnemAgent MCP (stdio -> spawns mcp-server -> MnemAgent :8000)
# Try mcp set first (current OpenClaw CLI), fall back to mcp add (older versions).
# If both fail the agent has NO memory tools --- it will fall back to its broken
# built-in index and leak workspace demo data as real user memory.  We must
# surface a clear error here rather than let the user continue blind.
Write-Host "Registering MnemAgent MCP..."
openclaw mcp unset mnemos 2>$null | Out-Null

$mcpSetJson = '{"command":"node","args":["' + $McpJs + '","--transport","stdio"],"env":{"MNEMOS_URL":"http://localhost:8000","MNEMOS_DEFAULT_USER_ID":"' + $MnemosUserId + '"}}'
openclaw mcp set mnemos $mcpSetJson 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  mcp set unavailable --- trying mcp add (older OpenClaw)" -ForegroundColor DarkGray
    openclaw mcp add mnemos `
      --command node `
      --arg $McpJs `
      --arg "--transport" `
      --arg "stdio" `
      --env "MNEMOS_URL=http://localhost:8000" `
      --env "MNEMOS_DEFAULT_USER_ID=$MnemosUserId" `
      --timeout 120 `
      --connect-timeout 30
}
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Could not register MnemAgent MCP tools." -ForegroundColor Red
    Write-Host "Without these tools the agent CANNOT use memory --- it will give WRONG answers." -ForegroundColor Red
    Write-Host "Manual fix:  openclaw mcp set mnemos '$mcpSetJson'" -ForegroundColor Yellow
    Write-Host "Then verify:  openclaw mcp probe mnemos" -ForegroundColor Yellow
    throw "MCP registration failed --- memory tools are required"
}

$UserFile = Join-Path $ConfigDir "mnemos-user-id.txt"

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
Write-Host "  MnemAgent user:   $(Get-Content $UserFile)"
Write-Host ""
Write-Host "Architecture:"
Write-Host "  You -> OpenClaw Gateway (:18789) -> Agent + mnemos MCP tools"
Write-Host "       -> mcp-server (stdio) -> MnemAgent API (:8000) -> SQLite memory"
