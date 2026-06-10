# Grant CLI device full operator scopes (fixes scope-upgrade loop on Windows)
$ErrorActionPreference = "Stop"
$scopes = @("operator.pairing", "operator.read", "operator.write")
$devicesDir = Join-Path $env:USERPROFILE ".openclaw\devices"
$identityDir = Join-Path $env:USERPROFILE ".openclaw\identity"
$pairedFile = Join-Path $devicesDir "paired.json"
$pendingFile = Join-Path $devicesDir "pending.json"
$authFile = Join-Path $identityDir "device-auth.json"

if (-not (Test-Path $pairedFile)) {
  Write-Host "No paired devices yet - run openclaw agent once, then re-run this script if needed."
  exit 0
}

$paired = Get-Content $pairedFile -Raw | ConvertFrom-Json
foreach ($prop in $paired.PSObject.Properties) {
  $dev = $prop.Value
  $dev.scopes = $scopes
  $dev.approvedScopes = $scopes
  if ($dev.tokens.operator) {
    $dev.tokens.operator.scopes = $scopes
  }
}
$paired | ConvertTo-Json -Depth 10 | Set-Content $pairedFile -Encoding UTF8
@{} | ConvertTo-Json | Set-Content $pendingFile -Encoding UTF8

if (Test-Path $authFile) {
  $auth = Get-Content $authFile -Raw | ConvertFrom-Json
  if ($auth.tokens.operator) {
    $auth.tokens.operator.scopes = $scopes
  }
  $auth | ConvertTo-Json -Depth 6 | Set-Content $authFile -Encoding UTF8
}

Write-Host "CLI device scopes updated: $($scopes -join ', ')" -ForegroundColor Green
