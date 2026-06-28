# Independent product review for MnemOS memory behavior.
#
# This script uses fresh per-run user ids against the running stack. It does not
# wipe existing memories, so it is safe to run on a demo machine.

param(
  [switch]$SkipLiveChat
)

$ErrorActionPreference = "Stop"

$Api = "http://127.0.0.1:8000"
$Harness = "http://127.0.0.1:3000"
$Run = [guid]::NewGuid().ToString("N").Substring(0, 10)
$PrimaryUser = "review-$Run"
$OtherUser = "review-other-$Run"
$SharedUser = "review-shared-$Run"
$Failures = 0

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
    -Body ($Payload | ConvertTo-Json -Depth 8) -TimeoutSec $TimeoutSec
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

Write-Host "=== MnemOS Independent Review ===" -ForegroundColor Cyan
Write-Host "Primary user: $PrimaryUser"

Step "Stack health" {
  if ((GetJson "$Api/health").status -ne "ok") { throw "MnemOS unhealthy" }
  if ((GetJson "$Harness/health").status -ne "ok") { throw "Harness unhealthy" }
  if ((GetJson "http://127.0.0.1:8001/health").status -ne "ok") { throw "MCP unhealthy" }
}

Step "Explicit cross-channel identity binding" {
  $bind = PostJson "$Api/api/user/bind" @{
    channel = "telegram"
    sender_id = "tester-$Run"
    display_name = "Independent Tester"
    user_id = $SharedUser
  }
  if ($bind.user_id -ne $SharedUser) { throw "Binding ignored requested user_id" }
  $bindings = GetJson "$Api/api/user/bindings/$SharedUser"
  if ($bindings.bindings.Count -lt 1) { throw "No binding returned for shared user" }
}

Step "Store review memories" {
  StoreFact $PrimaryUser "backend_language" "prefers" "Python" "preference" 1.0
  StoreFact $PrimaryUser "frontend_framework" "uses" "React" "system_state" 1.0
  StoreFact $PrimaryUser "project_codename" "is" "Atlas" "system_state" 1.0
}

Step "Cross-session dump recall" {
  $dump = GetJson "$Api/api/memory/dump/$PrimaryUser"
  if ($dump.response -notmatch "Python") { throw "Python missing from dump" }
  if ($dump.response -notmatch "React") { throw "React missing from dump" }
  if ($dump.response -notmatch "Atlas") { throw "Atlas missing from dump" }
}

Step "Natural compound memory_search" {
  $query = [uri]::EscapeDataString("what do I use for Python React backend work on Atlas")
  $search = GetJson "$Api/api/memory/search/$PrimaryUser`?query=$query&top_k=5"
  $text = ($search.results | ConvertTo-Json -Depth 6)
  if ($text -notmatch "Python") { throw "Compound search missed Python" }
  if ($text -notmatch "React") { throw "Compound search missed React" }
  if ($text -notmatch "Atlas") { throw "Compound search missed Atlas" }
}

Step "Visualizer graph uses same namespace" {
  $graph = GetJson "$Harness/api/graph/$PrimaryUser"
  if ($graph.beliefs.Count -lt 3) { throw "Visualizer graph did not expose stored beliefs" }
}

Step "Cross-user isolation" {
  StoreFact $OtherUser "secret_token" "is" "OtherUserOnly" "system_state" 1.0
  $primaryDump = GetJson "$Api/api/memory/dump/$PrimaryUser"
  if ($primaryDump.response -match "OtherUserOnly") { throw "Other user's memory leaked" }
}

Step "Salience gate rejects low-conviction noise" {
  $resp = PostJson "$Api/api/memory/store" @{
    user_id = $PrimaryUser
    entity = "maybe_framework"
    relation = "prefers"
    value = "Vue"
    category = "preference"
    conviction = 0.2
  }
  if ($resp.stored) { throw "Low conviction preference was stored" }
  $dump = GetJson "$Api/api/memory/dump/$PrimaryUser"
  if ($dump.response -match "Vue") { throw "Rejected value appeared in active dump" }
}

Step "Contradiction overwrites stale value" {
  StoreFact $PrimaryUser "backend_language" "prefers" "Rust" "preference" 1.0
  $dump = GetJson "$Api/api/memory/dump/$PrimaryUser"
  if ($dump.response -notmatch "Rust") { throw "New contradictory value missing" }
  if ($dump.response -match "backend_language.*Python") { throw "Superseded Python backend preference still current" }
}

if (-not $SkipLiveChat) {
  Step "Live chat recall without raw memory markup" {
    $chat = PostJson "$Api/chat" @{
      user_id = $PrimaryUser
      session_id = "review-session-2"
      message = "In one short sentence, what backend language should we use?"
    } 120
    if (-not $chat.response) { throw "Empty chat response" }
    if ($chat.response -match "<memory_update>|entity_source|entity_target") {
      throw "Raw memory markup leaked into chat"
    }
    if ($chat.response -notmatch "Rust") {
      throw "Chat did not recall current backend language: $($chat.response)"
    }
  }

  Step "Live chat does not force irrelevant memories" {
    $chat = PostJson "$Api/chat" @{
      user_id = $PrimaryUser
      session_id = "review-session-3"
      message = "Say hello in a friendly way, nothing else."
    } 120
    if (-not $chat.response) { throw "Empty chat response" }
    if ($chat.response -match "Atlas|React|Rust|Python") {
      throw "Irrelevant memory surfaced in casual greeting: $($chat.response)"
    }
  }
}

Write-Host ""
if ($Failures -eq 0) {
  Write-Host "Independent review passed for $PrimaryUser" -ForegroundColor Green
  exit 0
}

Write-Host "$Failures independent review check(s) failed." -ForegroundColor Red
exit 1
