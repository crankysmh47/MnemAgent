const CATEGORY_ALIASES = new Map([
  ["preference", "preference"],
  ["preferences", "preference"],
  ["persona", "persona"],
  ["system", "system_state"],
  ["system_state", "system_state"]
]);

const SHAPES_BY_CATEGORY = {
  preference: "leaf",
  persona: "pearl",
  system_state: "mineral",
};

export const clamp01 = value => Math.max(0, Math.min(1, Number(value) || 0));

function textValue(value) {
  return value == null ? "" : String(value);
}

function nonNegativeNumber(value) {
  return Math.max(0, Number(value) || 0);
}

function asRecord(value) {
  return value && typeof value === "object" ? value : {};
}

export function normalizeCategory(value) {
  const alias = textValue(value).trim().toLowerCase();
  return CATEGORY_ALIASES.get(alias) ?? "system_state";
}

export function deriveLifecycle(memory = {}) {
  const record = asRecord(memory);
  const nodeWeight = clamp01(record.nodeWeight ?? record.node_weight);
  const injectionCount = nonNegativeNumber(record.injectionCount ?? record.injection_count);

  if (nodeWeight >= 0.85 && injectionCount >= 3) {
    return "vivid";
  }
  if (nodeWeight >= 0.6 && injectionCount >= 3) {
    return "rooted";
  }
  if (nodeWeight >= 0.6 && injectionCount === 0) {
    return "new";
  }
  if (nodeWeight >= 0.6) {
    return "stable";
  }
  if (nodeWeight >= 0.3) {
    return "fading";
  }
  return "dormant";
}

export function normalizeMemory(raw = {}) {
  const record = asRecord(raw);
  const category = normalizeCategory(record.category);
  const confidence = clamp01(record.conviction_score ?? record.node_weight);
  const vitality = clamp01(record.node_weight);
  const injectionCount = nonNegativeNumber(record.injection_count);

  return {
    id: textValue(record.id),
    category,
    shape: SHAPES_BY_CATEGORY[category],
    source: textValue(record.entity_source ?? record.source),
    relation: textValue(record.relation),
    target: textValue(record.entity_target ?? record.target),
    confidence,
    vitality,
    injectionCount,
    lifecycle: deriveLifecycle({ nodeWeight: vitality, injectionCount }),
  };
}

export function normalizeRelationship(raw = {}, validIds = new Set()) {
  const record = asRecord(raw);
  const source = textValue(record.source);
  const target = textValue(record.target);

  if (!source || !target || !validIds?.has?.(source) || !validIds.has(target)) {
    return null;
  }

  return {
    source,
    target,
    kind: textValue(record.kind) || "related",
    weight: clamp01(record.weight),
  };
}

export function normalizeGraph(raw = {}) {
  const payload = asRecord(raw);
  const memories = (Array.isArray(payload.beliefs) ? payload.beliefs : []).map(normalizeMemory);
  const validIds = new Set(memories.map(memory => memory.id).filter(Boolean));
  const relationships = (Array.isArray(payload.edges) ? payload.edges : [])
    .map(edge => normalizeRelationship(edge, validIds))
    .filter(Boolean);

  return {
    memories,
    relationships,
    totalTurns: nonNegativeNumber(payload.total_turns ?? payload.totalTurns),
  };
}

export function statementFor(memory = {}) {
  const record = asRecord(memory);
  const source = textValue(record.source ?? record.entity_source) || "Unknown source";
  const relation = textValue(record.relation) || "relates to";
  const target = textValue(record.target ?? record.entity_target) || "unknown target";

  return `${source} ${relation} ${target}.`;
}
