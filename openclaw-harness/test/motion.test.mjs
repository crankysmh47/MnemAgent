import test from 'node:test';
import assert from 'node:assert/strict';
import { transitionForPhase } from '../src/public/scripts/motion/lifecycle-transitions.js';
import { selectMotionEvent } from '../src/public/scripts/motion/choreographer.js';

test('lifecycle transition specs reveal the forest from ground to canopy', () => {
  assert.deepEqual(transitionForPhase('arrival', false), { className: 'phase-arrival', duration: 1200 });
  assert.equal(transitionForPhase('opening-ground', false).duration, 420);
  assert.equal(transitionForPhase('opening-roots', false).duration, 360);
  assert.equal(transitionForPhase('opening-trunk', false).duration, 420);
  assert.equal(transitionForPhase('opening-branches', false).duration, 520);
  assert.equal(transitionForPhase('opening-bloom', false).duration, 1200);
  assert.equal(transitionForPhase('opening-connections', false).duration, 360);
  assert.equal(transitionForPhase('opening-settle', false).duration, 480);
  for (const phase of ['opening-ground', 'opening-roots', 'opening-trunk', 'opening-branches', 'opening-bloom', 'opening-connections', 'opening-settle', 'recall']) {
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
