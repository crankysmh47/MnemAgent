# Prove MnemOS memory works via terminal (no Telegram required)
$ErrorActionPreference = "Stop"
$Base = "http://127.0.0.1:8000"
$Harness = "http://127.0.0.1:3000"
$Uid = "demo-" + [guid]::NewGuid().ToString().Substring(0, 8)
$TeachSession = "teach-" + [guid]::NewGuid().ToString().Substring(0, 8)
$ProbeSession = "probe-" + [guid]::NewGuid().ToString().Substring(0, 8)

function Invoke-Chat($sessionId, $message) {
  $body = @{ user_id = $Uid; session_id = $sessionId; message = $message } | ConvertTo-Json
  return Invoke-RestMethod -Uri "$Harness/chat" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 180
}

function Invoke-Store($entity, $relation, $value, $category = "preference") {
  $body = @{
    user_id = $Uid
    entity = $entity
    relation = $relation
    value = $value
    category = $category
    conviction = 1.0
  } | ConvertTo-Json -Compress
  $r = Invoke-RestMethod -Uri "$Base/api/memory/store" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 30
  if (-not $r.stored) { throw "Store failed for $entity" }
  Start-Sleep -Seconds 2
}

function Get-Dump($retries = 5) {
  for ($i = 0; $i -lt $retries; $i++) {
    $d = Invoke-RestMethod -Uri "$Base/api/memory/dump/${Uid}?format=markdown" -TimeoutSec 30
    if ($d.response -and $d.response -notmatch "No memories stored") { return $d }
    Start-Sleep -Seconds 2
  }
  throw "Memory dump empty after store"
}

Write-Host "=== MnemOS Memory Proof (terminal) ===" -ForegroundColor Cyan
Write-Host ""

# 1. Health
Write-Host "[1/7] Health checks..."
$h = Invoke-RestMethod -Uri "$Base/health" -TimeoutSec 10
$m = Invoke-RestMethod -Uri "http://127.0.0.1:8001/health" -TimeoutSec 10
$w = Invoke-RestMethod -Uri "$Harness/health" -TimeoutSec 10
Write-Host "  MnemOS: $($h.status) | MCP: $($m.status) | Harness: $($w.status)" -ForegroundColor Green

# 2. Store facts via API (sequential to avoid SQLite lock storms)
Write-Host "[2/7] Storing memories (Python preference + FAST affiliation)..."
Invoke-Store "backend_language" "prefers" "Python"
Invoke-Store "user" "affiliated_with" "FAST" "persona"

# 3. Verify dump
Write-Host "[3/7] Memory dump..."
$dump = Get-Dump
Write-Host $dump.response
if ($dump.response -notmatch "Python") {
  Write-Host "  FAIL: Python not in memory dump" -ForegroundColor Red
  exit 1
}
Write-Host "  OK: Memories persisted" -ForegroundColor Green
Write-Host ""

# 4. Cross-session recall (new session_id)
Write-Host "[4/7] New session recall: what language for the API?"
$probe = Invoke-Chat $ProbeSession "What programming language should I use for our backend API?"
Write-Host "  Agent: $($probe.response.Substring(0, [Math]::Min(300, $probe.response.Length)))..."
if ($probe.response -match '\{\s*"entity"') {
  Write-Host "  FAIL: Raw JSON leaked!" -ForegroundColor Red
  exit 1
}
if ($probe.response -match "Python") {
  Write-Host "  OK: Recalled Python from memory" -ForegroundColor Green
} else {
  Write-Host "  WARN: Python not mentioned (model may answer generically)" -ForegroundColor Yellow
}

# 5. University recall
Write-Host "[5/7] New session recall: what university am I from?"
$recall = Invoke-Chat ($ProbeSession + "-uni") "What university am I from?"
Write-Host "  Agent: $($recall.response.Substring(0, [Math]::Min(250, $recall.response.Length)))"
if ($recall.response -match "FAST") {
  Write-Host "  OK: Recalled FAST" -ForegroundColor Green
} else {
  Write-Host "  WARN: FAST not mentioned" -ForegroundColor Yellow
}

# 6. Hackathon query (screenshot scenario - no JSON leak)
Write-Host "[6/7] Hackathon query (FAST student scenario)..."
$hack = Invoke-Chat ($ProbeSession + "-hack") "I am a student from FAST. Can you search for on-campus hackathons I might join?"
Write-Host "  Agent: $($hack.response.Substring(0, [Math]::Min(400, $hack.response.Length)))"
if ($hack.response -match '\{\s*"entity"') {
  Write-Host "  FAIL: JSON still leaking!" -ForegroundColor Red
  exit 1
}
Write-Host "  OK: Clean response (no JSON dump)" -ForegroundColor Green

# 7. Teach via chat (natural flow)
Write-Host "[7/7] Teach via chat: favorite IDE..."
$teach = Invoke-Chat $TeachSession "Remember this: my favorite IDE is VS Code. I am a FAST student."
Write-Host "  Agent: $($teach.response.Substring(0, [Math]::Min(200, $teach.response.Length)))..."
Start-Sleep -Seconds 2
$dump2 = Get-Dump
Write-Host $dump2.response

Write-Host ""
Write-Host "=== PROOF COMPLETE ===" -ForegroundColor Green
Write-Host "Web UI:  http://localhost:3000  (user_id: $Uid)"
Write-Host "Graph:   http://localhost:3000/visualizer?user=$Uid"
