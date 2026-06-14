/**
 * MnemOS Visualizer Harness — memory graph UI and API proxy.
 */

require("dotenv").config({ path: require("path").join(__dirname, "../../.env") });
const path = require("path");
const express = require("express");
const cors = require("cors");
const axios = require("axios");
const { DEMO_USER_ID, seedDemoBrain } = require("./demo-seed");

const PORT = process.env.PORT || 3000;
const MNEMOS_URL = (process.env.MNEMOS_URL || process.env.MCP_SERVER_URL || "http://localhost:8000").replace(/\/$/, "");
const MCP_ADAPTER_URL = (process.env.MCP_ADAPTER_URL || "http://localhost:8001").replace(/\/$/, "");
const AUTO_SEED_DEMO = process.env.AUTO_SEED_DEMO !== "false";

const app = express();
app.use(cors());
app.use(express.json());

// Prevent stale HTML/CSS in browsers during active development
app.use((req, res, next) => {
  if (
    req.method === "GET" &&
    (req.path === "/" ||
      req.path === "/visualizer" ||
      req.path.endsWith(".html") ||
      req.path.endsWith(".css"))
  ) {
    res.set("Cache-Control", "no-store, no-cache, must-revalidate, proxy-revalidate");
    res.set("Pragma", "no-cache");
    res.set("Expires", "0");
  }
  next();
});

app.use(express.static(path.join(__dirname, "public"), { etag: false, lastModified: false }));
// Bundled viz deps (avoid CDN failures → "Offline" in browser)
app.use("/vendor/d3", express.static(path.join(__dirname, "../node_modules/d3/dist")));
app.use(
  "/vendor/chart.js",
  express.static(path.join(__dirname, "../node_modules/chart.js/dist"))
);

// ── Health check ──
app.get("/health", async (_req, res) => {
  const status = { status: "ok", harness: true, mnemos: null, mcp_adapter: null, demo_brain: null };
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
  try {
    const graph = await axios.get(`${MNEMOS_URL}/api/graph/${encodeURIComponent(DEMO_USER_ID)}`, { timeout: 5000 });
    status.demo_brain = {
      beliefs: graph.data?.beliefs?.length ?? 0,
      edges: graph.data?.edges?.length ?? 0,
    };
  } catch (err) {
    status.demo_brain_error = err.message;
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

// ── Memory store proxy (eval + visualizer seeding) ──
app.post("/api/memory/store", async (req, res) => {
  try {
    const resp = await axios.post(`${MNEMOS_URL}/api/memory/store`, req.body, { timeout: 120000 });
    res.json(resp.data);
  } catch (err) {
    res.status(err.response?.status || 503).json({ error: err.message, detail: err.response?.data });
  }
});

app.post("/api/memory/store/batch", async (req, res) => {
  try {
    const resp = await axios.post(`${MNEMOS_URL}/api/memory/store/batch`, req.body, { timeout: 120000 });
    res.json(resp.data);
  } catch (err) {
    res.status(err.response?.status || 503).json({ error: err.message, detail: err.response?.data });
  }
});

// ── Demo brain seed ──
app.post("/api/demo/seed", async (req, res) => {
  try {
    const force = Boolean(req.body?.force);
    const result = await seedDemoBrain(axios, MNEMOS_URL, { force });
    res.json(result);
  } catch (err) {
    res.status(err.response?.status || 503).json({ error: err.message, detail: err.response?.data });
  }
});

app.get("/api/demo/status", async (_req, res) => {
  try {
    const graph = await axios.get(`${MNEMOS_URL}/api/graph/${encodeURIComponent(DEMO_USER_ID)}`, { timeout: 30000 });
    res.json({
      user_id: DEMO_USER_ID,
      beliefs: graph.data?.beliefs?.length ?? 0,
      edges: graph.data?.edges?.length ?? 0,
      url: `http://localhost:${PORT}?user=${DEMO_USER_ID}`,
    });
  } catch (err) {
    res.status(503).json({ error: err.message });
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
const visualizerPage = (_req, res) => {
  res.set("Cache-Control", "no-store, no-cache, must-revalidate, proxy-revalidate");
  res.set("Pragma", "no-cache");
  res.set("Expires", "0");
  res.sendFile(path.join(__dirname, "public", "index.html"));
};
app.get("/", visualizerPage);
app.get("/visualizer", visualizerPage);

// ── Error handler ──
app.use((err, _req, res, _next) => {
  res.status(500).json({ error: err.message });
});

async function ensureDemoBrain(retries = 12) {
  for (let i = 0; i < retries; i += 1) {
    try {
      await axios.get(`${MNEMOS_URL}/health`, { timeout: 5000 });
      const result = await seedDemoBrain(axios, MNEMOS_URL);
      if (result.seeded) {
        console.log(`Demo brain seeded: ${result.beliefs} beliefs, ${result.edges} edges (${DEMO_USER_ID})`);
      } else {
        console.log(`Demo brain ready: ${result.beliefs} beliefs, ${result.edges} edges (${DEMO_USER_ID})`);
      }
      return;
    } catch (err) {
      await new Promise((r) => setTimeout(r, 5000));
    }
  }
  console.warn("Demo brain seed skipped — MnemOS not reachable yet");
}

app.listen(PORT, () => {
  console.log(`MnemOS visualizer on :${PORT} → MnemOS ${MNEMOS_URL}, MCP ${MCP_ADAPTER_URL}`);
  console.log(`Open http://localhost:${PORT}?user=${DEMO_USER_ID} to view the memory graph`);
  if (AUTO_SEED_DEMO) {
    ensureDemoBrain();
  }
});
