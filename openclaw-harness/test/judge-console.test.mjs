import assert from 'node:assert/strict';
import { test } from 'node:test';
import { reduceJudgeState } from '../src/public/scripts/judge-console.js';

test('judge console preserves ordered activity and completion evidence', () => {
  let state = { status: 'idle', events: [] };
  state = reduceJudgeState(state, { type: 'run.started', sequence: 1, detail: {} });
  state = reduceJudgeState(state, { type: 'assistant.message', sequence: 2, detail: { text: 'Patch ready' } });
  state = reduceJudgeState(state, { type: 'run.completed', sequence: 3, detail: { usageUsd: 0.01 } });
  assert.equal(state.status, 'completed');
  assert.deepEqual(state.events.map(event => event.sequence), [1, 2, 3]);
  assert.equal(state.message, 'Patch ready');
});

test('duplicate replay events do not duplicate activity', () => {
  const event = { id: 'evt-1', type: 'run.started', sequence: 1, detail: {} };
  const state = reduceJudgeState(reduceJudgeState({ status: 'idle', events: [] }, event), event);
  assert.equal(state.events.length, 1);
});

test('judge state keeps quota and separates real evidence for memory and changes tabs', () => {
  const state = reduceJudgeState({ status: 'running', events: [], quota: null, evidence: null }, {
    id: 'evt-1', type: 'test.completed', sequence: 1, detail: { commandId: 'test-unit', exitCode: 0 },
  }, {
    quota: { chatTurnsRemaining: 2, codingRunsRemaining: 0, publicationsRemaining: 1, reservedUsdRemaining: 0.04 },
    evidence: { memories: [{ value: 'Use user-safe errors.' }], tests: [{ commandId: 'test-unit', passed: true }], diff: 'patch', readyForApproval: true },
  });
  assert.equal(state.quota.chatTurnsRemaining, 2);
  assert.equal(state.evidence.memories[0].value, 'Use user-safe errors.');
  assert.equal(state.evidence.readyForApproval, true);
});
