# Register MnemOS MCP server with OpenClaw CLI
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$McpPath = (Join-Path $Root "mcp-server\src\index.js") -replace "\\", "/"
$json = '{"command":"node","args":["' + $McpPath + '","--transport","stdio"],"env":{"MNEMOS_URL":"http://localhost:8000"}}'
openclaw mcp set mnemos $json
openclaw mcp list
