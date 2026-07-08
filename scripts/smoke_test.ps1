# MnemAgent end-to-end smoke test
$ErrorActionPreference = "Stop"
$base = Split-Path -Parent $PSScriptRoot

Write-Host "=== MnemAgent Smoke Test ===" -ForegroundColor Cyan

function Test-Endpoint($name, $url) {
    try {
        $r = Invoke-RestMethod -Uri $url -TimeoutSec 10
        Write-Host "[OK] $name" -ForegroundColor Green
        return $r
    } catch {
        Write-Host "[FAIL] $name - $_" -ForegroundColor Red
        exit 1
    }
}

Test-Endpoint "MnemAgent health" "http://127.0.0.1:8000/health"
Test-Endpoint "MCP adapter health" "http://127.0.0.1:8001/health"
$h = Test-Endpoint "Harness health" "http://127.0.0.1:3000/health"
Test-Endpoint "Graph API" "http://127.0.0.1:3000/api/graph/smoke-user"
Test-Endpoint "Metrics API" "http://127.0.0.1:3000/api/metrics/smoke-user"

$uid = "smoke-" + [guid]::NewGuid().ToString().Substring(0, 8)
Write-Host "Testing chat as user $uid ..."

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/memory/store" -Method POST -ContentType "application/json" -Body (@{
    user_id = $uid
    entity = "backend_language"
    relation = "prefers"
    value = "python"
    category = "preference"
    conviction = 0.95
} | ConvertTo-Json) | Out-Null

$mem = Invoke-RestMethod -Uri "http://127.0.0.1:8000/chat" -Method POST -ContentType "application/json" -Body (@{
    user_id = $uid
    session_id = "s1"
    message = "/memory"
} | ConvertTo-Json)
if ($mem.response -notmatch "python") {
    Write-Host "[FAIL] Memory store/recall" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Memory store + /memory dump" -ForegroundColor Green

$mcp = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/memory/search/$uid?query=python&top_k=3"
if (-not $mcp.results) {
    Write-Host "[FAIL] Memory search returned no results" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Memory search API" -ForegroundColor Green

$chat = Invoke-RestMethod -Uri "http://127.0.0.1:3000/chat" -Method POST -ContentType "application/json" -Body (@{
    user_id = $uid
    session_id = "s2"
    message = "What language do we prefer for backend?"
} | ConvertTo-Json -Depth 3)
Write-Host "[OK] Harness chat proxy" -ForegroundColor Green
Write-Host "Sample response: $($chat.response.Substring(0, [Math]::Min(120, $chat.response.Length)))..."
Write-Host "`nAll smoke tests passed." -ForegroundColor Green
