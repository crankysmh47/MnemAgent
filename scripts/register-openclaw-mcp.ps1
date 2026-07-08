# Register MnemAgent MCP server with OpenClaw CLI
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$ConfigDir = Join-Path $env:USERPROFILE ".openclaw"
$UserFile = Join-Path $ConfigDir "mnemos-user-id.txt"
if (-not (Test-Path $UserFile)) {
  try {
    $body = '{"channel":"openclaw","sender_id":"main"}'
    $canonical = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/user/bind" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 10
    if ($canonical.user_id) {
      $canonical.user_id | Set-Content $UserFile
    }
  } catch {
    [guid]::NewGuid().ToString() | Set-Content $UserFile
  }
  if (-not (Test-Path $UserFile)) {
    [guid]::NewGuid().ToString() | Set-Content $UserFile
  }
}
$UserId = (Get-Content $UserFile -Raw).Trim()
$McpPath = (Join-Path $Root "mcp-server\src\index.js") -replace "\\", "/"
$json = '{"command":"node","args":["' + $McpPath + '","--transport","stdio"],"env":{"MNEMOS_URL":"http://localhost:8000","MNEMOS_DEFAULT_USER_ID":"' + $UserId + '"}}'
try {
  openclaw mcp set mnemos $json 2>$null | Out-Null
  openclaw config set gateway.auth.mode none 2>$null | Out-Null
  openclaw plugins disable memory-core 2>$null | Out-Null
} catch {
  Write-Host "OpenClaw CLI registration failed; patching openclaw.json directly." -ForegroundColor Yellow
}

$ConfigFile = Join-Path $ConfigDir "openclaw.json"
if (Test-Path $ConfigFile) {
  $cfg = Get-Content $ConfigFile -Raw | ConvertFrom-Json
  if (-not $cfg.mcp) { $cfg | Add-Member -NotePropertyName mcp -NotePropertyValue ([pscustomobject]@{}) }
  if (-not $cfg.mcp.servers) { $cfg.mcp | Add-Member -NotePropertyName servers -NotePropertyValue ([pscustomobject]@{}) }
  if (-not ($cfg.mcp.servers.PSObject.Properties.Name -contains "mnemos")) {
    $cfg.mcp.servers | Add-Member -NotePropertyName mnemos -NotePropertyValue ([pscustomobject]@{})
  }
  $cfg.mcp.servers.mnemos = [pscustomobject]@{
    command = "node"
    args = @($McpPath, "--transport", "stdio")
    env = [pscustomobject]@{
      MNEMOS_URL = "http://localhost:8000"
      MNEMOS_DEFAULT_USER_ID = $UserId
    }
  }
  if (-not $cfg.plugins) { $cfg | Add-Member -NotePropertyName plugins -NotePropertyValue ([pscustomobject]@{}) }
  if (-not $cfg.plugins.entries) { $cfg.plugins | Add-Member -NotePropertyName entries -NotePropertyValue ([pscustomobject]@{}) }
  if (-not ($cfg.plugins.entries.PSObject.Properties.Name -contains "memory-core")) {
    $cfg.plugins.entries | Add-Member -NotePropertyName "memory-core" -NotePropertyValue ([pscustomobject]@{})
  }
  $cfg.plugins.entries."memory-core" | Add-Member -Force -NotePropertyName enabled -NotePropertyValue $false
  [System.IO.File]::WriteAllText($ConfigFile, ($cfg | ConvertTo-Json -Depth 100), [System.Text.UTF8Encoding]::new($false))
}

openclaw mcp list
