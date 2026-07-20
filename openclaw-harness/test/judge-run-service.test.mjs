import assert from 'node:assert/strict';
import { test } from 'node:test';
import serviceModule from '../src/judge-run-service.js';

const { createJudgeRunService, parseOpenClawResponse } = serviceModule;

test('OpenClaw response parser reads current payload and token usage shape', () => {
  const parsed = parseOpenClawResponse({ payloads: [{ text: 'Remembered.' }], meta: { agentMeta: { usage: { input: 3338, output: 12, total: 3350 } } } });
  assert.equal(parsed.text, 'Remembered.');
  assert.deepEqual(parsed.usageTokens, { input: 3338, output: 12, total: 3350 });
});

test('run service returns immediately, binds ownership, and completes asynchronously', async () => {
  const calls = [];
  let finish;
  const service = createJudgeRunService({
    model: 'deepseek-api/deepseek-v4-flash',
    executor: input => { calls.push(input); return new Promise(resolve => { finish = resolve; }); },
  });
  const run = service.create({ ownerSessionId: 'jss_owner', namespace: 'judge-private', sessionId: 'fresh-session', issueNumber: 1, message: 'Inspect and solve.' });
  assert.equal(run.status, 'running');
  assert.equal(service.get(run.id, 'jss_owner').namespace, 'judge-private');
  assert.equal(calls[0].model, 'deepseek-api/deepseek-v4-flash');
  finish({ text: 'Issue selected: add path normalization tests', usageUsd: 0.01 });
  await service.wait(run.id);
  assert.deepEqual(service.events(run.id, 'jss_owner').map(event => event.type), ['run.started', 'model.started', 'assistant.message', 'run.completed']);
  assert.equal(service.get(run.id, 'jss_owner').status, 'completed');
  assert.throws(() => service.get(run.id, 'jss_other'), /not found/i);
});

test('hard model token budget switches new runs to replay mode', async () => {
  const service = createJudgeRunService({ model: 'deepseek-v4-flash', hardBudgetTokens: 100, executor: async () => ({ text: 'ok', usageTokens: { input: 90, output: 10, total: 100 } }) });
  const first = service.create({ ownerSessionId: 'jss_one', namespace: 'judge-one', sessionId: 'one', issueNumber: 1, message: 'first' });
  await service.wait(first.id);
  const second = service.create({ ownerSessionId: 'jss_two', namespace: 'judge-two', sessionId: 'two', issueNumber: 1, message: 'second' });
  await service.wait(second.id);
  assert.equal(second.mode, 'replay');
  assert.equal(service.get(second.id, 'jss_two').status, 'completed');
});

test('coding runs accept only prepared MnemBench issue 1 and bounded directions', () => {
  const service = createJudgeRunService({ executor: async () => ({ text: 'ok', usageUsd: 0 }) });
  assert.throws(() => service.create({ ownerSessionId: 'jss_owner', namespace: 'judge-private', sessionId: 'fresh', issueNumber: 10, message: 'work' }), /prepared issue/i);
  assert.throws(() => service.create({ ownerSessionId: 'jss_owner', namespace: 'judge-private', sessionId: 'fresh', issueNumber: 1, message: 'x'.repeat(4_001) }), /bounded/i);
});
