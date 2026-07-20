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
const { canMutateThroughHarness, archiveAccessContext } = require("./cloud-policy");
const { randomBytes } = require("node:crypto");
const { createJudgeAuth } = require("./judge-auth");
const { createJudgeRunService } = require("./judge-run-service");
const { createJudgeChatService } = require("./judge-chat-service");
const { createJudgeSessionStore } = require("./judge-session-store");
const { createJudgeEvidenceStore } = require("./judge-evidence");
const { createBrokerClient } = require("./broker-client");
const { createInternalHmacVerifier } = require("./internal-hmac");

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
const judgeChats = createJudgeChatService();
const judgeSessions = createJudgeSessionStore();
const judgeEvidence = createJudgeEvidenceStore();
const brokerClient = createBrokerClient({ secret: process.env.WORKSPACE_HMAC_SECRET || 'local-development-hmac-secret-change-for-cloud-12345' });
const internalVerifier = createInternalHmacVerifier({ secret: process.env.WORKSPACE_HMAC_SECRET || 'local-development-hmac-secret-change-for-cloud-12345' });
const settledChatTurns = new Set();
const settledCodingRuns = new Set();
const enrichedCodingRuns = new Set();

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
if (CLOUD_MODE) app.set('trust proxy', 1);
app.disable("x-powered-by");
app.use(cors({ origin: false }));
app.use(express.json({ limit: '128kb', verify: (req, _res, buffer) => { req.rawBody = buffer.toString('utf8'); } }));
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
    const sponsored = judgeSessions.create({ sessionId: issued.sessionId, namespace: issued.namespace });
    res.set("Set-Cookie", issued.cookie);
    res.json({ authenticated: true, csrf: issued.csrf, namespace: issued.namespace, expiresAt: issued.expiresAt, quota: sponsored.quota });
  } catch (error) {
    const locked = /locked/i.test(error.message);
    res.status(locked ? 429 : 401).json({ error: locked ? "Judge access is temporarily locked." : "Invalid judge access code." });
  }
});

app.get("/api/judge/session", (req, res) => {
  try {
    const identity = verifyJudge(req);
    const sponsored = judgeSessions.get(identity.sessionId);
    res.json({
      authenticated: true,
      csrf: identity.csrf,
      namespace: identity.namespace,
      expiresAt: sponsored.expiresAt,
      quota: sponsored.quota,
      chatHistory: judgeChats.list(identity.sessionId),
    });
  }
  catch { res.status(401).json({ authenticated: false }); }
});

app.get("/api/judge/scenarios", (_req, res) => res.json({
  model: process.env.JUDGE_MODEL || "deepseek-api/deepseek-v4-flash",
  repository: process.env.JUDGE_DEMO_REPOSITORY || "crankysmh47/MnemBench",
  scenarios: [{ issueNumber: 1, title: "MnemBench · inverted contradiction score", outcome: "Repository recall, regression test, bounded fix, and approval-gated draft PR" }],
}));

app.post('/api/judge/internal/events', (req, res) => {
  try {
    internalVerifier.verify({ method: req.method, path: req.path, body: req.rawBody || '', headers: req.headers });
    const event = judgeEvidence.ingest(req.body?.runId, req.body || {});
    judgeRuns.appendInternal(req.body.runId, event);
    res.status(202).json({ accepted: true });
  } catch { res.status(401).json({ error: 'Internal evidence rejected.' }); }
});

app.post("/api/judge/chat", (req, res) => {
  try {
    const identity = verifyJudge(req, { mutable: true });
    const quota = judgeSessions.reserve(identity.sessionId, 'chat').quota;
    try {
      const turn = judgeChats.create({ ownerSessionId: identity.sessionId, namespace: identity.namespace, message: req.body?.message });
      res.status(202).json({ ...turn, quota });
    } catch (error) {
      judgeSessions.release(identity.sessionId, 'chat');
      throw error;
    }
  } catch (error) {
    res.status(/session|csrf|origin/i.test(error.message) ? 403 : 400).json({ error: "The sponsored chat turn could not be started." });
  }
});

app.get("/api/judge/chat/:id", (req, res) => {
  try {
    const identity = verifyJudge(req);
    const turn = judgeChats.get(req.params.id, identity.sessionId);
    if ((turn.status === 'completed' || turn.status === 'failed') && !settledChatTurns.has(turn.id)) {
      settledChatTurns.add(turn.id);
      if (turn.status === 'failed') judgeSessions.release(identity.sessionId, 'chat');
      else judgeSessions.settle(identity.sessionId, 'chat');
    }
    res.json({ ...turn, quota: judgeSessions.get(identity.sessionId).quota });
  } catch { res.status(404).json({ error: "Judge chat turn not found." }); }
});

