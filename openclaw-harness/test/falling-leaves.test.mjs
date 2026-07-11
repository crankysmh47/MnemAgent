import test from 'node:test';
import assert from 'node:assert/strict';
import { createFallingLeaves } from '../src/public/scripts/motion/falling-leaves.js';

test('falling leaves schedule sparsely and stop cleanly', () => {
  const callbacks = [];
  const controller = createFallingLeaves({ random: () => 0, schedule: (fn, ms) => { callbacks.push({ fn, ms }); return callbacks.length; }, cancel: () => {} });
  controller.start(); assert.equal(callbacks[0].ms, 7000); controller.stop(); assert.equal(controller.isRunning(), false);
});

test('reduced motion never schedules falling leaves', () => {
  let scheduled = false; createFallingLeaves({ reducedMotion: true, schedule: () => { scheduled = true; } }).start(); assert.equal(scheduled, false);
});
