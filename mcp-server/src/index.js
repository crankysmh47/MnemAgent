#!/usr/bin/env node
/**
 * MnemOS MCP server — exposes memory tools to OpenClaw via stdio or HTTP.
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import axios from "axios";
import cors from "cors";
import express from "express";
import { z } from "zod";

const MNEMOS_URL = (process.env.MNEMOS_URL || "http://localhost:8000").replace(/\/$/, "");
const DEFAULT_PORT = Number(process.env.MCP_PORT || process.env.PORT || 8001);

function parseArgs() {
  const args = process.argv.slice(2);
  let transport = "stdio";
  let port = DEFAULT_PORT;
  for (let i = 0; i < args.length; i += 1) {
    if (args[i] === "--transport" && args[i + 1]) {
      transport = args[i + 1];
      i += 1;
    } else if (args[i] === "--port" && args[i + 1]) {
      port = Number(args[i + 1]);
      i += 1;
    }
  }
  return { transport, port };
}

async function mnemosRequest(method, path, data) {
  const config = { timeout: 120000 };
  if (method === "get") {
    return (await axios.get(`${MNEMOS_URL}${path}`, config)).data;
  }
  return (await axios.post(`${MNEMOS_URL}${path}`, data, config)).data;
}

function createMcpServer() {
  const server = new McpServer({
    name: "mnemos-memory",
    version: "1.0.0",
  });

  server.tool(
    "memory_store",
    "Store a new fact in persistent MnemOS memory (salience-gated)",
    {
      user_id: z.string().describe("Canonical MnemOS user id"),
      entity: z.string(),
      relation: z.string(),
      value: z.string(),
      category: z.string().optional().default("preference"),
      conviction: z.number().min(0).max(1).optional().default(1.0),
    },
    async (args) => {
      const result = await mnemosRequest("post", "/api/memory/store", args);
      return { content: [{ type: "text", text: JSON.stringify(result) }] };
    }
  );

  server.tool(
    "memory_search",
    "Search persistent memory for relevant facts",
    {
      user_id: z.string(),
      query: z.string(),
      top_k: z.number().int().min(1).max(20).optional().default(5),
      category: z.string().optional(),
      min_confidence: z.number().min(0).max(1).optional(),
    },
    async (args) => {
      const params = new URLSearchParams({ query: args.query, top_k: String(args.top_k) });
      if (args.category) params.set("category", args.category);
      if (args.min_confidence !== undefined) {
        params.set("min_confidence", String(args.min_confidence));
      }
      const result = await mnemosRequest(
        "get",
        `/api/memory/search/${encodeURIComponent(args.user_id)}?${params}`
      );
      return { content: [{ type: "text", text: JSON.stringify(result.results) }] };
    }
  );

  server.tool(
    "memory_dump",
    "Get full brain state with confidence levels",
    { user_id: z.string(), format: z.enum(["text", "markdown", "json"]).optional() },
    async (args) => {
      const fmt = args.format ? `?format=${args.format}` : "";
      const result = await mnemosRequest(
        "get",
        `/api/memory/dump/${encodeURIComponent(args.user_id)}${fmt}`
      );
      const text = typeof result === "string" ? result : result.response || JSON.stringify(result);
      return { content: [{ type: "text", text }] };
    }
  );

  server.tool(
    "memory_stats",
    "Get UCB optimization metrics for stored beliefs",
    { user_id: z.string(), format: z.enum(["text", "markdown", "json"]).optional() },
    async (args) => {
      const fmt = args.format ? `?format=${args.format}` : "";
      const result = await mnemosRequest(
        "get",
        `/api/memory/stats/${encodeURIComponent(args.user_id)}${fmt}`
      );
      const text = typeof result === "string" ? result : result.response || JSON.stringify(result);
      return { content: [{ type: "text", text }] };
    }
  );

  server.tool(
    "memory_chat",
    "Send a message through MnemOS memory-augmented chat",
    {
      user_id: z.string(),
      session_id: z.string(),
      message: z.string(),
    },
    async (args) => {
      const result = await mnemosRequest("post", "/chat", args);
      return { content: [{ type: "text", text: result.response }] };
    }
  );

  server.tool(
    "memory_bind_user",
    "Bind a channel sender id to a canonical MnemOS user_id",
    {
      channel: z.string().describe("telegram, discord, whatsapp, slack, webchat"),
      sender_id: z.string(),
      display_name: z.string().optional(),
    },
    async (args) => {
      const result = await mnemosRequest("post", "/api/user/bind", args);
      return { content: [{ type: "text", text: JSON.stringify(result) }] };
    }
  );

  server.tool(
    "memory_resolve_user",
    "Resolve channel sender to canonical user_id (creates binding if missing)",
    {
      channel: z.string(),
      sender_id: z.string(),
      display_name: z.string().optional(),
    },
    async (args) => {
      const result = await mnemosRequest("post", "/api/user/bind", args);
      return { content: [{ type: "text", text: JSON.stringify(result) }] };
    }
  );

  return server;
}

async function startStdio() {
  const server = createMcpServer();
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

async function startHttp(port) {
  const app = express();
  app.use(cors());
  app.use(express.json({ limit: "2mb" }));

  const sessions = new Map();

  app.get("/health", async (_req, res) => {
    try {
      const upstream = await axios.get(`${MNEMOS_URL}/health`, { timeout: 5000 });
      res.json({ status: "ok", service: "mnemos-mcp-server", mnemos: upstream.data });
    } catch (err) {
      res.status(503).json({ status: "degraded", error: err.message });
    }
  });

  app.get("/mcp", async (req, res) => {
    const server = createMcpServer();
    const transport = new SSEServerTransport("/mcp/message", res);
    sessions.set(transport.sessionId, { server, transport });
    res.on("close", () => sessions.delete(transport.sessionId));
    await server.connect(transport);
  });

  app.post("/mcp/message", async (req, res) => {
    const sessionId = req.query.sessionId;
    const session = sessions.get(sessionId);
    if (!session) {
      res.status(404).json({ error: "Unknown MCP session" });
      return;
    }
    await session.transport.handlePostMessage(req, res, req.body);
  });

  app.listen(port, "0.0.0.0", () => {
    console.log(`MnemOS MCP server (http) on :${port} -> ${MNEMOS_URL}`);
  });
}

const { transport, port } = parseArgs();
if (transport === "http" || transport === "streamable-http") {
  startHttp(port).catch((err) => {
    console.error(err);
    process.exit(1);
  });
} else {
  startStdio().catch((err) => {
    console.error(err);
    process.exit(1);
  });
}
