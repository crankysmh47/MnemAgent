---
name: mnemos-memory
description: Persistent memory — store, search, dump, and stats across sessions and channels
---

# MnemOS Memory Skill

Use MnemOS MCP tools for all long-term memory operations.

## Workflow

1. **Resolve user** — `mnemos__memory_resolve_user(channel, sender_id)` on first message.
2. **Search** — `mnemos__memory_search(user_id, query)` before answering preference/history questions.
3. **Store** — `mnemos__memory_store` when user teaches firm facts.
4. **Dump** — `mnemos__memory_dump` when user asks what's remembered.

Do not use OpenClaw's built-in `memory_search` or `memory_get`. Those tools read
OpenClaw's local file-backed memory index, not the MnemOS semantic graph.

## Examples

**Store:** User says "I always prefer Python for backend."
→ `mnemos__memory_store({ user_id, entity: "backend_language", relation: "prefers", value: "Python", conviction: 1.0 })`

**Recall:** User asks "What language for the API?"
→ `mnemos__memory_search({ user_id, query: "backend language API" })` then answer using results.

**Cross-channel:** Same user_id from `mnemos__memory_resolve_user` works on Telegram, Discord, WhatsApp.
