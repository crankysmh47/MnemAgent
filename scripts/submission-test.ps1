# Complete submission verification for MnemAgent project
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

# ── Report file ────────────────────────────────────────────────────────────
$Timestamp = Get-Date -Format "yyyyMMddTHHmmss"
$ReportDir = Join-Path $Root "eval\results"
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
$ReportFile = Join-Path $ReportDir "submission_check_${Timestamp}.txt"

# ── Color helpers ──────────────────────────────────────────────────────────
function Write-Green  { Write-Host "$args" -ForegroundColor Green }
function Write-Yellow { Write-Host "$args" -ForegroundColor Yellow }
function Write-Red    { Write-Host "$args" -ForegroundColor Red }
function Write-Cyan   { Write-Host "$args" -ForegroundColor Cyan }

# ── Test tracking ─────────────────────────────────────────────────────────
$Global:Passed = 0
$Global:Failed = 0
$Global:Skipped = 0
$Global:Failures = @()

# Resolve Python executable
$PythonExe = if (Test-Path (Join-Path $Root ".venv\Scripts\python.exe")) {
    Join-Path $Root ".venv\Scripts\python.exe"
} else { "python" }

# ── Test runner ────────────────────────────────────────────────────────────
function Run-Check {
    param(
        [string]$Name,
        [ScriptBlock]$ScriptBlock,
        [switch]$IsWarning
    )
    Write-Host "  [$Name] ... " -NoNewline
    try {
        & $ScriptBlock
        Write-Green " PASS"
        $Global:Passed++
    } catch {
        $msg = $_.Exception.Message
        if ($IsWarning) {
            Write-Yellow " SKIP: $msg"
            $Global:Skipped++
        } else {
            Write-Red " FAIL: $msg"
            $Global:Failed++
            $Global:Failures += "[$Name] $msg"
        }
    }
}

function Write-Section {
    param([string]$Title)
    Write-Host ""
    Write-Cyan "───────────────────────────────────────────────────────"
    Write-Cyan "  $Title"
    Write-Cyan "───────────────────────────────────────────────────────"
}

function Write-Report {
    param([string]$Text)
    Add-Content -Path $ReportFile -Value $Text -Encoding UTF8
}

# ═══════════════════════════════════════════════════════════════════════════
Write-Cyan "╔══════════════════════════════════════════════════════════════╗"
Write-Cyan "║     MnemAgent Submission Verification                       ║"
Write-Cyan "╚══════════════════════════════════════════════════════════════╝"

Write-Report "# MnemAgent Submission Check - $Timestamp"
Write-Report ""
Write-Report "## Environment"
Write-Report "- Date: $Timestamp"
Write-Report "- Host: $env:COMPUTERNAME"
Write-Report "- PowerShell: $($PSVersionTable.PSVersion)"
Write-Report ""

# ── 1. DOCKER SERVICES ────────────────────────────────────────────────────
Write-Section "1. Docker Services"

Run-Check "Docker running" {
    $info = docker info 2>&1 | Out-String
    if ($info -notmatch "Server Version") { throw "Docker Desktop not running" }
}

Run-Check "MnemOS memory (:8000)" {
    $r = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 5
    if ($r.status -ne "ok") { throw "status: $($r.status)" }
}

Run-Check "MnemOS MCP (:8001)" {
    $r = Invoke-RestMethod -Uri "http://127.0.0.1:8001/health" -TimeoutSec 5
    if ($r.status -ne "ok") { throw "status: $($r.status)" }
}

Run-Check "Web Harness (:3000)" -IsWarning {
    $r = Invoke-RestMethod -Uri "http://127.0.0.1:3000/health" -TimeoutSec 5
    if ($r.status -ne "ok") { throw "status: $($r.status)" }
}

# ── 2. UNIT TESTS ─────────────────────────────────────────────────────────
Write-Section "2. Unit Tests (pytest)"
Write-Host "  Running all unit tests (128 expected)..."
Write-Host ""

$unitOut = ""
$unitExit = 0
Push-Location $Root
try {
    $unitOut = & $PythonExe -m pytest tests/ -v --tb=short 2>&1 | Out-String
    $unitExit = $LASTEXITCODE
} catch {
    $unitExit = 1
    $unitOut = $_.Exception.Message
}
Pop-Location

# Parse the summary line
$unitPass = 0; $unitFail = 0; $unitSkip = 0
if ($unitOut -match "(\d+) passed") { $unitPass = [int]$Matches[1] }
if ($unitOut -match "(\d+) failed") { $unitFail = [int]$Matches[1] }
if ($unitOut -match "(\d+) skipped") { $unitSkip = [int]$Matches[1] }

