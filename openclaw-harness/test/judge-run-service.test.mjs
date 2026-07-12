import assert from 'node:assert/strict';
import { test } from 'node:test';
import serviceModule from '../src/judge-run-service.js';

const { createJudgeRunService } = serviceModule;

test('run service emits observable ordered activity and uses the configured model', async () => {
  const calls = [];
  const service = createJudgeRunService({
    model: 'deepseek-api/deepseek-v4-flash',
    executor: async input => { calls.push(input); return { text: 'Issue selected: add path normalization tests', usageUsd: 0.01 }; },
  });
  const run = await service.create({ sessionId: 'fresh-session', issueNumber: 1, message: 'Inspect and choose.' });
  assert.equal(calls[0].model, 'deepseek-api/deepseek-v4-flash');
  assert.deepEqual(service.events(run.id).map(event => event.type), ['run.started', 'model.started', 'assistant.message', 'run.completed']);
  assert.equal(service.get(run.id).status, 'completed');
});

test('hard model budget switches new runs to replay mode', async () => {
  const service = createJudgeRunService({ model: 'deepseek-v4-flash', hardBudgetUsd: 0.02, executor: async () => ({ text: 'ok', usageUsd: 0.02 }) });
  await service.create({ sessionId: 'one', issueNumber: 1, message: 'first' });
  const second = await service.create({ sessionId: 'two', issueNumber: 1, message: 'second' });
  assert.equal(second.mode, 'replay');
  assert.equal(service.get(second.id).status, 'completed');
});
