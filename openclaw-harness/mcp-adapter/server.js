/**
 * MnemOS MCP Adapter — exposes MnemOS memory operations as MCP tools over HTTP SSE.
 */

require("dotenv").config();
const express = require("express");
const cors = require("cors");
const axios = require("axios");
const { v4: uuidv4 } = require("uuid");

const PORT = process.env.PORT || 8001;
const MNEMOS_URL = (process.env.MNEMOS_URL || "http://localhost:8000").replace(/\/$/, "");

const app = express();
app.use(cors());
app.use(express.json({ limit: "2mb" }));

const sseClients = new Set();
const sessions = new Map();

const MCP_TOOLS = [
  {
    name: "memory_store",
    description: "Store a new fact in persistent memory",
    inputSchema: {
      type: "object",
      properties: {
        user_id: { type: "string" },
        entity: { type: "string" },
        relation: { type: "string" },
        value: { type: "string" },
        category: { type: "string" },
        conviction: { type: "number" },
      },
      required: ["user_id", "entity", "relation", "value"],
    },
  },
  {
    name: "memory_search",
    description: "Search persistent memory for relevant facts",
    inputSchema: {
      type: "object",
      properties: {
        user_id: { type: "string" },
        query: { type: "string" },
        top_k: { type: "number" },
      },
      required: ["user_id", "query"],
    },
  },
  {
    name: "memory_dump",
    description: "Get full brain state with confidence levels",
    inputSchema: {
      type: "object",
      properties: { user_id: { type: "string" } },
      required: ["user_id"],
    },
  },
  {
    name: "memory_stats",
    description: "Get UCB optimization metrics",
    inputSchema: {
      type: "object",
      properties: { user_id: { type: "string" } },
      required: ["user_id"],
    },
  },
];

function sendSse(res, payload) {
  res.write(`event: message\ndata: ${JSON.stringify(payload)}\n\n`);
}

function broadcast(payload) {
  for (const client of sseClients) {
    try {
      sendSse(client, payload);
    } catch (err) {
      sseClients.delete(client);
    }
  }
}

async function callTool(name, args) {
  const userId = args.user_id || "openclaw-default";
  console.log(`[MCP] tools/call ${name} user=${userId}`, args);

  if (name === "memory_store") {
    const resp = await axios.post(`${MNEMOS_URL}/api/memory/store`, {
      user_id: userId,
      entity: args.entity,
      relation: args.relation,
      value: args.value,
      category: args.category || "preference",
      conviction: args.conviction ?? 1.0,
    });
    return { content: [{ type: "text", text: JSON.stringify(resp.data) }] };
  }

  if (name === "memory_search") {
    const resp = await axios.get(`${MNEMOS_URL}/api/memory/search/${encodeURIComponent(userId)}`, {
      params: { query: args.query, top_k: args.top_k || 5 },
    });
    return { content: [{ type: "text", text: JSON.stringify(resp.data.results) }] };
  }

  if (name === "memory_dump") {
    const resp = await axios.post(`${MNEMOS_URL}/chat`, {
      user_id: userId,
      session_id: "mcp-adapter",
      message: "/memory",
    });
    return { content: [{ type: "text", text: resp.data.response }] };
  }

  if (name === "memory_stats") {
    const resp = await axios.post(`${MNEMOS_URL}/chat`, {
      user_id: userId,
      session_id: "mcp-adapter",
      message: "/memory --mode stats",
    });
    return { content: [{ type: "text", text: resp.data.response }] };
  }

  throw new Error(`Unknown tool: ${name}`);
}

async function handleJsonRpc(message) {
  const { id, method, params } = message;

  if (method === "initialize") {
    const sessionId = uuidv4();
    sessions.set(sessionId, { user_id: params?.clientInfo?.name || "openclaw" });
    return {
      jsonrpc: "2.0",
      id,
      result: {
        protocolVersion: "2024-11-05",
        capabilities: { tools: {} },
        serverInfo: { name: "mnemos-mcp-adapter", version: "1.0.0" },
        sessionId,
      },
    };
  }

  if (method === "notifications/initialized") {
    return null;
  }

  if (method === "tools/list") {
    return { jsonrpc: "2.0", id, result: { tools: MCP_TOOLS } };
  }

  if (method === "tools/call") {
    try {
      const result = await callTool(params.name, params.arguments || {});
      return { jsonrpc: "2.0", id, result };
    } catch (err) {
      return {
        jsonrpc: "2.0",
        id,
        error: { code: -32000, message: err.message },
      };
    }
  }

  return {
    jsonrpc: "2.0",
    id,
    error: { code: -32601, message: `Method not found: ${method}` },
  };
}

app.get("/health", async (_req, res) => {
  try {
    const upstream = await axios.get(`${MNEMOS_URL}/health`, { timeout: 5000 });
    res.json({ status: "ok", service: "mnemos-mcp-adapter", mnemos: upstream.data });
  } catch (err) {
    res.status(503).json({ status: "degraded", error: err.message });
  }
});

app.get("/mcp", (req, res) => {
  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.flushHeaders?.();

  sseClients.add(res);
  sendSse(res, { jsonrpc: "2.0", method: "notifications/endpoint", params: { uri: "/mcp/message" } });

  const heartbeat = setInterval(() => {
    try {
      res.write(": heartbeat\n\n");
    } catch {
      clearInterval(heartbeat);
      sseClients.delete(res);
    }
  }, 15000);

  req.on("close", () => {
    clearInterval(heartbeat);
    sseClients.delete(res);
    console.log("[MCP] SSE client disconnected — waiting for reconnection");
  });
});

app.post("/mcp/message", async (req, res) => {
  const message = req.body;
  const response = await handleJsonRpc(message);
  if (response) {
    broadcast(response);
    res.json(response);
  } else {
    res.status(202).json({ accepted: true });
  }
});

app.post("/tools/call", async (req, res) => {
  try {
    const { name, arguments: args } = req.body;
    const result = await callTool(name, args || {});
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.use((err, _req, res, _next) => {
  res.status(500).json({ error: err.message });
});

app.listen(PORT, () => {
  console.log(`MnemOS MCP adapter on :${PORT} → ${MNEMOS_URL}`);
});
