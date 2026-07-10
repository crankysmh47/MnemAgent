import test from 'node:test';
import assert from 'node:assert/strict';
import { deriveVitalSigns, eventGlyph } from '../src/public/scripts/render/annotations.js';

test('vital signs count visible memories, relationships, and recent recall events', () => {
  const signs = deriveVitalSigns({
    memories: [{ id: 'a', visible: true }, { id: 'b', visible: false }, { id: 'c' }],
    relationships: [{ id: 'x' }, { id: 'y' }],
    events: [{ id: 1, eventType: 'injected' }, { id: 2, eventType: 'influenced' }, { id: 2, eventType: 'influenced' }],
  });
  assert.deepEqual(signs, { memories: 2, relationships: 2, recalls: 2 });
});

test('lifecycle events use material glyphs', () => {
  assert.equal(eventGlyph({ eventType: 'new_belief' }), 'seed');
  assert.equal(eventGlyph({ eventType: 'injected' }), 'pulse');
  assert.equal(eventGlyph({ eventType: 'contradiction' }), 'scar');
  assert.equal(eventGlyph({ eventType: 'pruned' }), 'husk');
  assert.equal(eventGlyph({ eventType: 'unknown' }), 'settled');
});
