/**
 * MnemAgent Visualizer Harness — memory graph UI and API proxy.
 */

require("dotenv").config({ path: require("path").join(__dirname, "../../.env") });
const path = require("path");
const fs = require("fs");
const os = require("os");
const express = require("express");
const cors = require("cors");
const axios = require("axios");
const { DEMO_USER_ID, seedDemoBrain } = require("./demo-seed");
const { canReadArchive, canMutateThroughHarness } = require("./cloud-policy");
const { randomBytes } = require("node:crypto");
const { createJudgeAuth } = require("./judge-auth");
const { createJudgeRunService } = require("./judge-run-service");

const PORT = process.env.PORT || 3000;
const MNEMOS_URL = (process.env.MNEMOS_URL || process.env.MCP_SERVER_URL || "http://localhost:8000").replace(/\/$/, "");
const MCP_ADAPTER_URL = (process.env.MCP_ADAPTER_URL || "http://localhost:8001").replace(/\/$/, "");
const AUTO_SEED_DEMO = process.env.AUTO_SEED_DEMO !== "false";
const MNEMAGENT_API_TOKEN = (process.env.MNEMAGENT_API_TOKEN || "").trim();
const CLOUD_MODE = process.env.MNEMAGENT_ENV === "cloud";
if (CLOUD_MODE && (!process.env.JUDGE_ACCESS_CODE || !process.env.JUDGE_SESSION_SECRET)) {
  throw new Error("Cloud mode requires JUDGE_ACCESS_CODE and JUDGE_SESSION_SECRET.");
}
const judgeAuth = createJudgeAuth({
  accessCode: process.env.JUDGE_ACCESS_CODE || "mnemcode-local-judge",
  sessionSecret: process.env.JUDGE_SESSION_SECRET || randomBytes(48).toString("hex"),
  secure: CLOUD_MODE,
});
const judgeRuns = createJudgeRunService();

function mnemosConfig(config = {}) {
  const headers = { ...(config.headers || {}) };
  if (MNEMAGENT_API_TOKEN) {
    headers.Authorization = `Bearer ${MNEMAGENT_API_TOKEN}`;
  }
  return { ...config, headers };
}

function resolveSetupUserId() {
  if (process.env.MNEMOS_DEFAULT_USER_ID) {
    return process.env.MNEMOS_DEFAULT_USER_ID.trim();
  }
  const configDir = process.env.OPENCLAW_CONFIG_DIR || path.join(os.homedir(), ".openclaw");
  const userFile = path.join(configDir, "mnemos-user-id.txt");
  try {
    if (fs.existsSync(userFile)) {
      const id = fs.readFileSync(userFile, "utf8").trim();
      if (id) return id;
    }
  } catch {
    /* ignore */
  }
  return null;
}

async function resolveCanonicalUserId() {
  // Priority 1: env override
  if (process.env.MNEMOS_DEFAULT_USER_ID) {
    return process.env.MNEMOS_DEFAULT_USER_ID.trim();
  }
  // Priority 2: try MnemAgent API to get the canonical user_id (same one the agent uses)
  try {
    const resp = await axios.post(`${MNEMOS_URL}/api/user/bind`, {
      channel: "openclaw",
      sender_id: process.env.OPENCLAW_AGENT_NAME || "main",
    }, mnemosConfig({ timeout: 5000 }));
    if (resp.data?.user_id) {
      return resp.data.user_id;
    }
  } catch {
    /* MnemAgent not reachable — fall through to file-based */
  }
  // Priority 3: read from setup-generated file
  return resolveSetupUserId();
}

