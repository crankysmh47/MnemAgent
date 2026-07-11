import test from 'node:test';
import assert from 'node:assert/strict';
import { computeArchiveLayout, relationshipPath } from '../src/public/scripts/layout.js';
import { createTreeSkeleton, cubicPoint, curvePath } from '../src/public/scripts/tree-geometry.js';

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
test('selected and high-vitality memories remain individual and groves aggregate', () => {
  const many = Array.from({ length: 100 }, (_, i) => ({ id: `m${i}`, category: 'persona', vitality: i === 0 ? 1 : 0.1 }));
  const layout = computeArchiveLayout(many, [], { width: 1000, height: 720, selectedMemoryId: 'm99' });
  assert.equal(layout.nodes.find(n => n.id === 'm0').collapsed, false);
  assert.equal(layout.nodes.find(n => n.id === 'm99').collapsed, false);
  const grove = layout.groves.find(g => g.category === 'persona');
  assert.ok(grove.aggregate?.memberIds.length);
  assert.equal(grove.aggregate.count, grove.aggregate.memberIds.length);
  assert.equal(grove.aggregate.representative, grove.aggregate.memberIds[0]);
  assert.ok(grove.members.includes('m0'));
  assert.ok(grove.members.includes('m99'));
});
test('missing IDs derive permutation-stable identities', () => {
  const m = [{ category:'preference', source:'a', relation:'likes', target:'b' }, { category:'persona', source:'c', relation:'is', target:'d' }];
  assert.deepEqual(computeArchiveLayout(m, [], {}).nodes, computeArchiveLayout([...m].reverse(), [], {}).nodes);
});
test('relationshipPath returns cubic path', () => assert.match(relationshipPath({x:0,y:0},{x:10,y:5}), /^M0,0 C/));

test('layout paths preserve relationship styling metadata', () => {
  const layout = computeArchiveLayout(
    [{ id: 'a', category: 'preference', vitality: 0.9 }, { id: 'b', category: 'persona', vitality: 0.8 }],
    [{ id: 'edge-1', source: 'a', target: 'b', kind: 'bridge', weight: 0.7 }],
  );
  assert.deepEqual(layout.paths[0], { ...layout.paths[0], kind: 'bridge', weight: 0.7 });
});

test('crowded layouts keep every memory form fully inside the archive stage', () => {
  const crowded = Array.from({ length: 62 }, (_, i) => ({ id: `dense-${i}`, category: ['preference','persona','system_state'][i % 3], vitality: 0.45 + (i % 6) / 12 }));
  const layout = computeArchiveLayout(crowded, [], { width: 943, height: 620 });
  for (const node of layout.nodes) {
    assert.ok(node.x - node.radius >= layout.bounds.marginX, `${node.id} escaped left`);
    assert.ok(node.x + node.radius <= layout.bounds.width - layout.bounds.marginX, `${node.id} escaped right`);
    assert.ok(node.y - node.radius >= layout.bounds.marginY, `${node.id} escaped top`);
    assert.ok(node.y + node.radius <= layout.bounds.height - layout.bounds.marginY, `${node.id} escaped bottom`);
  }
});

test('tree skeleton is rooted and branches upward into three category families', () => {
  const tree = createTreeSkeleton({ width: 1000, height: 720 });
  assert.ok(tree.root.x >= 540 && tree.root.x <= 560);
  assert.ok(tree.root.y > tree.crown.y);
  assert.deepEqual([...new Set(tree.branches.map(branch => branch.category))].sort(), ['persona','preference','system_state']);
  assert.ok(tree.branches.every(branch => branch.end.y < tree.root.y));
  assert.ok(tree.branches.every(branch => /^M[-+\d.e, ]+ C[-+\d.e, ]+$/.test(curvePath(branch))));
});

test('cubic interpolation keeps branch endpoints exact', () => {
  const curve = { start:{x:0,y:10}, control1:{x:3,y:5}, control2:{x:7,y:2}, end:{x:10,y:0} };
  assert.deepEqual(cubicPoint(curve, 0), curve.start);
  assert.deepEqual(cubicPoint(curve, 1), curve.end);
});

test('memories grow along category branches instead of a radial cluster', () => {
  const layout = computeArchiveLayout(Array.from({length:62}, (_,i) => ({
    id:`tree-${i}`, category:['preference','persona','system_state'][i%3], vitality:.5 + (i%5)/10,
  })), [], {width:1000,height:720});
  assert.ok(layout.tree.root.y > layout.tree.crown.y);
  assert.ok(layout.nodes.every(node => node.branchId && Number.isFinite(node.branchT)));
  assert.ok(layout.nodes.every(node => node.y < layout.tree.root.y));
  assert.ok(Math.max(...layout.nodes.map(node => node.y)) - Math.min(...layout.nodes.map(node => node.y)) > 260);
});

test('a dominant category spreads across overlapping canopy limbs', () => {
  const memories = Array.from({length:48}, (_,i) => ({ id:`system-${i}`, category:'system_state', vitality:.7 }));
  const layout = computeArchiveLayout(memories, [], {width:1000,height:720});
  const xs = layout.nodes.map(node => node.x);
  assert.ok(Math.max(...xs) - Math.min(...xs) > 460);
});
