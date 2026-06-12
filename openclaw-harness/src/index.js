/**
 * MnemOS Visualizer Harness — memory graph UI and API proxy.
 */

require("dotenv").config({ path: require("path").join(__dirname, "../../.env") });
const path = require("path");
const express = require("express");
const cors = require("cors");
const axios = require("axios");

const PORT = process.env.PORT || 3000;
const MNEMOS_URL = (process.env.MNEMOS_URL || process.env.MCP_SERVER_URL || "http://localhost:8000").replace(/\/$/, "");
const MCP_ADAPTER_URL = (process.env.MCP_ADAPTER_URL || "http://localhost:8001").replace(/\/$/, "");

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, "public")));

// ── Health check ──
app.get("/health", async (_req, res) => {
  const status = { status: "ok", harness: true, mnemos: null, mcp_adapter: null };
  try {
    status.mnemos = (await axios.get(`${MNEMOS_URL}/health`, { timeout: 5000 })).data;
  } catch (err) {
    status.status = "degraded";
    status.mnemos_error = err.message;
  }
  try {
    status.mcp_adapter = (await axios.get(`${MCP_ADAPTER_URL}/health`, { timeout: 5000 })).data;
  } catch (err) {
    status.mcp_adapter_error = err.message;
  }
  res.status(status.status === "ok" ? 200 : 503).json(status);
});

// ── Chat proxy (API — used by OpenClaw, scripts, and programmatic clients) ──
app.post("/chat", async (req, res) => {
  try {
    const { user_id, session_id, message } = req.body;
    if (!user_id || !session_id || message === undefined) {
      return res.status(400).json({ error: "user_id, session_id, and message are required" });
    }
    const resp = await axios.post(
      `${MNEMOS_URL}/chat`,
      { user_id, session_id, message },
      { timeout: 120000 }
    );
    res.json(resp.data);
  } catch (err) {
    const code = err.response?.status || 503;
    res.status(code).json({
      error: "Failed to reach MnemOS memory server",
      detail: err.message,
    });
  }
});

// ── Memory visualization API proxy ──
for (const route of ["graph", "events", "metrics"]) {
  app.get(`/api/${route}/:uid`, async (req, res) => {
    try {
      const suffix = route === "events" ? `?${new URLSearchParams(req.query)}` : "";
      const url = `${MNEMOS_URL}/api/${route}/${encodeURIComponent(req.params.uid)}${suffix}`;
      const resp = await axios.get(url, { timeout: 30000 });
      res.json(resp.data);
    } catch (err) {
      res.status(503).json({ error: err.message });
    }
  });
}

// ── Visualizer landing page ──
app.get("/", (_req, res) => {
  res.sendFile(path.join(__dirname, "public", "index.html"));
});

// ── Error handler ──
app.use((err, _req, res, _next) => {
  res.status(500).json({ error: err.message });
});

app.listen(PORT, () => {
  console.log(`MnemOS visualizer on :${PORT} → MnemOS ${MNEMOS_URL}, MCP ${MCP_ADAPTER_URL}`);
  console.log(`Open http://localhost:${PORT} to view the memory graph`);
});
