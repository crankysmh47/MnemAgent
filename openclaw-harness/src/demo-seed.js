/**
 * Demo brain seed — 32 beliefs with hub entities for visible synaptic edges.
 * Used by harness startup and /api/demo/seed.
 */

const DEMO_USER_ID = "demo-brain";

const DEMO_FACTS = [
  // Phoenix project cluster (shared entity → interconnections)
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
  // Preferences (golden vivid nodes)
  { entity: "language", relation: "prefers", value: "Python", category: "preference", conviction: 1.0 },
  { entity: "code_style", relation: "prefers", value: "minimal_comments", category: "preference", conviction: 0.85 },
  { entity: "editor", relation: "prefers", value: "VS_Code", category: "preference", conviction: 0.8 },
  { entity: "api_format", relation: "prefers", value: "JSON", category: "preference", conviction: 0.78 },
  { entity: "logging", relation: "prefers", value: "structured_JSON", category: "preference", conviction: 0.75 },
  { entity: "monitoring", relation: "prefers", value: "Prometheus", category: "preference", conviction: 0.72 },
  { entity: "documentation", relation: "prefers", value: "Markdown", category: "preference", conviction: 0.7 },
];

async function seedDemoBrain(axios, mnemosUrl, { force = false } = {}) {
  const userId = DEMO_USER_ID;
  const graphUrl = `${mnemosUrl}/api/graph/${encodeURIComponent(userId)}`;

  try {
    const existing = await axios.get(graphUrl, { timeout: 30000 });
    const beliefCount = existing.data?.beliefs?.length ?? 0;
    if (!force && beliefCount >= 8) {
      return {
        user_id: userId,
        seeded: false,
        reason: "already_populated",
        beliefs: beliefCount,
        edges: existing.data?.edges?.length ?? 0,
      };
    }
  } catch {
    // proceed with seed if graph check fails
  }

  await axios.post(
    `${mnemosUrl}/api/memory/store/batch`,
    { user_id: userId, facts: DEMO_FACTS },
    { timeout: 120000 }
  );

  // Contradiction arc demo: supersede Express → FastAPI on backend framework
  await axios.post(
    `${mnemosUrl}/api/memory/store`,
    {
      user_id: userId,
      entity: "backend",
      relation: "framework",
      value: "Express",
      category: "system_state",
      conviction: 0.9,
    },
    { timeout: 60000 }
  );
  await axios.post(
    `${mnemosUrl}/api/memory/store`,
    {
      user_id: userId,
      entity: "backend",
      relation: "framework",
      value: "FastAPI",
      category: "system_state",
      conviction: 0.95,
    },
    { timeout: 60000 }
  );

  const graph = await axios.get(graphUrl, { timeout: 30000 });
  return {
    user_id: userId,
    seeded: true,
    beliefs: graph.data?.beliefs?.length ?? 0,
    edges: graph.data?.edges?.length ?? 0,
  };
}

module.exports = { DEMO_USER_ID, DEMO_FACTS, seedDemoBrain };
