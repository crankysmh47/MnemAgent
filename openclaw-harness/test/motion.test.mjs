import test from 'node:test';
import assert from 'node:assert/strict';
import { transitionForPhase } from '../src/public/scripts/motion/lifecycle-transitions.js';
import { selectMotionEvent } from '../src/public/scripts/motion/choreographer.js';

test('lifecycle transition specs use a brief four-part forest awakening', () => {
  assert.deepEqual(transitionForPhase('arrival', false), { className: 'phase-arrival', duration: 1200 });
  assert.equal(transitionForPhase('opening-ground', false).duration, 500);
  assert.equal(transitionForPhase('opening-tree', false).duration, 700);
  assert.equal(transitionForPhase('opening-bloom', false).duration, 1200);
  assert.equal(transitionForPhase('opening-settle', false).duration, 500);
  for (const phase of ['opening-ground', 'opening-tree', 'opening-bloom', 'opening-settle', 'recall']) {
    assert.ok(transitionForPhase(phase, true).duration <= 180);
  }
});

test('motion event selection prioritizes one meaningful event and caps pulses', () => {
  const decision = selectMotionEvent([
    { id: 1, eventType: 'decayed' },
    { id: 2, eventType: 'contradiction' },
    { id: 3, eventType: 'injected' },
  ], new Set());
  assert.equal(decision.featured.id, 2);
  assert.equal(decision.pulseLimit, 3);
});
