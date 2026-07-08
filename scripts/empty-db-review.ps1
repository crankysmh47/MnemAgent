# Isolated first-install product review for MnemAgent.
#
# Starts a temporary API server against a brand-new SQLite database, exercises the
# memory layer like a real user across sessions, then tears the server down.

param(
  [int]$Port = 8010,
  [string]$Model = "qwen3.5-flash",
  [switch]$KeepDb
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Api = "http://127.0.0.1:$Port"
$Run = [guid]::NewGuid().ToString("N").Substring(0, 10)
$PrimaryUser = "empty-review-$Run"
$OtherUser = "empty-review-other-$Run"
$TempRoot = Join-Path ([System.IO.Path]::GetTempPath()) "mnemos-empty-review-$Run"
$DbPath = Join-Path $TempRoot "memory_state.db"
$Failures = 0
$Server = $null

$OldDbPath = $env:DB_PATH
$OldQwenModel = $env:QWEN_MODEL
$OldPythonPath = $env:PYTHONPATH

function Step($Name, [scriptblock]$Body) {
  Write-Host "[$Name] " -NoNewline
  try {
    & $Body
    Write-Host "OK" -ForegroundColor Green
  } catch {
    $script:Failures++
    Write-Host "FAIL" -ForegroundColor Red
    Write-Host "  $($_.Exception.Message)" -ForegroundColor Red
  }
}

function PostJson($Url, $Payload, $TimeoutSec = 30) {
  Invoke-RestMethod -Uri $Url -Method POST -ContentType "application/json" `
    -Body ($Payload | ConvertTo-Json -Depth 10) -TimeoutSec $TimeoutSec
}

function GetJson($Url, $TimeoutSec = 30) {
  Invoke-RestMethod -Uri $Url -TimeoutSec $TimeoutSec
}

function StoreFact($UserId, $Entity, $Relation, $Value, $Category = "preference", $Conviction = 1.0) {
  $resp = PostJson "$Api/api/memory/store" @{
    user_id = $UserId
    entity = $Entity
    relation = $Relation
    value = $Value
    category = $Category
    conviction = $Conviction
  }
  if (-not $resp.stored) {
    throw "Expected stored=true for $Entity $Relation $Value"
  }
}

function WaitForHealth($Seconds = 120) {
  $deadline = (Get-Date).AddSeconds($Seconds)
  do {
    try {
      $health = GetJson "$Api/health" 5
      if ($health.status -eq "ok") { return $health }
    } catch {
      Start-Sleep -Milliseconds 750
    }
  } while ((Get-Date) -lt $deadline)
  throw "Temporary API did not become healthy on $Api within $Seconds seconds"
}

function AssertTextContains($Text, $Needle, $Context) {
  if ($Text -notmatch [regex]::Escape($Needle)) {
    throw "$Context missing '$Needle'. Actual: $Text"
  }
}

try {
  New-Item -ItemType Directory -Force -Path $TempRoot | Out-Null

  $python = Join-Path $Root ".venv\Scripts\python.exe"
  if (-not (Test-Path $python)) {
    $python = "python"
  }

  $env:DB_PATH = $DbPath
  $env:QWEN_MODEL = $Model
  $env:PYTHONPATH = Join-Path $Root "mcp-memory-server\src"

  Write-Host "=== MnemAgent Empty-DB Product Review ===" -ForegroundColor Cyan
  Write-Host "API: $Api"
  Write-Host "Model: $Model"
  Write-Host "Primary user: $PrimaryUser"
  Write-Host "Database: $DbPath"

  $serverArgs = @("-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "$Port", "--log-level", "warning")
  $Server = Start-Process -FilePath $python -ArgumentList $serverArgs `
    -WorkingDirectory (Join-Path $Root "mcp-memory-server\src") `
    -WindowStyle Hidden -PassThru

  Step "Temporary API health" {
    $health = WaitForHealth 120
    if ($health.service -ne "mnemos") { throw "Unexpected service: $($health.service)" }
  }

  Step "Database starts empty" {
    $dump = GetJson "$Api/api/memory/dump/$PrimaryUser"
    if ($dump.response -notmatch "No active memories|No memories|empty") {
      throw "Expected empty initial dump, got: $($dump.response)"
    }
  }

  Step "First chat stores explicit memories" {
    $chat = PostJson "$Api/chat" @{
      user_id = $PrimaryUser
      session_id = "first-chat"
      message = "Remember this for future chats: my hackathon project codename is HelioForge, my preferred backend language is Python, and my frontend framework is React."
    } 120
    if (-not $chat.response) { throw "Empty teach response" }
    if ($chat.response -match "<memory_update>|entity_source|entity_target") {
      throw "Raw memory markup leaked into teach response: $($chat.response)"
    }
    Start-Sleep -Seconds 6
    $dump = GetJson "$Api/api/memory/dump/$PrimaryUser"
    $text = $dump.response
    AssertTextContains $text "HelioForge" "Teach dump"
    AssertTextContains $text "Python" "Teach dump"
    AssertTextContains $text "React" "Teach dump"
  }

  Step "New chat recalls cross-session facts" {
    $chat = PostJson "$Api/chat" @{
      user_id = $PrimaryUser
      session_id = "fresh-chat"
      message = "New chat. What do you remember about my project codename and stack?"
    } 120
    $response = $chat.response
    AssertTextContains $response "HelioForge" "Fresh-session recall"
    AssertTextContains $response "Python" "Fresh-session recall"
    AssertTextContains $response "React" "Fresh-session recall"
    if ($response -match "<memory_update>|entity_source|entity_target") {
      throw "Raw memory markup leaked into recall response: $response"
    }
  }

  Step "Casual chat stays non-intrusive" {
    $chat = PostJson "$Api/chat" @{
      user_id = $PrimaryUser
      session_id = "casual-chat"
      message = "Say hello in one short sentence."
    } 120
    $response = $chat.response
    if (-not $response) { throw "Empty casual response" }
    if ($response -match "HelioForge|Python|React") {
      throw "Casual greeting surfaced irrelevant memory: $response"
    }
  }

  Step "Natural compound search finds all facts" {
    $query = [uri]::EscapeDataString("what is my HelioForge Python React stack")
    $search = GetJson "$Api/api/memory/search/$PrimaryUser`?query=$query&top_k=6"
    $text = $search.results | ConvertTo-Json -Depth 8
    AssertTextContains $text "HelioForge" "Compound search"
    AssertTextContains $text "Python" "Compound search"
    AssertTextContains $text "React" "Compound search"
  }

  Step "Cross-user isolation" {
    StoreFact $OtherUser "private_codename" "is" "OtherOnly" "system_state" 1.0
    $dump = GetJson "$Api/api/memory/dump/$PrimaryUser"
    if ($dump.response -match "OtherOnly") { throw "Other user's memory leaked into primary dump" }
  }

  Step "Salience rejects low-conviction noise" {
    $resp = PostJson "$Api/api/memory/store" @{
      user_id = $PrimaryUser
      entity = "maybe_runtime"
      relation = "prefers"
      value = "Bun"
      category = "preference"
      conviction = 0.2
    }
    if ($resp.stored) { throw "Low-conviction preference was stored" }
    $dump = GetJson "$Api/api/memory/dump/$PrimaryUser"
    if ($dump.response -match "Bun") { throw "Rejected low-conviction value appeared in dump" }
  }

  Step "Contradiction replaces stale value" {
    StoreFact $PrimaryUser "backend_language" "prefers" "Rust" "preference" 1.0
    $dump = GetJson "$Api/api/memory/dump/$PrimaryUser"
    $text = $dump.response
    AssertTextContains $text "Rust" "Contradiction dump"
    if ($text -match "backend_language.*Python") {
      throw "Superseded backend_language Python value still current"
    }
  }

  Step "Memory graph API exposes active beliefs" {
    $graph = GetJson "$Api/api/graph/$PrimaryUser"
    if ($graph.beliefs.Count -lt 3) {
      throw "Expected at least 3 graph beliefs, got $($graph.beliefs.Count)"
    }
  }

  Write-Host ""
  if ($Failures -eq 0) {
    Write-Host "Empty-DB product review passed for $PrimaryUser" -ForegroundColor Green
    exit 0
  }

  Write-Host "$Failures empty-DB review check(s) failed." -ForegroundColor Red
  exit 1
} finally {
  if ($Server -and -not $Server.HasExited) {
    Stop-Process -Id $Server.Id -Force -ErrorAction SilentlyContinue
  }

  $env:DB_PATH = $OldDbPath
  $env:QWEN_MODEL = $OldQwenModel
  $env:PYTHONPATH = $OldPythonPath

  if (-not $KeepDb -and (Test-Path $TempRoot)) {
    Remove-Item -LiteralPath $TempRoot -Recurse -Force -ErrorAction SilentlyContinue
  }
}
