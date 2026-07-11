import test from 'node:test';
import assert from 'node:assert/strict';
import { memoryLabelPosition, shortMemoryStatement } from '../src/public/scripts/render/memory-label.js';

test('short memory labels contain only a bounded statement', () => {
  assert.equal(shortMemoryStatement({ statement: 'Likes quiet interfaces', confidence: .9 }), 'Likes quiet interfaces');
  const shortened = shortMemoryStatement({ statement: 'one two three four five six seven' }, 18);
  assert.ok(shortened.length <= 18 && shortened.endsWith('…'));
  assert.equal(shortMemoryStatement({}), 'Memory details unavailable');
});

test('memory label positions flip and clamp inside stage bounds', () => {
  assert.deepEqual(memoryLabelPosition({ x: 8, y: 20, radius: 10 }, { width: 300, height: 200 }, { width: 120, height: 38 }), { x: 8, y: 40, anchor: 'start' });
  const right = memoryLabelPosition({ x: 292, y: 180, radius: 10 }, { width: 300, height: 200 }, { width: 120, height: 38 });
  assert.equal(right.anchor, 'end'); assert.ok(right.y <= 180);
});
