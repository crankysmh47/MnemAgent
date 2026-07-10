import test from 'node:test';
import assert from 'node:assert/strict';
import { nextEscapeState, filterMemory } from '../src/public/scripts/interactions/memory-focus.js';

test('Escape unwinds trace before focus before menu', () => {
  assert.deepEqual(nextEscapeState({ tracedMemoryId: 'a', selectedMemoryId: 'a', menuOpen: true }), { tracedMemoryId: null, selectedMemoryId: 'a', menuOpen: true });
  assert.deepEqual(nextEscapeState({ tracedMemoryId: null, selectedMemoryId: 'a', menuOpen: true }), { tracedMemoryId: null, selectedMemoryId: null, menuOpen: true });
  assert.deepEqual(nextEscapeState({ tracedMemoryId: null, selectedMemoryId: null, menuOpen: true }), { tracedMemoryId: null, selectedMemoryId: null, menuOpen: false });
});

test('filters quiet excluded memories without deleting them', () => {
  assert.equal(filterMemory({ category: 'preference', lifecycle: 'vivid' }, { categories: ['preference'], lifecycles: ['vivid'] }), true);
  assert.equal(filterMemory({ category: 'persona', lifecycle: 'vivid' }, { categories: ['preference'], lifecycles: ['vivid'] }), false);
});
