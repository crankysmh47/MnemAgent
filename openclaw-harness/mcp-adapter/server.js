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
    name: "memory_resolve_user",
    description:
      "Resolve channel + sender_id to a stable canonical user_id. MUST be called before any other memory tool. Returns the user_id to use for all subsequent memory operations.",
    inputSchema: {
      type: "object",
      properties: {
        channel: { type: "string", description: "Channel identifier (openclaw, telegram, discord, whatsapp, slack, webchat)" },
        sender_id: { type: "string", description: "Sender identifier within that channel (e.g. agent name, user handle)" },
        display_name: { type: "string", description: "Optional human-readable display name" },
      },
      required: ["channel", "sender_id"],
    },
  },
  {
    name: "memory_bind_user",
    description: "Bind a channel sender to a specific canonical user_id",
    inputSchema: {
      type: "object",
      properties: {
        channel: { type: "string" },
        sender_id: { type: "string" },
        display_name: { type: "string" },
        user_id: { type: "string", description: "Optional — derived from channel+sender_id if omitted" },
      },
      required: ["channel", "sender_id"],
    },
  },
  {
    name: "memory_store",
    description: "Store a new fact in persistent memory (salience-gated)",
    inputSchema: {
      type: "object",
      properties: {
        user_id: { type: "string", description: "REQUIRED — call memory_resolve_user first to get this" },
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
        user_id: { type: "string", description: "REQUIRED — call memory_resolve_user first to get this" },
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
      properties: { user_id: { type: "string", description: "REQUIRED — call memory_resolve_user first to get this" } },
      required: ["user_id"],
    },
  },
  {
    name: "memory_stats",
    description: "Get UCB optimization metrics for stored beliefs",
    inputSchema: {
      type: "object",
      properties: { user_id: { type: "string", description: "REQUIRED — call memory_resolve_user first to get this" } },
      required: ["user_id"],
    },
  },
  {
    name: "memory_chat",
    description: "Send a message through MnemOS memory-augmented chat",
    inputSchema: {
      type: "object",
      properties: {
        user_id: { type: "string", description: "REQUIRED — call memory_resolve_user first to get this" },
        session_id: { type: "string" },
        message: { type: "string" },
      },
      required: ["user_id", "session_id", "message"],
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

function requireUserId(args, session) {
  const userId = args.user_id || (session && session.user_id);
  if (!userId) {
    throw new Error(
      "user_id is required. Call memory_resolve_user(channel, sender_id) first to obtain your canonical user_id."
    );
  }
  return userId;
}

async function callTool(name, args, session) {
  if (name === "memory_resolve_user" || name === "memory_bind_user") {
    const resp = await axios.post(`${MNEMOS_URL}/api/user/bind`, {
      channel: args.channel || "openclaw",
      sender_id: args.sender_id,
      display_name: args.display_name,
      user_id: args.user_id,
    });
    const userId = resp.data.user_id;
    // Update session so subsequent tool calls use the resolved user_id automatically
    if (session) {
      session.user_id = userId;
      session.display_name = resp.data.display_name || args.display_name;
    }
    console.log(`[MCP] ${name} channel=${args.channel} sender=${args.sender_id} → user_id=${userId}`);
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            user_id: userId,
            message:
              "User identity resolved. Use this user_id for all subsequent memory operations in this session. " +
              "The session will remember it automatically.",
          }),
        },
      ],
    };
  }

  const userId = requireUserId(args, session);
  console.log(`[MCP] tools/call ${name} user=${userId}`);

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
      session_id: args.session_id || "mcp-adapter",
      message: "/memory",
    });
    return { content: [{ type: "text", text: resp.data.response }] };
  }

  if (name === "memory_stats") {
    const resp = await axios.post(`${MNEMOS_URL}/chat`, {
      user_id: userId,
      session_id: args.session_id || "mcp-adapter",
      message: "/memory --mode stats",
    });
    return { content: [{ type: "text", text: resp.data.response }] };
  }

  if (name === "memory_chat") {
    const resp = await axios.post(`${MNEMOS_URL}/chat`, {
      user_id: userId,
      session_id: args.session_id || "mcp-adapter",
      message: args.message,
    });
    return { content: [{ type: "text", text: resp.data.response }] };
  }

  throw new Error(`Unknown tool: ${name}`);
}

async function handleJsonRpc(message) {
  const { id, method, params } = message;

  if (method === "initialize") {
    const sessionId = uuidv4();
    const channel = params?.clientInfo?.channel || "openclaw";
    const senderId = params?.clientInfo?.name || "openclaw";
    const session = { sessionId, channel, sender_id: senderId, user_id: null };

    // Auto-resolve canonical user_id on session creation
    try {
      const bindResp = await axios.post(`${MNEMOS_URL}/api/user/bind`, {
        channel,
        sender_id: senderId,
        display_name: params?.clientInfo?.displayName,
      });
      session.user_id = bindResp.data.user_id;
      console.log(`[MCP] session ${sessionId} auto-resolved → user_id=${session.user_id}`);
    } catch (err) {
      console.warn(`[MCP] session ${sessionId} could not auto-resolve user_id: ${err.message}`);
    }

    sessions.set(sessionId, session);
    return {
      jsonrpc: "2.0",
      id,
      result: {
        protocolVersion: "2024-11-05",
        capabilities: { tools: {} },
        serverInfo: { name: "mnemos-mcp-adapter", version: "1.1.0" },
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
      // Look up session by matching the request — OpenClaw passes sessionId via headers or params
      const sessionId = params?._meta?.sessionId || message.sessionId;
      const session = sessionId ? sessions.get(sessionId) : null;
      const result = await callTool(params.name, params.arguments || {}, session);
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

// Track SSE sessions by MCP sessionId (passed as ?sessionId= query param)
app.post("/mcp/message", async (req, res) => {
  const message = req.body;
  // Attach sessionId from query so handleJsonRpc can look up the session
  if (req.query.sessionId && !message.sessionId) {
    message.sessionId = req.query.sessionId;
  }
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
    const { name, arguments: args, session_id } = req.body;
    const session = session_id ? sessions.get(session_id) : null;
    const result = await callTool(name, args || {}, session);
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
