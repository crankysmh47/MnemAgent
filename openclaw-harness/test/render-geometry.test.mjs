import test from 'node:test';
import assert from 'node:assert/strict';
import { memoryFormPath, memoryAriaLabel, memoryVeinPath } from '../src/public/scripts/render/memory-form.js';
import * as tendril from '../src/public/scripts/render/tendril.js';

const { tendrilClass } = tendril;

test('memory form paths are closed for living forms and finite', () => {
  for (const shape of ['leaf', 'pearl', 'mineral']) {
    const path = memoryFormPath(shape, 14);
    assert.match(path, /^M/);
    assert.match(path, /Z$/);
    assert.ok([...path.matchAll(/-?\d+(?:\.\d+)?/g)].every(m => Number.isFinite(Number(m[0]))));
  }
});

test('husk geometry remains open and memory labels expose lifecycle details', () => {
  assert.doesNotMatch(memoryFormPath('husk', 12), /Z$/);
  const label = memoryAriaLabel({ statement: 'interface prefers quiet motion', category: 'preference', lifecycle: 'vivid', confidence: 0.94, injectionCount: 3 });
  assert.match(label, /interface prefers quiet motion/);
  assert.match(label, /preference/);
  assert.match(label, /vivid/);
  assert.match(label, /94%/);
  assert.match(label, /3 recalls/);
});

test('tendril classes encode relationship kind and quiet state', () => {
  assert.equal(tendrilClass({ kind: 'cluster' }, 'active'), 'tendril tendril-cluster is-active');
  assert.equal(tendrilClass({ kind: 'bridge' }, 'quiet'), 'tendril tendril-bridge is-quiet');
});

test('only relationships incident to the focused memory become active', () => {
  assert.equal(typeof tendril.relationshipFocusState, 'function');
  assert.equal(tendril.relationshipFocusState({ source: 'a', target: 'b' }, 'a'), 'active');
  assert.equal(tendril.relationshipFocusState({ source: 'a', target: 'b' }, 'b'), 'active');
  assert.equal(tendril.relationshipFocusState({ source: 'b', target: 'c' }, 'a'), 'quiet');
  assert.equal(tendril.relationshipFocusState({ source: 'b', target: 'c' }, null), 'quiet');
});

test('botanical memory forms expose internal organic markings', () => {
  for (const shape of ['leaf', 'pearl', 'mineral']) {
    const path = memoryVeinPath(shape, 14);
    assert.match(path, /^M/);
    assert.ok([...path.matchAll(/-?\d+(?:\.\d+)?/g)].every(match => Number.isFinite(Number(match[0]))));
  }
});
