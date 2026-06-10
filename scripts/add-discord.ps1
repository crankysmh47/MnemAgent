# Add Discord channel to OpenClaw
param([string]$Token = "")
if (-not $Token) {
  $Token = Read-Host "Enter Discord bot token"
}
openclaw channels add --channel discord --token $Token
openclaw gateway restart
Write-Host "Discord configured. Invite bot to your server and test in DMs."
