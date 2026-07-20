import assert from 'node:assert/strict';
import { test } from 'node:test';
import chatModule from '../src/judge-chat-service.js';

const { createJudgeChatService } = chatModule;

test('chat creates a fresh OpenClaw session while retaining the private memory namespace', async () => {
  const calls = [];
  const service = createJudgeChatService({ executor: async input => { calls.push(input); return { text: 'I will remember that.', usageUsd: 0.002 }; } });
  const first = service.create({ ownerSessionId: 'jss_owner', namespace: 'judge-private', message: 'For MnemBench, keep every dimension oriented so 1.0 means best.' });
  const second = service.create({ ownerSessionId: 'jss_owner', namespace: 'judge-private', message: 'What style do I prefer?' });
  await Promise.all([service.wait(first.id), service.wait(second.id)]);
  assert.notEqual(calls[0].sessionId, calls[1].sessionId);
  assert.equal(calls[0].namespace, 'judge-private');
  assert.equal(calls[0].agentId, 'judge-chat');
  assert.match(calls[0].message, /scope_type[^\n]*repository/i);
  assert.match(calls[0].message, /crankysmh47\/MnemBench/);
  assert.match(calls[0].message, /explicitly asks you to remember[\s\S]*must call memory_store before replying/i);
  assert.match(calls[0].message, /judge-private/);
  assert.equal(service.get(first.id, 'jss_owner').status, 'completed');
  assert.throws(() => service.get(first.id, 'jss_other'), /not found/i);
});

test('chat rejects empty and oversized messages', () => {
  const service = createJudgeChatService({ executor: async () => ({ text: 'ok' }) });
  assert.throws(() => service.create({ ownerSessionId: 'jss_owner', namespace: 'judge-private', message: '' }), /bounded/i);
  assert.throws(() => service.create({ ownerSessionId: 'jss_owner', namespace: 'judge-private', message: 'x'.repeat(2_001) }), /bounded/i);
});
