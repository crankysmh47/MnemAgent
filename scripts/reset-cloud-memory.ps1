# Prepare a judge-safe MnemAgent database.
#
# Preserves demo namespaces such as demo-brain, removes all test/live users,
# creates a fresh judge user id, and updates local OpenClaw MCP registration
# when the OpenClaw CLI is available.
[CmdletBinding(SupportsShouldProcess = $true)]
param(
  [string]$DbPath = "",
  [string[]]$KeepUsers = @("demo-brain"),
  [string]$JudgePrefix = "judge",
  [switch]$KeepDemoBrain,
  [switch]$NoDockerRestart
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$ConfigDir = Join-Path $env:USERPROFILE ".openclaw"
$UserFile = Join-Path $ConfigDir "mnemos-user-id.txt"

function Resolve-DbPath {
  param([string]$ExplicitPath)
  if ($ExplicitPath) { return (Resolve-Path $ExplicitPath).Path }

  $candidates = @(
    (Join-Path $Root "mcp-memory-server\src\data\memory_state.db"),
    (Join-Path $Root "data\memory_state.db")
  )
  foreach ($candidate in $candidates) {
    if (Test-Path $candidate) { return (Resolve-Path $candidate).Path }
  }
  return (Join-Path $Root "mcp-memory-server\src\data\memory_state.db")
}

function Test-DockerServiceRunning {
  try {
    $cid = docker compose ps -q mnemos-memory 2>$null
    return -not [string]::IsNullOrWhiteSpace($cid)
  } catch {
    return $false
  }
}

function Set-DotEnvValue {
  param([string]$Name, [string]$Value)
  $envFile = Join-Path $Root ".env"
  if (-not (Test-Path $envFile)) {
    Copy-Item (Join-Path $Root "config\env.template") $envFile
  }

  $lines = Get-Content $envFile
  $escaped = [regex]::Escape($Name)
  $line = "$Name=$Value"
  $found = $false
  $updated = foreach ($entry in $lines) {
    if ($entry -match "^\s*$escaped=") {
      $found = $true
      $line
    } else {
      $entry
    }
  }
  if (-not $found) {
    $updated += $line
  }
  Set-Content -Path $envFile -Value $updated -Encoding UTF8
}

function Update-OpenClawJson {
  param([string]$JudgeUserId)

  $configFile = Join-Path $ConfigDir "openclaw.json"
  if (-not (Test-Path $configFile)) { return }

  $mcpPath = (Join-Path $Root "mcp-server\src\index.js") -replace "\\", "/"
  $cfg = Get-Content $configFile -Raw | ConvertFrom-Json
  if (-not $cfg.mcp) { $cfg | Add-Member -NotePropertyName mcp -NotePropertyValue ([pscustomobject]@{}) }
  if (-not $cfg.mcp.servers) { $cfg.mcp | Add-Member -NotePropertyName servers -NotePropertyValue ([pscustomobject]@{}) }
  if (-not ($cfg.mcp.servers.PSObject.Properties.Name -contains "mnemos")) {
    $cfg.mcp.servers | Add-Member -NotePropertyName mnemos -NotePropertyValue ([pscustomobject]@{})
  }
  $cfg.mcp.servers.mnemos = [pscustomobject]@{
    command = "node"
    args = @($mcpPath, "--transport", "stdio")
    env = [pscustomobject]@{
      MNEMOS_URL = "http://localhost:8000"
      MNEMOS_DEFAULT_USER_ID = $JudgeUserId
    }
  }
  if (-not $cfg.plugins) { $cfg | Add-Member -NotePropertyName plugins -NotePropertyValue ([pscustomobject]@{}) }
  if (-not $cfg.plugins.entries) { $cfg.plugins | Add-Member -NotePropertyName entries -NotePropertyValue ([pscustomobject]@{}) }
  if (-not ($cfg.plugins.entries.PSObject.Properties.Name -contains "memory-core")) {
    $cfg.plugins.entries | Add-Member -NotePropertyName "memory-core" -NotePropertyValue ([pscustomobject]@{})
  }
  $cfg.plugins.entries."memory-core" | Add-Member -Force -NotePropertyName enabled -NotePropertyValue $false

  $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
  [System.IO.File]::WriteAllText($configFile, ($cfg | ConvertTo-Json -Depth 100), $utf8NoBom)
}

function Write-ResetPythonScript {
  param([string[]]$PreserveUsers)

  $keepJson = ConvertTo-Json -InputObject @($PreserveUsers) -Compress
  $keepPayload = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($keepJson))
  $script = @'
import base64
import json
import os
import sqlite3
import sys

db_path = sys.argv[1]
keep_users = set(json.loads(base64.b64decode(sys.argv[2]).decode("utf-8")))
os.makedirs(os.path.dirname(db_path), exist_ok=True)
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
try:
    conn.execute("PRAGMA foreign_keys = OFF")
    before = {}
    for table in ("semantic_graph", "episodic_logs", "memory_events", "user_bindings", "user_entities"):
        try:
            before[table] = conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()["c"]
        except sqlite3.Error:
            before[table] = 0

    if keep_users:
        placeholders = ",".join("?" for _ in keep_users)
        params = list(keep_users)
        keep_ids = [
            int(row["id"])
            for row in conn.execute(
                f"SELECT id FROM semantic_graph WHERE user_id IN ({placeholders})",
                params,
            ).fetchall()
        ]
        for table in ("semantic_graph", "episodic_logs", "memory_events", "user_bindings", "user_entities"):
            conn.execute(f"DELETE FROM {table} WHERE user_id NOT IN ({placeholders})", params)
        try:
            if keep_ids:
                id_placeholders = ",".join("?" for _ in keep_ids)
                conn.execute(f"DELETE FROM vec_memory WHERE id NOT IN ({id_placeholders})", keep_ids)
            else:
                conn.execute("DELETE FROM vec_memory")
        except sqlite3.Error:
            pass
    else:
        for table in ("semantic_graph", "episodic_logs", "memory_events", "user_bindings", "user_entities"):
            conn.execute(f"DELETE FROM {table}")
        try:
            conn.execute("DELETE FROM vec_memory")
        except sqlite3.Error:
            pass

    conn.commit()
    conn.execute("VACUUM")
    after = {}
    for table in ("semantic_graph", "episodic_logs", "memory_events", "user_bindings", "user_entities"):
        try:
            after[table] = conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()["c"]
        except sqlite3.Error:
            after[table] = 0
    print(json.dumps({"before": before, "after": after}, indent=2))
finally:
    conn.close()
'@
  $tempScript = Join-Path ([System.IO.Path]::GetTempPath()) "mnemos_reset_memory.py"
  Set-Content -Path $tempScript -Value $script -Encoding UTF8
  return @{ Path = $tempScript; KeepPayload = $keepPayload }
}

