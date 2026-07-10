import assert from "node:assert/strict";
import test from "node:test";

import {
  clamp01,
  deriveLifecycle,
  normalizeCategory,
  normalizeGraph,
  normalizeMemory,
  normalizeRelationship,
  statementFor,
} from "../src/public/scripts/memory-model.js";
import { EMPTY_FIXTURE, GRAPH_FIXTURE } from "./fixtures/archive-fixture.mjs";

test("normalizes the documented category aliases without inventing a category", () => {
  assert.equal(normalizeCategory("preference"), "preference");
  assert.equal(normalizeCategory("preferences"), "preference");
  assert.equal(normalizeCategory("persona"), "persona");
  assert.equal(normalizeCategory("system"), "system_state");
  assert.equal(normalizeCategory("system_state"), "system_state");
  assert.equal(normalizeCategory("unknown"), "system_state");
});

test("clamps visual scores to the unit interval", () => {
  assert.equal(clamp01(-0.25), 0);
  assert.equal(clamp01(1.25), 1);
  assert.equal(clamp01("0.75"), 0.75);
  assert.equal(clamp01("not-a-score"), 0);
});

test("normalizes raw beliefs into shaped visual memories", () => {
  const preference = normalizeMemory(GRAPH_FIXTURE.beliefs[0]);
  const persona = normalizeMemory({ ...GRAPH_FIXTURE.beliefs[0], category: "persona" });
  const systemState = normalizeMemory({ ...GRAPH_FIXTURE.beliefs[0], category: "system" });

  assert.equal(preference.id, "1");
  assert.equal(preference.category, "preference");
  assert.equal(preference.shape, "leaf");
  assert.equal(preference.source, "interface");
  assert.equal(preference.relation, "prefers");
  assert.equal(preference.target, "quiet motion");
  assert.equal(preference.confidence, 0.96);
  assert.equal(preference.vitality, 0.94);
  assert.equal(preference.injectionCount, 7);
  assert.equal(preference.statement, "interface prefers quiet motion.");
  assert.equal(preference.influenceCount, 4);
  assert.equal(persona.shape, "pearl");
  assert.equal(systemState.shape, "mineral");
});

test("uses conviction when available, otherwise node weight, without failing on optional fields", () => {
  const convictionZero = normalizeMemory({
    id: 42,
    category: "unsupported",
    node_weight: 0.8,
    conviction_score: 0,
    injection_count: -2,
  });
  const fallback = normalizeMemory({ id: "fallback", node_weight: 1.5 });

  assert.equal(convictionZero.id, "42");
  assert.equal(convictionZero.category, "system_state");
  assert.equal(convictionZero.confidence, 0);
  assert.equal(convictionZero.vitality, 0.8);
  assert.equal(convictionZero.injectionCount, 0);
  assert.equal(fallback.confidence, 1);
  assert.equal(fallback.vitality, 1);
  assert.doesNotThrow(() => normalizeMemory());
});

test("derives lifecycle states from vitality and recall thresholds", () => {
  assert.equal(deriveLifecycle({ nodeWeight: 0.9, injectionCount: 4 }), "vivid");
  assert.equal(deriveLifecycle({ nodeWeight: 0.7, injectionCount: 3 }), "rooted");
  assert.equal(deriveLifecycle({ nodeWeight: 0.7, injectionCount: 1 }), "stable");
  assert.equal(deriveLifecycle({ nodeWeight: 0.7, injectionCount: 0 }), "new");
  assert.equal(deriveLifecycle({ nodeWeight: 0.45, injectionCount: 0 }), "fading");
  assert.equal(deriveLifecycle({ nodeWeight: 0.2, injectionCount: 0 }), "dormant");
});

test("builds readable memory statements", () => {
  assert.equal(
    statementFor(normalizeMemory(GRAPH_FIXTURE.beliefs[0])),
    "interface prefers quiet motion."
  );
});

test("keeps only relationships between known memory IDs", () => {
  const validIds = new Set(["1", "2"]);

  assert.deepEqual(normalizeRelationship(GRAPH_FIXTURE.edges[0], validIds), {
    source: "1",
    target: "2",
    kind: "cluster",
    weight: 0.65,
  });
  assert.equal(normalizeRelationship({ source: 1, target: 999, weight: 0.4 }, validIds), null);
  assert.equal(normalizeRelationship({ source: 1, weight: 0.4 }, validIds), null);
});

test("normalizes graph payloads and safely ignores non-array collections", () => {
  const graph = normalizeGraph(GRAPH_FIXTURE);

  assert.equal(graph.memories.length, 6);
  assert.equal(graph.relationships.length, 5);
  assert.equal(graph.totalTurns, 12);
  assert.deepEqual(normalizeGraph(EMPTY_FIXTURE), {
    memories: [],
    relationships: [],
    totalTurns: 0,
  });
  assert.deepEqual(normalizeGraph({ beliefs: {}, edges: "invalid", total_turns: "nope" }), {
    memories: [],
    relationships: [],
    totalTurns: 0,
  });
});
