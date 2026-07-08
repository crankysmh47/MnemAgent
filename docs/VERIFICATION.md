# MnemOS Verification Evidence

This file records the product-level checks used before the deployment/submission
phase. It is intentionally focused on user-visible behavior, not only unit tests.

## Current Runtime Model

The local review environment uses Alibaba/Qwen workspace-compatible API routing
with:

```text
LLM_MODEL=qwen3.5-flash
```

This model is the default for development and review because it preserves the
larger trial models for final benchmark/video runs while still exercising the
real hosted model path.

Recommended model tiers:

| Use case | Model |
| --- | --- |
| Daily development and UX checks | `qwen3.5-flash` |
| Long-running memory benchmarks | `qwen3.5-flash` or `qwen-flash` |
| Final demo recording / judge-facing run | strongest available trial model, e.g. `qwen-max` if quota allows |

## Empty-Database Product Review

Command:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\empty-db-review.ps1
```

What it does:

1. Starts a temporary MnemOS API server on port `8010`.
2. Uses a brand-new SQLite database under the system temp directory.
3. Teaches explicit memories through `/chat`.
4. Verifies a different session recalls those memories.
5. Verifies casual chat does not surface irrelevant memories.
6. Verifies natural compound search finds the stored facts.
7. Verifies cross-user isolation.
8. Verifies low-conviction noise is rejected.
9. Verifies contradiction overwrite replaces stale beliefs.
10. Verifies the graph API exposes active beliefs.
11. Stops the temporary server and removes the temp DB by default.

Latest observed result:

```text
Empty-DB product review passed for empty-review-680d3c62bf
```

This is the strongest local proof for the "fresh install / first user / empty
brain" path because it does not rely on the warmed Docker demo database.

## OpenClaw Agent Path

The product is not only the MnemOS API. The submission path is OpenClaw with
MnemOS attached through MCP.

Health checks:

```powershell
openclaw gateway health
openclaw mcp probe mnemos
```

Latest observed result:

```text
Gateway Health
OK (91ms)

MCP probe (...\.openclaw\openclaw.json):
- mnemos: 7 tools
```

Live OpenClaw teach/recall check:

```powershell
$uid = "openclaw-live-52294092"

openclaw agent --agent main --session-id "oc-teach-$uid" `
  --message "For user_id $uid, call mnemos memory_store to remember: my project codename is SolarisWing, my backend language is Python, and my frontend framework is React. Then reply in one short sentence with no JSON."

openclaw agent --agent main --session-id "oc-recall-$uid" `
  --message "For user_id $uid, use mnemos memory_search or memory_dump, then answer: what is my project codename and stack? Reply naturally, no raw JSON."
```

Latest observed output:

```text
I've remembered your project codename is SolarisWing, your backend uses Python, and your frontend framework is React.

Your project codename is SolarisWing, and your stack consists of Python for the backend and React for the frontend.
```

Stored memory dump:

```text
project -> codename -> SolarisWing
technology -> backend_language -> Python
technology -> frontend_framework -> React
```

Casual non-intrusion check:

```powershell
openclaw agent --agent main --session-id "oc-casual-$uid" `
  --message "For user_id $uid, just say hello in one short friendly sentence. Do not discuss memory unless needed."
```

Latest observed output:

```text
Hello! 👋
```

This verifies the memory layer is available through the real OpenClaw path and
does not automatically make ordinary chat feel invasive.

## Browser UX Check

The in-app browser was used against:

```text
http://127.0.0.1:3000/?user=ux-review-6612d988
```

Observed behavior:

- The user id field preserved `ux-review-6612d988`.
- The visualizer showed the user's memories instead of a generic placeholder.
- After teaching two new facts, the graph refreshed from 3 nodes to 5 nodes.
- The visible memories included:
  - backend language: Python
  - frontend framework: React
  - project codename: HelioForge
  - deployment region: Singapore
  - benchmark suite: MnemBench

Live chat check through the MnemOS API:

```text
Teach: stored Singapore and MnemBench.
Fresh session recall: recalled Python, React, HelioForge, Singapore, and MnemBench.
Casual greeting: "Hello, how can I assist you today?"
```

This verifies the tester-reported user-id issue is not reproducing on the current
runtime when the URL contains an explicit `?user=...` namespace.

## Targeted Regression Tests

Command:

```powershell
.\.venv\Scripts\python.exe -m pytest `
  tests/test_response_grounding.py `
  tests/test_waking.py `
  tests/test_main.py `
  tests/test_qwen_client.py `
  tests/test_api_data.py `
  tests/test_api_user_bind.py `
  tests/test_user_bindings.py `
  -q --tb=short
```

Latest observed result:

```text
84 passed, 1 warning
```

These tests cover the highest-risk memory UX paths touched during review:

- relevance-gated memory injection
- waking-phase retrieval behavior
- fallback extraction and response handling
- Qwen memory parsing
- memory graph/search data APIs
- explicit user binding
- cross-channel user identity mapping

## What This Proves

| Requirement | Evidence |
| --- | --- |
| Fresh empty DB works | `scripts/empty-db-review.ps1` starts a new temp DB and passes end-to-end |
| Cross-session persistence | Empty-DB review and OpenClaw teach/recall use different session ids |
| OpenClaw integration works | Gateway health plus `openclaw mcp probe mnemos` reports 7 tools |
| Real agent can store through MCP | OpenClaw teach command stored SolarisWing/Python/React |
| Real agent can recall through MCP | OpenClaw recall command answered from stored memory |
| Casual chat is not invasive | MnemOS and OpenClaw casual checks did not mention stored project facts |
| User-id namespace is preserved in UI | Browser check kept `ux-review-6612d988` and showed matching memories |
| Low-conviction noise is rejected | Empty-DB review rejects `conviction=0.2` preference |
| Contradictions overwrite stale values | Empty-DB review replaces backend language with Rust |
| Cross-user isolation holds | Empty-DB review stores a second user's private fact and verifies no leak |

## Remaining Outside Local Verification

These are deployment/submission tasks rather than core local product behavior:

- Alibaba ECS deployment
- Alibaba OSS proof screenshot
- final demo video capture
- public release tagging

The local product path is ready to support those tasks.
