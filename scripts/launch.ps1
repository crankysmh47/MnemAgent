# Unified MnemAgent launcher with mandatory MnemOS + OpenClaw integration
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$ConfigDir = Join-Path $env:USERPROFILE ".openclaw"

# ── Color helpers ──────────────────────────────────────────────────────────
function Write-Green  { Write-Host "$args" -ForegroundColor Green }
function Write-Yellow { Write-Host "$args" -ForegroundColor Yellow }
function Write-Red    { Write-Host "$args" -ForegroundColor Red }
function Write-Cyan   { Write-Host "$args" -ForegroundColor Cyan }

# ── Step helper ────────────────────────────────────────────────────────────
$Global:StepOk = $true
function Step($Name, $ScriptBlock) {
    Write-Host "  >> $Name ... " -NoNewline
    try {
        & $ScriptBlock
        Write-Green "OK"
    } catch {
        Write-Red "FAIL: $_"
        $Global:StepOk = $false
    }
}

# ── Prerequisite helpers ───────────────────────────────────────────────────
function Test-DockerRunning {
    $info = docker info 2>&1 | Out-String
    return $info -match "Server Version|Containers:\s+\d"
}

function Test-NodeInstalled {
    $v = node --version 2>$null
    return ($null -ne $v)
}

function Test-VenvExists {
    return (Test-Path (Join-Path $Root ".venv\Scripts\python.exe"))
}

function Test-OpenClawInstalled {
    return ($null -ne (Get-Command openclaw -ErrorAction SilentlyContinue))
}

function Wait-ForHealth {
    param([string]$Url, [int]$TimeoutSeconds = 60, [string]$Label = "service")
    $elapsed = 0
    $interval = 3
    while ($elapsed -lt $TimeoutSeconds) {
        try {
            $r = Invoke-RestMethod -Uri $Url -TimeoutSec 5
            if ($r.status -eq "ok") {
                Write-Green "  $Label ready after ${elapsed}s"
                return $true
            }
        } catch { }
        Start-Sleep -Seconds $interval
        $elapsed += $interval
    }
    Write-Red "  $Label not healthy within ${TimeoutSeconds}s"
    return $false
}

function Get-DotEnvValue([string]$Name) {
    $envFile = Join-Path $Root ".env"
    if (-not (Test-Path $envFile)) { return $null }
    foreach ($line in Get-Content $envFile) {
        if ($line -match "^\s*#") { continue }
        if ($line -match "^\s*$Name=(.*)$") { return $Matches[1].Trim() }
    }
    return $null
}

# ═══════════════════════════════════════════════════════════════════════════
Write-Cyan "╔══════════════════════════════════════════════════════════════╗"
Write-Cyan "║         MnemAgent Unified Launcher                         ║"
Write-Cyan "║   MnemOS Memory Layer + OpenClaw Integration               ║"
Write-Cyan "╚══════════════════════════════════════════════════════════════╝"
Write-Host ""

# ── 1. PREREQUISITES ──────────────────────────────────────────────────────
Write-Cyan "[1/6] Checking prerequisites..."

Step "Docker Desktop running" {
    if (-not (Test-DockerRunning)) { throw "Docker Desktop is not running" }
}

Step "Node.js installed" {
    if (-not (Test-NodeInstalled)) { throw "Node.js is not installed" }
    Write-Host "($(node --version)) " -NoNewline
}

Step "Python virtual environment" {
    if (-not (Test-VenvExists)) {
        Write-Yellow "  .venv not found, creating..."
        Push-Location $Root
        python -m venv .venv | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Failed to create .venv" }
        .\.venv\Scripts\pip.exe install -r requirements.txt --quiet 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "pip install failed" }
        Write-Green "  .venv created and packages installed"
        Pop-Location
    } else {
        Write-Host "(exists) " -NoNewline
    }
}

# ── 2. DOCKER SERVICES ────────────────────────────────────────────────────
Write-Cyan "[2/6] Starting Docker services..."
Push-Location $Root
docker compose up -d --build 2>&1 | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
if ($LASTEXITCODE -ne 0) { Write-Red "docker compose failed"; $Global:StepOk = $false }
Pop-Location

