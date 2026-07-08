/**
 * Demo brain seed — beliefs with hub entities + cross-cluster synaptic links.
 * Used by harness startup and /api/demo/seed.
 */

const DEMO_USER_ID = "demo-brain";
const DEMO_TARGET_COUNT = 62;
const BATCH_CHUNK = 12;
const BATCH_TIMEOUT_MS = 600000;

const DEMO_CORE = [
  // Phoenix project cluster
  { entity: "phoenix", relation: "codename", value: "Phoenix", category: "system_state", conviction: 0.95 },
  { entity: "phoenix", relation: "lead", value: "Sarah", category: "persona", conviction: 0.9 },
  { entity: "phoenix", relation: "deadline", value: "March_15", category: "system_state", conviction: 0.9 },
  { entity: "phoenix", relation: "architecture", value: "microservices", category: "system_state", conviction: 0.88 },
  { entity: "phoenix", relation: "auth", value: "Auth0", category: "system_state", conviction: 0.85 },
  { entity: "phoenix", relation: "payments", value: "Stripe_Connect", category: "system_state", conviction: 0.85 },
  { entity: "phoenix", relation: "cache", value: "Redis", category: "system_state", conviction: 0.82 },
  { entity: "phoenix", relation: "compliance", value: "regul8-v2", category: "system_state", conviction: 0.8 },
  // User persona cluster
  { entity: "user", relation: "affiliation", value: "FAST_student", category: "persona", conviction: 0.95 },
  { entity: "user", relation: "role", value: "backend_lead", category: "persona", conviction: 0.9 },
  { entity: "user", relation: "team", value: "platform_squad", category: "persona", conviction: 0.85 },
  { entity: "user", relation: "timezone", value: "Asia/Karachi", category: "persona", conviction: 0.8 },
  // Backend stack cluster
  { entity: "backend", relation: "language", value: "Python", category: "system_state", conviction: 0.95 },
  { entity: "backend", relation: "framework", value: "FastAPI", category: "system_state", conviction: 0.92 },
  { entity: "backend", relation: "database", value: "PostgreSQL", category: "system_state", conviction: 0.9 },
  { entity: "backend", relation: "orm", value: "SQLAlchemy", category: "system_state", conviction: 0.85 },
  { entity: "backend", relation: "testing", value: "pytest", category: "system_state", conviction: 0.82 },
  // Frontend cluster
  { entity: "frontend", relation: "framework", value: "Next.js", category: "system_state", conviction: 0.9 },
  { entity: "frontend", relation: "styling", value: "Tailwind_CSS", category: "system_state", conviction: 0.88 },
  { entity: "frontend", relation: "state", value: "Zustand", category: "system_state", conviction: 0.8 },
  { entity: "frontend", relation: "api_client", value: "TanStack_Query", category: "system_state", conviction: 0.78 },
  // Deployment cluster
  { entity: "deployment", relation: "cloud", value: "AWS", category: "system_state", conviction: 0.9 },
  { entity: "deployment", relation: "cicd", value: "GitHub_Actions", category: "system_state", conviction: 0.88 },
  { entity: "deployment", relation: "container", value: "Docker", category: "system_state", conviction: 0.85 },
  { entity: "deployment", relation: "orchestration", value: "ECS", category: "system_state", conviction: 0.82 },
  // Preferences
  { entity: "language", relation: "also_knows", value: "Rust", category: "preference", conviction: 0.88 },
  { entity: "code_style", relation: "prefers", value: "minimal_comments", category: "preference", conviction: 0.85 },
  { entity: "editor", relation: "prefers", value: "VS_Code", category: "preference", conviction: 0.8 },
  { entity: "api_format", relation: "prefers", value: "JSON", category: "preference", conviction: 0.78 },
  { entity: "logging", relation: "prefers", value: "structured_JSON", category: "preference", conviction: 0.75 },
  { entity: "monitoring", relation: "prefers", value: "Prometheus", category: "preference", conviction: 0.72 },
  { entity: "documentation", relation: "prefers", value: "Markdown", category: "preference", conviction: 0.7 },
];

