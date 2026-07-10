import test from 'node:test';
import assert from 'node:assert/strict';
import { structuralKey, statusFromSnapshot, shouldSeedDemo } from '../src/public/scripts/main.js';

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
