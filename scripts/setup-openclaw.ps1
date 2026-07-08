# One-command MnemAgent + OpenClaw setup (Windows) — delegates to onboard-openclaw.ps1
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

$nodeVer = node --version 2>$null
if (-not $nodeVer) { Write-Error "Node.js required. Install from https://nodejs.org" }

$openclaw = Get-Command openclaw -ErrorAction SilentlyContinue
if (-not $openclaw) {
  Write-Host "Installing OpenClaw globally..." -ForegroundColor Yellow
  npm install -g openclaw@latest
}

& (Join-Path $PSScriptRoot "onboard-openclaw.ps1")
