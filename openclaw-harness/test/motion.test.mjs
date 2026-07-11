import test from 'node:test';
import assert from 'node:assert/strict';
import { transitionForPhase } from '../src/public/scripts/motion/lifecycle-transitions.js';
import { selectMotionEvent } from '../src/public/scripts/motion/choreographer.js';

test('lifecycle transition specs use the approved opening and reduced-motion timings', () => {
  assert.deepEqual(transitionForPhase('arrival', false), { className: 'phase-arrival', duration: 1200 });
  assert.equal(transitionForPhase('opening-skeleton', false).duration, 2000);
  assert.equal(transitionForPhase('opening-branches', false).duration, 3000);
  assert.equal(transitionForPhase('opening-root', false).duration, 3000);
  assert.equal(transitionForPhase('opening-annotations', false).duration, 2000);
  assert.ok(transitionForPhase('recall', true).duration <= 180);
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
