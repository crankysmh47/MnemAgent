import test from 'node:test';
import assert from 'node:assert/strict';
import { createLoadingGate } from '../src/public/scripts/motion/loading-gate.js';

test('loading gate waits for readiness and one complete 1400ms spinner turn', async () => {
  let time = 0; const waits = [];
  const gate = createLoadingGate({ minimumMs: 1400, now: () => time, wait: async ms => { waits.push(ms); time += ms; } });
  let released = false; const release = gate.release().then(() => { released = true; });
  await Promise.resolve(); assert.equal(released, false); time = 400; gate.ready(); await release;
  assert.deepEqual(waits, [1000]); assert.equal(time, 1400);
});

test('loading gate releases non-ready archive states through the readiness signal', async () => {
  const gate = createLoadingGate({ minimumMs: 0, wait: async () => {} }); gate.ready(); await gate.release(); assert.equal(gate.isReleased(), true);
});
