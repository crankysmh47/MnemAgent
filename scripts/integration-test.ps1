# Full MnemOS + OpenClaw integration smoke test
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Failed = 0

function Test-Step($Name, $ScriptBlock) {
  Write-Host "[$Name]..." -NoNewline
  try {
    & $ScriptBlock
    Write-Host " OK" -ForegroundColor Green
  } catch {
    Write-Host " FAIL: $_" -ForegroundColor Red
    $script:Failed++
  }
}

Write-Host "=== MnemOS Integration Test ===" -ForegroundColor Cyan

Test-Step "MnemOS health" {
  $r = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 5
  if ($r.status -ne "ok") { throw "bad status" }
}

Test-Step "MCP server health" {
  $r = Invoke-RestMethod -Uri "http://127.0.0.1:8001/health" -TimeoutSec 5
  if ($r.status -ne "ok") { throw "bad status" }
}

Test-Step "Harness health" {
  $r = Invoke-RestMethod -Uri "http://127.0.0.1:3000/health" -TimeoutSec 5
  if ($r.status -ne "ok") { throw "bad status" }
}

$uid = "integration-test-" + [guid]::NewGuid().ToString().Substring(0, 8)

Test-Step "User bind API" {
  $body = @{ channel = "webchat"; sender_id = "test-sender"; display_name = "Tester" } | ConvertTo-Json
  $r = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/user/bind" -Method POST -ContentType "application/json" -Body $body
  if (-not $r.user_id) { throw "no user_id" }
  $script:uid = $r.user_id
}

Test-Step "Memory store API" {
  $body = @{
    user_id = $uid
    entity = "backend_language"
    relation = "prefers"
    value = "Python"
    category = "preference"
    conviction = 1.0
  } | ConvertTo-Json
  $r = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/memory/store" -Method POST -ContentType "application/json" -Body $body
  if (-not $r.stored) { throw "not stored" }
}

Test-Step "Memory search API" {
  $searchUrl = "http://127.0.0.1:8000/api/memory/search/$([uri]::EscapeDataString($uid))?query=Python&top_k=5"
  $r = Invoke-RestMethod -Uri $searchUrl
  if ($r.results.Count -lt 1) { throw "no results" }
}

Test-Step "Memory dump API" {
  $r = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/memory/dump/$uid"
  if ($r.response -notmatch "Python") { throw "Python not in dump" }
}

Test-Step "Harness chat" {
  $body = @{ user_id = $uid; session_id = "int-test"; message = "Hello" } | ConvertTo-Json
  $r = Invoke-RestMethod -Uri "http://127.0.0.1:3000/chat" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 120
  if (-not $r.response) { throw "empty response" }
}

Test-Step "Bare JSON strip (unit)" {
  Push-Location $Root
  $out = .\.venv\Scripts\python.exe -m pytest tests/test_qwen_client.py::test_strip_memory_tags_bare_json -q 2>&1
  Pop-Location
  if ($LASTEXITCODE -ne 0) { throw "pytest failed" }
}

Test-Step "Agentic eval dry-run" {
  Push-Location $Root
  $out = .\.venv\Scripts\python.exe -m eval.run_agentic_benchmark --dry-run --mode both 2>&1
  Pop-Location
  if ($LASTEXITCODE -ne 0) { throw "benchmark failed" }
}

Write-Host ""
if ($Failed -eq 0) {
  Write-Host "All integration tests passed." -ForegroundColor Green
  exit 0
} else {
  Write-Host "$Failed test(s) failed." -ForegroundColor Red
  exit 1
}
