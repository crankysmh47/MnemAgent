import test from 'node:test';
import assert from 'node:assert/strict';
import { relatedMemoryIds, selectRenderableRelationships, structuralKey, statusFromSnapshot, shouldSeedDemo } from '../src/public/scripts/main.js';

test('structural key ignores metric-only changes and is order-independent', () => {
  const a = { memories: [{ id: 'b' }, { id: 'a' }], relationships: [{ source: 'b', target: 'a' }] };
  const b = { memories: [{ id: 'a' }, { id: 'b' }], relationships: [{ source: 'b', target: 'a' }], metrics: { total: 99 } };
  assert.equal(structuralKey(a), structuralKey(b));
});

test('snapshot status distinguishes usable, degraded, empty, and fatal states', () => {
  assert.equal(statusFromSnapshot({ graph: { beliefs: [{ id: 1 }] }, failures: {} }), 'ready');
  assert.equal(statusFromSnapshot({ graph: { beliefs: [{ id: 1 }] }, failures: { metrics: 'offline' } }), 'degraded');
  assert.equal(statusFromSnapshot({ graph: { beliefs: [] }, failures: {} }), 'empty');
  assert.equal(statusFromSnapshot({ graph: null, failures: { graph: 'offline' } }), 'error');
});

test('only the explicit demo user may request demo seeding', () => {
  assert.equal(shouldSeedDemo('demo-brain', { beliefs: 2 }), true);
  assert.equal(shouldSeedDemo('demo-brain', { beliefs: 8 }), false);
  assert.equal(shouldSeedDemo('real-user', { beliefs: 0 }), false);
});

test('dense archives limit ambient tendrils while focus keeps every incident relationship', () => {
  const relationships = Array.from({ length: 200 }, (_, index) => ({
    source: String(index % 20),
    target: String((index + 1) % 20),
    kind: index % 3 === 0 ? 'cluster' : 'affinity',
    weight: 1 - index / 400,
  }));
  assert.equal(selectRenderableRelationships(relationships, null, 80).length, 80);
  const focused = selectRenderableRelationships(relationships, '3', 80);
  assert.ok(focused.every(edge => edge.source === '3' || edge.target === '3' || focused.indexOf(edge) < 80));
  assert.ok(focused.filter(edge => edge.source === '3' || edge.target === '3').length > 0);
  assert.deepEqual([...relatedMemoryIds('3', relationships)].sort(), ['2', '4']);
});