function Invoke-SqliteReset {
  param([string]$Path, [string[]]$PreserveUsers, [bool]$UseDocker)

  $payload = Write-ResetPythonScript -PreserveUsers $PreserveUsers
  if ($UseDocker) {
    docker compose cp $payload.Path mnemos-memory:/tmp/mnemos_reset_memory.py | Out-Null
    docker compose exec -T mnemos-memory python /tmp/mnemos_reset_memory.py /app/data/memory_state.db $payload.KeepPayload
    if ($LASTEXITCODE -ne 0) {
      throw "In-container SQLite reset failed"
    }
    return
  }

  python $payload.Path $Path $payload.KeepPayload
  if ($LASTEXITCODE -ne 0) {
    throw "SQLite reset failed"
  }
}

$useDockerDb = (-not $DbPath) -and (Test-DockerServiceRunning)
$resolvedDb = if ($useDockerDb) { "/app/data/memory_state.db (mnemos-memory container)" } else { Resolve-DbPath $DbPath }
$keep = if ($KeepDemoBrain) { $KeepUsers } else { $KeepUsers }
$judgeUserId = "$JudgePrefix-$([guid]::NewGuid().ToString("N").Substring(0, 12))"

Write-Host "=== MnemAgent Cloud Memory Reset ===" -ForegroundColor Cyan
Write-Host "Database: $resolvedDb"
Write-Host "Preserving users: $($keep -join ', ')"
Write-Host "Fresh judge user_id: $judgeUserId"

if ($PSCmdlet.ShouldProcess($resolvedDb, "wipe non-demo memories and create judge namespace")) {
  Invoke-SqliteReset -Path $resolvedDb -PreserveUsers $keep -UseDocker:$useDockerDb

  New-Item -ItemType Directory -Force -Path $ConfigDir | Out-Null
  $judgeUserId | Set-Content $UserFile -Encoding UTF8
  Set-DotEnvValue -Name "MNEMOS_DEFAULT_USER_ID" -Value $judgeUserId

  $mcpPath = (Join-Path $Root "mcp-server\src\index.js") -replace "\\", "/"
  $openclaw = Get-Command openclaw -ErrorAction SilentlyContinue
  if ($openclaw) {
    $json = '{"command":"node","args":["' + $mcpPath + '","--transport","stdio"],"env":{"MNEMOS_URL":"http://localhost:8000","MNEMOS_DEFAULT_USER_ID":"' + $judgeUserId + '"}}'
    try {
      openclaw mcp set mnemos $json 2>$null | Out-Null
      openclaw config set gateway.auth.mode none 2>$null | Out-Null
      openclaw plugins disable memory-core 2>$null | Out-Null
    } catch {
      Write-Host "WARNING: OpenClaw CLI update failed; patching openclaw.json directly." -ForegroundColor Yellow
    }
  }
  Update-OpenClawJson -JudgeUserId $judgeUserId

  if (-not $NoDockerRestart) {
    docker compose restart mnemos-memory mnemos-mcp openclaw-harness | Out-Null
  }

  Write-Host ""
  Write-Host "Judge namespace is clean." -ForegroundColor Green
  Write-Host "Judge user_id: $judgeUserId"
  Write-Host "Visualizer demo: http://localhost:3000?user=demo-brain"
  Write-Host "Judge visualizer: http://localhost:3000?user=$judgeUserId"
}