const app = express();
app.disable("x-powered-by");
app.use(cors({ origin: false }));
app.use(express.json());
app.use((_req, res, next) => {
  res.set("X-Content-Type-Options", "nosniff");
  res.set("X-Frame-Options", "DENY");
  res.set("Referrer-Policy", "same-origin");
  res.set("Permissions-Policy", "camera=(), microphone=(), geolocation=()");
  next();
});
app.use((req, res, next) => {
  if (!req.path.startsWith("/judge/") && !req.path.startsWith("/api/judge/") && !canMutateThroughHarness(req.method, CLOUD_MODE)) {
    return res.status(403).json({ error: "Browser mutations are disabled in cloud mode; use the protected OpenClaw/MCP path." });
  }
  next();
});

function verifyJudge(req, { mutable = false } = {}) {
  return judgeAuth.verify({
    cookieHeader: req.headers.cookie,
    csrfHeader: req.headers["x-csrf-token"],
    origin: req.headers.origin,
    host: req.headers.host,
    mutable,
  });
}

app.post("/judge/session", (req, res) => {
  try {
    const issued = judgeAuth.login({ accessCode: req.body?.accessCode, ip: req.ip });
    res.set("Set-Cookie", issued.cookie);
    res.json({ authenticated: true, csrf: issued.csrf });
  } catch (error) {
    const locked = /locked/i.test(error.message);
    res.status(locked ? 429 : 401).json({ error: locked ? "Judge access is temporarily locked." : "Invalid judge access code." });
  }
});

app.get("/api/judge/session", (req, res) => {
  try { verifyJudge(req); res.json({ authenticated: true }); }
  catch { res.status(401).json({ authenticated: false }); }
});

app.get("/api/judge/scenarios", (_req, res) => res.json({
  model: process.env.JUDGE_MODEL || "openrouter/deepseek/deepseek-v4-flash",
  repository: process.env.JUDGE_DEMO_REPOSITORY || "crankysmh47/MnemAgent-Agent-Lab",
  scenarios: [
    { issueNumber: 1, title: "Retry transient configuration failures", outcome: "A tested patch and review memory" },
    { issueNumber: 2, title: "Apply repository timeout conventions", outcome: "Fresh-session repository recall" },
    { issueNumber: 3, title: "Bound incoming request bodies", outcome: "A draft PR approval demonstration" },
  ],
}));

app.post("/api/judge/runs", async (req, res) => {
  try {
    verifyJudge(req, { mutable: true });
    const run = await judgeRuns.create(req.body || {});
    res.status(201).json(run);
  } catch (error) {
    res.status(/session|csrf|origin/i.test(error.message) ? 403 : 400).json({ error: "The judge run could not be started." });
  }
});

app.get("/api/judge/runs/:id", (req, res) => {
  try { verifyJudge(req); } catch { return res.status(401).json({ error: "Judge access required." }); }
  const run = judgeRuns.get(req.params.id);
  if (!run) return res.status(404).json({ error: "Run not found." });
  res.json({ ...run, events: judgeRuns.events(req.params.id, req.query.after) });
});

// Prevent stale HTML/CSS in browsers during active development
app.use((req, res, next) => {
  if (
    req.method === "GET" &&
    (req.path === "/" ||
      req.path === "/visualizer" ||
      req.path.endsWith(".html") ||
      req.path.endsWith(".css") ||
      req.path.endsWith(".js") ||
      req.path.endsWith(".svg") ||
      req.path.endsWith(".png"))
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
    const graph = await axios.get(`${MNEMOS_URL}/api/graph/${encodeURIComponent(DEMO_USER_ID)}`, mnemosConfig({ timeout: 5000 }));
    status.demo_brain = {
      beliefs: graph.data?.beliefs?.length ?? 0,
      edges: graph.data?.edges?.length ?? 0,
    };
  } catch (err) {
    status.demo_brain_error = err.message;
  }
  if (CLOUD_MODE) {
    return res.status(status.status === "ok" ? 200 : 503).json({
      status: status.status,
      services: { memory: Boolean(status.mnemos), mcp: Boolean(status.mcp_adapter), demo: Boolean(status.demo_brain) },
    });
  }
  res.status(status.status === "ok" ? 200 : 503).json(status);
});