/** Bridge + shared-concept facts — targets overlap subjects so synapses span clusters. */
const DEMO_LINKS = [
  { entity: "Python", relation: "powers", value: "backend", category: "system_state", conviction: 0.91 },
  { entity: "Python", relation: "used_in", value: "phoenix", category: "system_state", conviction: 0.89 },
  { entity: "FastAPI", relation: "serves", value: "phoenix", category: "system_state", conviction: 0.9 },
  { entity: "FastAPI", relation: "exposes", value: "backend", category: "system_state", conviction: 0.88 },
  { entity: "PostgreSQL", relation: "stores", value: "phoenix", category: "system_state", conviction: 0.87 },
  { entity: "PostgreSQL", relation: "backs", value: "backend", category: "system_state", conviction: 0.86 },
  { entity: "Redis", relation: "caches_for", value: "phoenix", category: "system_state", conviction: 0.85 },
  { entity: "Redis", relation: "accelerates", value: "backend", category: "system_state", conviction: 0.84 },
  { entity: "Docker", relation: "packages", value: "backend", category: "system_state", conviction: 0.88 },
  { entity: "Docker", relation: "deploys", value: "phoenix", category: "system_state", conviction: 0.86 },
  { entity: "Docker", relation: "used_by", value: "deployment", category: "system_state", conviction: 0.85 },
  { entity: "AWS", relation: "hosts", value: "phoenix", category: "system_state", conviction: 0.9 },
  { entity: "AWS", relation: "runs", value: "deployment", category: "system_state", conviction: 0.88 },
  { entity: "Next.js", relation: "consumes", value: "backend", category: "system_state", conviction: 0.87 },
  { entity: "Next.js", relation: "fronts", value: "phoenix", category: "system_state", conviction: 0.85 },
  { entity: "Auth0", relation: "secures", value: "phoenix", category: "system_state", conviction: 0.88 },
  { entity: "Stripe_Connect", relation: "bills_for", value: "phoenix", category: "system_state", conviction: 0.86 },
  { entity: "Prometheus", relation: "monitors", value: "phoenix", category: "system_state", conviction: 0.83 },
  { entity: "Prometheus", relation: "scrapes", value: "backend", category: "system_state", conviction: 0.82 },
  { entity: "Sarah", relation: "leads", value: "phoenix", category: "persona", conviction: 0.92 },
  { entity: "Sarah", relation: "mentors", value: "user", category: "persona", conviction: 0.88 },
  { entity: "platform_squad", relation: "owns", value: "phoenix", category: "persona", conviction: 0.87 },
  { entity: "platform_squad", relation: "maintains", value: "backend", category: "persona", conviction: 0.86 },
  { entity: "microservices", relation: "spans", value: "backend", category: "system_state", conviction: 0.84 },
  { entity: "microservices", relation: "includes", value: "frontend", category: "system_state", conviction: 0.84 },
  { entity: "JSON", relation: "serializes", value: "api_format", category: "preference", conviction: 0.8 },
  { entity: "Markdown", relation: "documents", value: "phoenix", category: "preference", conviction: 0.78 },
  { entity: "pytest", relation: "validates", value: "backend", category: "system_state", conviction: 0.83 },
  { entity: "GitHub_Actions", relation: "ships", value: "phoenix", category: "system_state", conviction: 0.85 },
  { entity: "ECS", relation: "orchestrates", value: "phoenix", category: "system_state", conviction: 0.84 },
];

const DEMO_FACTS = [...DEMO_CORE, ...DEMO_LINKS];

function factKey(fact) {
  return `${fact.entity}|${fact.relation}`;
}

async function storeBatch(axios, mnemosUrl, userId, facts, { refreshVitality = false, requestConfig = {} } = {}) {
  const payload = facts.map((fact) => ({ ...fact, user_id: userId }));
  for (let i = 0; i < payload.length; i += BATCH_CHUNK) {
    const chunk = payload.slice(i, i + BATCH_CHUNK);
    const isLast = i + BATCH_CHUNK >= payload.length;
    await axios.post(
      `${mnemosUrl}/api/memory/store/batch`,
      {
        user_id: userId,
        facts: chunk,
        skip_maintenance: true,
        refresh_vitality: refreshVitality && isLast,
      },
      { timeout: BATCH_TIMEOUT_MS, ...(requestConfig || {}) }
    );
  }
}

async function seedDemoBrain(axios, mnemosUrl, { force = false, requestConfig = {} } = {}) {
  const userId = DEMO_USER_ID;
  const graphUrl = `${mnemosUrl}/api/graph/${encodeURIComponent(userId)}`;

  const existingKeys = new Set();
  let beliefCount = 0;
  try {
    const existing = await axios.get(graphUrl, { timeout: 30000, ...(requestConfig || {}) });
    beliefCount = existing.data?.beliefs?.length ?? 0;
    (existing.data?.beliefs || []).forEach((b) => {
      existingKeys.add(`${b.entity_source}|${b.relation}`);
    });
  } catch {
    // proceed with seed if graph check fails
  }

  const missing = DEMO_FACTS.filter((f) => !existingKeys.has(factKey(f)));
  const needsSeed = force || missing.length > 0 || beliefCount < DEMO_TARGET_COUNT - 2;

  if (!needsSeed) {
    const graph = await axios.get(graphUrl, { timeout: 30000, ...(requestConfig || {}) });
    return {
      user_id: userId,
      seeded: false,
      reason: "complete",
      expected: DEMO_TARGET_COUNT,
      beliefs: graph.data?.beliefs?.length ?? 0,
      edges: graph.data?.edges?.length ?? 0,
    };
  }

  const toStore = force ? DEMO_FACTS : missing;
  await storeBatch(axios, mnemosUrl, userId, toStore, { refreshVitality: true, requestConfig });

  const graph = await axios.get(graphUrl, { timeout: 30000, ...(requestConfig || {}) });
  return {
    user_id: userId,
    seeded: true,
    reason: force ? "force_reseed" : "missing_facts",
    added: toStore.length,
    expected: DEMO_TARGET_COUNT,
    beliefs: graph.data?.beliefs?.length ?? 0,
    edges: graph.data?.edges?.length ?? 0,
  };
}

module.exports = {
  DEMO_USER_ID,
  DEMO_CORE,
  DEMO_LINKS,
  DEMO_FACTS,
  DEMO_TARGET_COUNT,
  seedDemoBrain,
};
