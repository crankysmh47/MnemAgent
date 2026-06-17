# Grant CLI device full operator scopes (fixes scope-upgrade loop on Windows)
$ErrorActionPreference = "Stop"
$scopes = @("operator.pairing", "operator.read", "operator.write")
$devicesDir = Join-Path $env:USERPROFILE ".openclaw\devices"
$identityDir = Join-Path $env:USERPROFILE ".openclaw\identity"
$pairedFile = Join-Path $devicesDir "paired.json"
$pendingFile = Join-Path $devicesDir "pending.json"
$authFile = Join-Path $identityDir "device-auth.json"

function Read-JsonFile([string]$Path) {
  $raw = [System.IO.File]::ReadAllText($Path)
  return ($raw.TrimStart([char]0xFEFF) | ConvertFrom-Json)
}

function Write-Utf8JsonFile([string]$Path, $Object, [int]$Depth = 10) {
  $utf8NoBom = New-Object System.Text.UTF8Encoding $false
  $json = $Object | ConvertTo-Json -Depth $Depth -Compress:$false
  [System.IO.File]::WriteAllText($Path, $json, $utf8NoBom)
}

if (-not (Test-Path $pairedFile)) {
  Write-Host "No paired devices yet - run openclaw agent once, then re-run this script if needed."
  exit 0
}

$paired = Read-JsonFile $pairedFile
foreach ($prop in $paired.PSObject.Properties) {
  $dev = $prop.Value
  $dev.scopes = $scopes
  $dev.approvedScopes = $scopes
  if ($dev.tokens.operator) {
    $dev.tokens.operator.scopes = $scopes
  }
}
Write-Utf8JsonFile $pairedFile $paired 10
Write-Utf8JsonFile $pendingFile @{} 3

if (Test-Path $authFile) {
  $auth = Read-JsonFile $authFile
  if ($auth.tokens.operator) {
    $auth.tokens.operator.scopes = $scopes
  }
  Write-Utf8JsonFile $authFile $auth 6
}

Write-Host "CLI device scopes updated: $($scopes -join ', ')" -ForegroundColor Green