if ($unitExit -eq 0) {
    Write-Green "  PASS: $unitPass passed, $unitSkip skipped"
    $Global:Passed++
} else {
    Write-Red "  FAIL: $unitPass passed, $unitFail failed, $unitSkip skipped"
    $Global:Failed++
    $Global:Failures += "[Unit Tests] $unitPass passed, $unitFail failed"
}
Write-Report ""
Write-Report "## Unit Tests"
Write-Report "- Status: $(if ($unitExit -eq 0) {'PASS'} else {'FAIL'})"
Write-Report "- Passed: $unitPass | Failed: $unitFail | Skipped: $unitSkip"

# ── 3. INTEGRATION TESTS ──────────────────────────────────────────────────
Write-Section "3. Integration Tests"
Write-Host "  Running integration tests..."
Write-Host ""

$intOut = ""
$intExit = 0
Push-Location $Root
try {
    $intOut = & $PythonExe -m pytest tests/test_integration.py -v --tb=short 2>&1 | Out-String
    $intExit = $LASTEXITCODE
} catch {
    $intExit = 1
    $intOut = $_.Exception.Message
}
Pop-Location

$intPass = 0; $intFail = 0; $intSkip = 0
if ($intOut -match "(\d+) passed") { $intPass = [int]$Matches[1] }
if ($intOut -match "(\d+) failed") { $intFail = [int]$Matches[1] }
if ($intOut -match "(\d+) skipped") { $intSkip = [int]$Matches[1] }

if ($intExit -eq 0) {
    Write-Green "  PASS: $intPass passed"
    $Global:Passed++
} else {
    Write-Red "  FAIL: $intPass passed, $intFail failed"
    $Global:Failed++
    $Global:Failures += "[Integration Tests] $intPass passed, $intFail failed"
}
Write-Report ""
Write-Report "## Integration Tests"
Write-Report "- Status: $(if ($intExit -eq 0) {'PASS'} else {'FAIL'})"
Write-Report "- Passed: $intPass | Failed: $intFail | Skipped: $intSkip"

# ── 4. EVAL FRAMEWORK ─────────────────────────────────────────────────────
Write-Section "4. Eval Framework (dry-run)"

# Stderr capture note: run_benchmark writes to stdout only in dry-run mode
$evalDryRunExit = 0
$evalDryRunOut = ""
Push-Location $Root
try {
    $evalDryRunOut = & $PythonExe -m eval.run_benchmark --dry-run --mode both 2>&1 | Out-String
    $evalDryRunExit = $LASTEXITCODE
} catch {
    $evalDryRunExit = 1
    $evalDryRunOut = $_.Exception.Message
}
Pop-Location

if ($evalDryRunExit -eq 0) {
    Write-Green "  PASS: Benchmark dry-run completed (both modes)"
    $Global:Passed++
} else {
    Write-Red "  FAIL: Benchmark dry-run failed (exit code $evalDryRunExit)"
    $Global:Failed++
    $Global:Failures += "[Eval Benchmark dry-run] exit code $evalDryRunExit"
}

# Also extract scores if available
if ($evalDryRunOut -match "MnemOS average score:\s*([0-9.]+%)") {
    Write-Host "    MnemOS score: $($Matches[1])" -ForegroundColor Gray
}
if ($evalDryRunOut -match "Baseline average score:\s*([0-9.]+%)") {
    Write-Host "    Baseline score: $($Matches[1])" -ForegroundColor Gray
}
if ($evalDryRunOut -match "Report written to (.+)") {
    Write-Host "    Report: $($Matches[1])" -ForegroundColor Gray
}
Write-Report ""
Write-Report "## Eval Benchmark (dry-run)"
Write-Report "- Status: $(if ($evalDryRunExit -eq 0) {'PASS'} else {'FAIL'})"

# ── 5. AGENTIC BENCHMARK ──────────────────────────────────────────────────
Write-Section "5. Agentic Benchmark (dry-run)"

$agenticExit = 0
$agenticOut = ""
Push-Location $Root
try {
    $agenticOut = & $PythonExe -m eval.run_agentic_benchmark --dry-run 2>&1 | Out-String
    $agenticExit = $LASTEXITCODE
} catch {
    $agenticExit = 1
    $agenticOut = $_.Exception.Message
}
Pop-Location

if ($agenticExit -eq 0) {
    Write-Green "  PASS: Agentic benchmark dry-run completed"
    $Global:Passed++
} else {
    Write-Red "  FAIL: Agentic benchmark dry-run failed (exit code $agenticExit)"
    $Global:Failed++
    $Global:Failures += "[Agentic Benchmark dry-run] exit code $agenticExit"
}

# Extract growth metrics if available
if ($agenticOut -match "Behavior advantage growth:\s*([+-]?[0-9.]+)") {
    Write-Host "    Behavior advantage growth: $($Matches[1])" -ForegroundColor Gray
}
if ($agenticOut -match "Report written to (.+)") {
    Write-Host "    Report: $($Matches[1])" -ForegroundColor Gray
}
Write-Report ""
Write-Report "## Agentic Benchmark (dry-run)"
Write-Report "- Status: $(if ($agenticExit -eq 0) {'PASS'} else {'FAIL'})"