app.post("/api/judge/runs", (req, res) => {
  try {
    const identity = verifyJudge(req, { mutable: true });
    const quota = judgeSessions.reserve(identity.sessionId, 'coding').quota;
    try {
      const run = judgeRuns.create({
        ownerSessionId: identity.sessionId,
        namespace: identity.namespace,
        sessionId: `judge-code-${randomBytes(12).toString('hex')}`,
        issueNumber: Number(req.body?.issueNumber),
        message: String(req.body?.message || '').trim() || 'Solve MnemBench issue #1 using the repository conventions you remember. Write the regression test first, fix only the contradiction dimension aggregation, run both fixed Python test commands, and show the exact diff.',
      });
      res.status(202).json({ ...run, quota });
    } catch (error) {
      judgeSessions.release(identity.sessionId, 'coding');
      throw error;
    }
  } catch (error) {
    res.status(/session|csrf|origin/i.test(error.message) ? 403 : 400).json({ error: "The judge run could not be started." });
  }
});

app.get("/api/judge/runs/:id", (req, res) => {
  try {
    const identity = verifyJudge(req);
    const run = judgeRuns.get(req.params.id, identity.sessionId);
    if ((run.status === 'completed' || run.status === 'failed') && !settledCodingRuns.has(run.id)) {
      settledCodingRuns.add(run.id);
      if (run.status === 'failed') judgeSessions.release(identity.sessionId, 'coding');
      else judgeSessions.settle(identity.sessionId, 'coding');
    }
    if (run.status === 'completed' && !enrichedCodingRuns.has(run.id)) {
      enrichedCodingRuns.add(run.id);
      axios.get(`${MNEMOS_URL}/api/memory/search/${encodeURIComponent(identity.namespace)}`, mnemosConfig({
        timeout: 5_000,
        params: { query: 'contradiction dimension score orientation regression tests repository rules', top_k: 4, scope_type: 'repository', scope_id: 'crankysmh47/MnemBench' },
      })).then(response => {
        for (const memory of response.data?.results || []) {
          const event = judgeEvidence.ingest(run.id, { type: 'memory.retrieved', detail: { scope: 'repository/crankysmh47/MnemBench', entity: memory.entity_source, relation: memory.relation, value: memory.entity_target } });
          judgeRuns.appendInternal(run.id, event);
        }
      }).catch(() => {});
    }
    res.json({ ...run, events: judgeRuns.events(req.params.id, identity.sessionId, req.query.after), evidence: judgeEvidence.get(run.id), quota: judgeSessions.get(identity.sessionId).quota });
  } catch { res.status(404).json({ error: "Judge run not found." }); }
});

app.post('/api/judge/runs/:id/approve', async (req, res) => {
  try {
    const identity = verifyJudge(req, { mutable: true });
    const run = judgeRuns.get(req.params.id, identity.sessionId);
    const evidence = judgeEvidence.get(run.id);
    if (req.body?.confirmed !== true || run.status !== 'completed' || !evidence.readyForApproval || evidence.pr) throw new Error('Run is not ready for publication.');
    const metadata = {
      runId: run.id,
      title: 'fix: correct inverted contradiction dimension score',
      body: 'Closes #1.\n\nGenerated through the MnemAgent sponsored judge workflow after repository-scoped memory retrieval and constrained test execution.',
    };
    const approval = await brokerClient.prepare(evidence.workspaceId, metadata);
    const pr = await brokerClient.open(evidence.workspaceId, { ...metadata, token: approval.token, expiresAt: approval.expiresAt });
    judgeSessions.consumePublication(identity.sessionId);
    res.status(201).json({ evidence: judgeEvidence.setPr(run.id, pr), quota: judgeSessions.get(identity.sessionId).quota });
  } catch (error) {
    res.status(/session|csrf|origin/i.test(error.message) ? 403 : 400).json({ error: 'The draft PR could not be opened.' });
  }
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
      let sessionUserId = null;
      try { sessionUserId = verifyJudge(req).namespace; } catch { /* anonymous demo visit */ }
      const access = archiveAccessContext({
        cloudMode: CLOUD_MODE,
        userId: req.params.uid,
        judgeUserId: resolveSetupUserId(),
        sessionUserId,
        repository: process.env.JUDGE_DEMO_REPOSITORY || "crankysmh47/MnemBench",
        query: req.query,
      });
      if (!access.allowed) {
        return res.status(403).json({ error: "Archive namespace is not available." });
      }
      const suffix = access.queryString ? `?${access.queryString}` : "";
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
