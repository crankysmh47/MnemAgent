# MnemOS Memory Tools

## MCP Server: mnemos

- **stdio**: `node /path/to/mcp-server/src/index.js --transport stdio`
- **HTTP**: `http://localhost:8001/mcp` (transport: streamable-http)

## MnemOS Backend

- API: `http://localhost:8000`
- Health: `GET /health`

## Tool Schemas

### memory_store
`{ user_id, entity, relation, value, category?, conviction? }`

### memory_search
`{ user_id, query, top_k?, category?, min_confidence? }`

### memory_dump / memory_stats
`{ user_id, format?: text|markdown|json }`

### memory_bind_user / memory_resolve_user
`{ channel, sender_id, display_name? }` → `{ user_id }`

Channels: `telegram`, `discord`, `whatsapp`, `slack`, `webchat`