app.get("/api/setup/default-user-id", async (_req, res) => {
  const userId = await resolveCanonicalUserId();
  res.json({ user_id: userId });
});

// ── Whoami — returns the canonical user_id the agent uses ──
app.get("/api/user/whoami", async (_req, res) => {
  try {
    const userId = await resolveCanonicalUserId();
    if (userId) {
      res.json({ user_id: userId, source: "resolved" });
    } else {
      res.json({ user_id: null, hint: "Run setup script or set MNEMOS_DEFAULT_USER_ID" });
    }
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
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
      mnemosConfig({ timeout: 120000 })
    );
    res.json(resp.data);
  } catch (err) {
    const code = err.response?.status || 503;
    res.status(code).json({
      error: "Failed to reach MnemAgent memory server",
      detail: err.message,
    });
  }
});

// ── Memory store proxy (eval + visualizer seeding) ──
app.post("/api/memory/store", async (req, res) => {
  try {
    const resp = await axios.post(`${MNEMOS_URL}/api/memory/store`, req.body, mnemosConfig({ timeout: 120000 }));
    res.json(resp.data);
  } catch (err) {
    res.status(err.response?.status || 503).json({ error: err.message, detail: err.response?.data });
  }
});

app.post("/api/memory/store/batch", async (req, res) => {
  try {
    const resp = await axios.post(`${MNEMOS_URL}/api/memory/store/batch`, req.body, mnemosConfig({ timeout: 120000 }));
    res.json(resp.data);
  } catch (err) {
    res.status(err.response?.status || 503).json({ error: err.message, detail: err.response?.data });
  }
});

// ── Demo brain seed ──
app.post("/api/demo/seed", async (req, res) => {
  try {
    const force = Boolean(req.body?.force);
    const result = await seedDemoBrain(axios, MNEMOS_URL, { force, requestConfig: mnemosConfig() });
    res.json(result);
  } catch (err) {
    res.status(err.response?.status || 503).json({ error: err.message, detail: err.response?.data });
  }
});

app.get("/api/demo/status", async (_req, res) => {
  try {
    const graph = await axios.get(`${MNEMOS_URL}/api/graph/${encodeURIComponent(DEMO_USER_ID)}`, mnemosConfig({ timeout: 30000 }));
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
      if (CLOUD_MODE && !canReadArchive(req.params.uid, resolveSetupUserId())) {
        return res.status(403).json({ error: "Archive namespace is not available." });
      }
      const query = new URLSearchParams(req.query).toString();
      const suffix = query ? `?${query}` : "";
      const url = `${MNEMOS_URL}/api/${route}/${encodeURIComponent(req.params.uid)}${suffix}`;
      const resp = await axios.get(url, mnemosConfig({ timeout: 30000 }));
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
app.get("/diag", (_req, res) => {
  res.set("Cache-Control", "no-store");
  res.sendFile(path.join(__dirname, "public", "diag.html"));
});

// ── Error handler ──
app.use((err, _req, res, _next) => {
  res.status(500).json({ error: err.message });
});

async function ensureDemoBrain(retries = 12) {
  for (let i = 0; i < retries; i += 1) {
    try {
      await axios.get(`${MNEMOS_URL}/health`, { timeout: 5000 });
      const result = await seedDemoBrain(axios, MNEMOS_URL, { requestConfig: mnemosConfig() });
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
  console.warn("Demo brain seed skipped — MnemAgent not reachable yet");
}

app.listen(PORT, () => {
  console.log(`MnemAgent visualizer on :${PORT} → MnemAgent ${MNEMOS_URL}, MCP ${MCP_ADAPTER_URL}`);
  console.log(`Open http://localhost:${PORT}?user=${DEMO_USER_ID} to view the memory graph`);
  if (AUTO_SEED_DEMO) {
    ensureDemoBrain();
  }
});
