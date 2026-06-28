# Register MnemOS MCP server with OpenClaw CLI
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
openclaw mcp set mnemos $json
openclaw config set gateway.auth.mode none 2>$null | Out-Null
openclaw plugins disable memory-core 2>$null | Out-Null
openclaw mcp list
