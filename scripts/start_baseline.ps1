# Start the memory-less baseline server for eval comparisons (port 8002).
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root
$env:PYTHONPATH = Join-Path $root "mcp-memory-server\src"
& (Join-Path $root ".venv\Scripts\uvicorn.exe") eval.baseline_server:app --host 127.0.0.1 --port 8002