# ── 3. WAIT FOR MNEMOS ────────────────────────────────────────────────────
Write-Cyan "[3/6] Waiting for MnemOS services..."
$memOk = Wait-ForHealth -Url "http://127.0.0.1:8000/health" -Label "MnemOS memory (:8000)"
if (-not $memOk) { Write-Red "MnemOS memory service did not start"; $Global:StepOk = $false }

$mcpOk = Wait-ForHealth -Url "http://127.0.0.1:8001/health" -Label "MnemOS MCP (:8001)"
if (-not $mcpOk) { Write-Red "MnemOS MCP service did not start"; $Global:StepOk = $false }

# Wait for harness (optional, softer)
try {
    $h = Invoke-RestMethod -Uri "http://127.0.0.1:3000/health" -TimeoutSec 5
    if ($h.status -eq "ok") { Write-Green "  Harness (:3000) ready" }
} catch { Write-Yellow "  Harness (:3000) not responding yet (deployed but may need more time)" }

# ── 4. OPENCLAW INTEGRATION ───────────────────────────────────────────────
Write-Cyan "[4/6] OpenClaw integration..."
if (Test-OpenClawInstalled) {
    Write-Host "  OpenClaw: $(openclaw --version 2>$null)" -ForegroundColor Gray

    # MCP server dependencies
    Step "MCP server npm dependencies" {
        Push-Location (Join-Path $Root "mcp-server")
        npm install --silent 2>$null
        if ($LASTEXITCODE -ne 0) { throw "npm install failed" }
        Pop-Location
    }

    # Register MnemOS MCP
    Step "Register MnemOS MCP tools" {
        $McpJs = (Join-Path $Root "mcp-server/src/index.js") -replace "\\", "/"
        openclaw mcp unset mnemos 2>$null | Out-Null
        openclaw mcp add mnemos `
            --command node `
            --arg $McpJs `
            --arg "--transport" `
            --arg "stdio" `
            --env "MNEMOS_URL=http://localhost:8000" `
            --timeout 120 `
            --connect-timeout 30 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "openclaw mcp add failed" }
    }

    # Free model bundle
    $freePatch = Join-Path $Root "config\openclaw\free-models.patch.json"
    if (Test-Path $freePatch) {
        Step "Apply free model bundle" {
            Get-Content $freePatch -Raw | openclaw config patch --stdin 2>&1 | Out-Null
            openclaw config set gateway.auth.mode none 2>$null | Out-Null
        }
    }

    # Gateway management
    Step "Gateway health check" {
        $gh = openclaw gateway health 2>&1 | Out-String
        if ($gh -match "error|refused|not running") {
            Write-Yellow "  Gateway not running, starting..."
            openclaw gateway restart --force 2>&1 | Out-Null
            Start-Sleep -Seconds 5
        }
        # Re-check
        $gh2 = openclaw gateway health 2>&1 | Out-String
        if ($gh2 -match "error|refused|not running") { throw "Gateway failed to start" }
    }

    # Verify MCP probe
    Step "Verify MnemOS MCP probe" {
        $probe = openclaw mcp probe mnemos 2>&1 | Out-String
        if ($probe -notmatch "\d+ tool") { throw "MCP probe returned: $probe" }
        Write-Host "($($probe.Trim())) " -NoNewline
    }

    # Fix device scopes (if paired device exists)
    $fixScript = Join-Path $PSScriptRoot "fix-openclaw-device-scopes.ps1"
    if (Test-Path $fixScript) {
        & $fixScript 2>&1 | Out-Null
    }
} else {
    Write-Yellow "  OpenClaw not installed. Agent usage requires: npm install -g openclaw@latest"
}

# ── 5. SERVICE SUMMARY ────────────────────────────────────────────────────
Write-Cyan "[5/6] Service summary..."
Write-Host ""
Write-Host "  +------------------+--------+-------------------------------+"
Write-Host "  | Service          | Port   | Status                        |"
Write-Host "  +------------------+--------+-------------------------------+"
$services = @(
    @{ Name = "MnemOS Memory API"; Port = "8000"; Test = $memOk }
    @{ Name = "MnemOS MCP Server"; Port = "8001"; Test = $mcpOk }
    @{ Name = "Web Harness";      Port = "3000"; Test = $null }  # checked above
)
foreach ($svc in $services) {
    $statusText = if ($svc.Test -eq $true) { "Running" } elseif ($svc.Test -eq $false) { "FAILED" } else { "Unknown" }
    $color = if ($svc.Test -eq $true) { "Green" } elseif ($svc.Test -eq $false) { "Red" } else { "Yellow" }
    Write-Host ("  | {0,-16} | {1,6} | " -f $svc.Name, $svc.Port) -NoNewline
    Write-Host ("{0,-29}" -f $statusText) -ForegroundColor $color -NoNewline
    Write-Host "|"
}
Write-Host "  +------------------+--------+-------------------------------+"
if (Test-OpenClawInstalled) {
    Write-Host "  | OpenClaw Gateway | 18789  | " -NoNewline
    try {
        $gh = openclaw gateway health 2>&1 | Out-String
        if ($gh -match "error|refused|not running") { throw "down" }
        Write-Host "Running" -ForegroundColor Green -NoNewline
    } catch {
        Write-Host "Stopped" -ForegroundColor Yellow -NoNewline
    }
    Write-Host "                      |"
    Write-Host "  +------------------+--------+-------------------------------+"
}

# ── 6. QUICK-START ────────────────────────────────────────────────────────
Write-Cyan "[6/6] Quick-start commands"
Write-Host ""
Write-Host "  MnemOS Services Running:" -ForegroundColor White
if ($memOk)   { Write-Host "    o Memory API:  http://localhost:8000/docs" -ForegroundColor Gray }
if ($mcpOk)   { Write-Host "    o MCP Server:  http://localhost:8001/health" -ForegroundColor Gray }
Write-Host "    o Web Harness: http://localhost:3000" -ForegroundColor Gray
Write-Host "    o Visualizer:  http://localhost:3000/visualizer" -ForegroundColor Gray
Write-Host ""

if (Test-OpenClawInstalled) {
    Write-Host "  OpenClaw Agent Commands:" -ForegroundColor White
    $UserFile = Join-Path $ConfigDir "mnemos-user-id.txt"
    $uid = if (Test-Path $UserFile) { Get-Content $UserFile } else { "your-user-id" }
    Write-Host "    o Chat (CLI):   openclaw agent --agent main --message `"Hello`"" -ForegroundColor Gray
    Write-Host "    o Dashboard:    openclaw dashboard" -ForegroundColor Gray
    Write-Host "    o MCP Verify:   openclaw mcp probe mnemos" -ForegroundColor Gray
    Write-Host "    o MnemOS User:  $uid" -ForegroundColor Gray
    Write-Host ""
}

Write-Host "  Demo & Test:" -ForegroundColor White
Write-Host "    o Seed demo:   .\scripts\start-demo.ps1" -ForegroundColor Gray
Write-Host "    o Proof test:  .\scripts\prove-openclaw.ps1" -ForegroundColor Gray
Write-Host "    o Verify all:  .\scripts\submission-test.ps1" -ForegroundColor Gray
Write-Host ""

# ── FINAL ─────────────────────────────────────────────────────────────────
if ($Global:StepOk) {
    Write-Green "╔════════════════════════════════════════════════════════╗"
    Write-Green "║     MNEMAGENT LAUNCH COMPLETE                         ║"
    Write-Green "╚════════════════════════════════════════════════════════╝"
} else {
    Write-Yellow "╔════════════════════════════════════════════════════════╗"
    Write-Yellow "║  Launch completed with warnings.                     ║"
    Write-Yellow "║  Review messages above and fix issues.               ║"
    Write-Yellow "╚════════════════════════════════════════════════════════╝"
    exit 1
}
