# Judge guide

MnemAgent is submitted to Track 1: MemoryAgent. The shortest useful test is a store, a new-session recall, and a correction.

## Deployed walkthrough

1. Open the submitted Alibaba Cloud visualizer URL and inspect `demo-brain`.
2. Open the protected OpenClaw console, or use the terminal commands shown in the video.
3. Store: "My backend framework is FastAPI and my project codename is Fern."
4. Start a new session. Ask: "What backend framework and codename did I choose?"
5. Correct it: "I switched my backend framework from FastAPI to Hono."
6. Start one more session and ask for the framework. The answer should contain Hono and omit FastAPI.
7. Search for `backend framework` in the visualizer. Select the result to inspect its relationships.

`demo-brain` is a populated read-only presentation namespace. Deployment operators should reset a separate `judge-*` namespace before recording or judging.

## Local walkthrough

```bash
git clone https://github.com/crankysmh47/MnemAgent.git
cd MnemAgent
cp config/env.template .env
# Set LLM_API_KEY and QWEN_API_KEY in .env
docker compose up -d --build
```

Open `http://localhost:3000/?user=demo-brain`. The memory API and MCP health endpoints are `http://localhost:8000/health` and `http://localhost:8001/health`.

For the real agent path, follow `scripts/setup-openclaw.sh`, then run:

```bash
openclaw mcp probe mnemos
openclaw agent --agent main --session-id judge-store --message "Remember that my backend framework is FastAPI."
openclaw agent --agent main --session-id judge-recall --message "What backend framework do I use?"
```

## Expected failure messages

- API health fails: inspect `docker compose logs mnemos-memory`.
- MCP probe fails: verify `http://mnemos-mcp:8001/mcp` in the OpenClaw configuration.
- The archive is empty: use `?user=demo-brain` and run `powershell -File scripts/seed-demo-brain.ps1` on Windows.
- Qwen calls fail: verify the DashScope key, compatible-mode URL, and model name without printing the key.
