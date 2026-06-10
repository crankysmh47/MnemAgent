# Add Telegram channel to OpenClaw
param([string]$Token = "")
if (-not $Token) {
  $Token = Read-Host "Enter Telegram bot token from @BotFather"
}
openclaw channels add --channel telegram --token $Token
openclaw gateway restart
Write-Host "Telegram configured. DM your bot and approve pairing in dashboard."
