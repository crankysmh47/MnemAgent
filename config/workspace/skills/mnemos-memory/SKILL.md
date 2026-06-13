---
name: mnemos-memory
description: Persistent memory — store, search, dump, and stats across sessions and channels
---

# MnemOS Memory Skill

Use MnemOS MCP tools for all long-term memory operations.

## Workflow

1. **Resolve user** — `memory_resolve_user(channel, sender_id)` on first message.
2. **Search** — `memory_search(user_id, query)` before answering preference/history questions.
3. **Store** — `memory_store` when user teaches firm facts.
4. **Dump** — `memory_dump` when user asks what's remembered.

## Examples

**Store:** User says "I always prefer Python for backend."
→ `memory_store({ user_id, entity: "backend_language", relation: "prefers", value: "Python", conviction: 1.0 })`

**Recall:** User asks "What language for the API?"
→ `memory_search({ user_id, query: "backend language API" })` then answer using results.

**Cross-channel:** Same user_id from `memory_resolve_user` works on Telegram, Discord, WhatsApp.