# ── 6. OPENCLAW CHECKS ───────────────────────────────────────────────────
Write-Section "6. OpenClaw Integration"

$openclawInstalled = $null -ne (Get-Command openclaw -ErrorAction SilentlyContinue)
if ($openclawInstalled) {
    Run-Check "OpenClaw gateway health" {
        $gh = openclaw gateway health 2>&1 | Out-String
        if ($gh -match "error|refused|not running") { throw "Gateway not healthy" }
    }

    Run-Check "OpenClaw MCP probe (mnemos)" -IsWarning {
        $probe = openclaw mcp probe mnemos 2>&1 | Out-String
        if ($probe -notmatch "\d+ tool") { throw "mnemos MCP not registered" }
        Write-Host "($($probe.Trim())) " -NoNewline
    }
} else {
    Write-Yellow "  OpenClaw not installed — skipping gateway/MCP checks"
    $Global:Skipped += 2
}
Write-Report ""
Write-Report "## OpenClaw Integration"
Write-Report "- OpenClaw installed: $openclawInstalled"

# ── 7. MEMORY API SMOKE TEST ──────────────────────────────────────────────
Write-Section "7. Memory API Smoke Test"

$smokeUid = "submission-check-" + [guid]::NewGuid().ToString().Substring(0, 8)

Run-Check "Store a memory" {
    $body = @{
        user_id = $smokeUid
        entity = "test_entity"
        relation = "is"
        value = "submission_check_ok"
        category = "test"
        conviction = 1.0
    } | ConvertTo-Json
    $r = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/memory/store" -Method POST `
        -ContentType "application/json" -Body $body -TimeoutSec 10
    if (-not $r.stored) { throw "not stored" }
}

Run-Check "Search memories" {
    $searchUrl = "http://127.0.0.1:8000/api/memory/search/$([uri]::EscapeDataString($smokeUid))?query=test&top_k=5"
    $r = Invoke-RestMethod -Uri $searchUrl -TimeoutSec 10
    if ($r.results.Count -lt 1) { throw "no results" }
}

Run-Check "Dump memories" {
    $r = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/memory/dump/$smokeUid" -TimeoutSec 10
    if ($r.response -notmatch "submission_check_ok") { throw "value not in dump" }
}
Write-Report ""
Write-Report "## Memory API Smoke"
Write-Report "- User ID: $smokeUid"

# ═══════════════════════════════════════════════════════════════════════════
# SUMMARY
Write-Cyan "═══════════════════════════════════════════════════════════════"
Write-Cyan "  SUMMARY"
Write-Cyan "═══════════════════════════════════════════════════════════════"
Write-Host ""
Write-Host "  Passed:  " -NoNewline; Write-Green "$($Global:Passed)"
Write-Host "  Failed:  " -NoNewline; Write-Red "$($Global:Failed)"
Write-Host "  Skipped: " -NoNewline; Write-Yellow "$($Global:Skipped)"

if ($Global:Failures.Count -gt 0) {
    Write-Host ""
    Write-Yellow "  Failed checks:"
    foreach ($f in $Global:Failures) {
        Write-Host "    - $f" -ForegroundColor Yellow
    }
}

Write-Host ""

Write-Report ""
Write-Report "## Summary"
Write-Report "- Passed: $($Global:Passed) | Failed: $($Global:Failed) | Skipped: $($Global:Skipped)"
if ($Global:Failures.Count -gt 0) {
    Write-Report "- Failures:"
    foreach ($f in $Global:Failures) {
        Write-Report "  - $f"
    }
}

if ($Global:Failed -eq 0) {
    Write-Green "╔════════════════════════════════════════════════════════╗"
    Write-Green "║     READY FOR SUBMISSION                              ║"
    Write-Green "║     All checks passed.                                ║"
    Write-Green "╚════════════════════════════════════════════════════════╝"
    Write-Report "- Verdict: READY FOR SUBMISSION"
    Write-Report "- All checks passed."
    $exitCode = 0
} else {
    Write-Red "╔════════════════════════════════════════════════════════╗"
    Write-Red "║     ISSUES FOUND                                      ║"
    Write-Red "║     $($Global:Failed) check(s) failed. Review above.             ║"
    Write-Red "╚════════════════════════════════════════════════════════╝"
    Write-Report "- Verdict: ISSUES FOUND"
    Write-Report "- $($Global:Failed) check(s) failed."
    $exitCode = 1
}

Write-Host ""
Write-Host "  Report saved to: " -NoNewline
Write-Cyan "$ReportFile"
Write-Report ""

exit $exitCode
