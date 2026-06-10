# Link WhatsApp to OpenClaw (QR pairing)
Write-Host "Starting WhatsApp login — scan QR with your phone (Linked Devices)"
openclaw channels login --channel whatsapp
openclaw gateway restart
Write-Host "WhatsApp linked. Send a test message to verify."
