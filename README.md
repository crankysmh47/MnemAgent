# MnemOS

Memory layer for OpenClaw — selective ingestion, UCB retrieval, closed-loop feedback, and mathematical forgetting for the Qwen Global AI Hackathon (Track 1: MemoryAgent).

## Four Pillars

1. **Selective Ingestion** — Salience Auction gates what enters the graph
2. **Intelligent Retrieval** — UCB Multi-Armed Bandit + RWR associative hops
3. **Closed-Loop Feedback** — Proximity-based influence tracking adjusts Q_i
4. **Mathematical Forgetting** — Exponential decay + hard prune floor

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env         # add your QWEN_API_KEY
cd mcp-memory-server/src
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Docker

```bash
cp .env.example .env
docker-compose up --build
```

- MnemOS API: http://localhost:8000
- OpenClaw gateway: http://localhost:3000

## Evaluation Benchmark

Offline dry-run (no API key required):

```bash
python -m eval.run_benchmark --dry-run --mode both
```

Live comparison (requires running servers + QWEN_API_KEY):

```bash
python -m eval.run_benchmark --mode both
```

## MCP Commands

- `/memory` — brain state dump
- `/memory --mode stats` — UCB stats table for demo

## Alibaba Cloud Proof

OSS backup is implemented in [`mcp-memory-server/src/storage/cloud_sync.py`](mcp-memory-server/src/storage/cloud_sync.py).

## Tests

```bash
pytest tests/ -v
```

## License

MIT
