import test from 'node:test';
import assert from 'node:assert/strict';
import { computeArchiveLayout, relationshipPath } from '../src/public/scripts/layout.js';

const memories = Array.from({ length: 6 }, (_, i) => ({ id: `m${i}`, category: ['preference','persona','system_state'][i % 3], vitality: 0.4 + i / 10, confidence: 0.5 }));
const relationships = [{ source: 'm0', target: 'm1' }, { source: 'm2', target: 'm3' }];
test('layout is deterministic, bounded, grouped, and has finite paths', () => {
  const a = computeArchiveLayout(memories, relationships, { width: 1200, height: 800 });
  const b = computeArchiveLayout([...memories].reverse(), [...relationships].reverse(), { width: 1200, height: 800 });
  assert.deepEqual(a, b);
  for (const n of a.nodes) { assert.ok(n.x >= 72 && n.x <= 1128); assert.ok(n.y >= 64 && n.y <= 736); }
  assert.ok(new Set(a.nodes.map(n => n.grove)).size >= 3);
  for (const p of a.paths) { assert.equal(p.d[0], 'M'); assert.match(p.d, /^M[-+\d.e, ]+ C[-+\d.e, ]+$/); }
});
test('large archives collapse low-priority distant groups', () => {
  const many = Array.from({ length: 100 }, (_, i) => ({ id: `m${i}`, category: i % 2 ? 'persona' : 'preference', vitality: i === 0 ? 1 : 0.2 }));
  const layout = computeArchiveLayout(many, [], { width: 1000, height: 720 });
  assert.ok(layout.groves.some(g => g.collapsed));
  assert.ok(layout.nodes.some(n => n.id === 'm0' && !n.collapsed));
});
test('relationshipPath returns cubic path', () => assert.match(relationshipPath({x:0,y:0},{x:10,y:5}), /^M0,0 C/));
