import assert from 'node:assert/strict';
import { test } from 'node:test';
import sessionModule from '../src/judge-session-store.js';

const { createJudgeSessionStore } = sessionModule;

test('sponsored session enforces chat, coding, publication, and allowance quotas', () => {
  const store = createJudgeSessionStore({ now: () => 1_000, ttlMs: 3_600_000 });
  const session = store.create({ sessionId: 'jss_owner', namespace: 'judge-private' });
  assert.deepEqual(session.quota, { chatTurnsRemaining: 3, codingRunsRemaining: 1, publicationsRemaining: 1, reservedUsdRemaining: 0.1 });
  for (let i = 0; i < 3; i += 1) store.reserve('jss_owner', 'chat');
  assert.throws(() => store.reserve('jss_owner', 'chat'), /allowance/i);
  store.reserve('jss_owner', 'coding');
  assert.throws(() => store.reserve('jss_owner', 'coding'), /allowance/i);
  store.consumePublication('jss_owner');
  assert.throws(() => store.consumePublication('jss_owner'), /allowance/i);
  assert.deepEqual(store.get('jss_owner').quota, { chatTurnsRemaining: 0, codingRunsRemaining: 0, publicationsRemaining: 0, reservedUsdRemaining: 0.02 });
});

test('sponsored sessions expire and release restores only an in-flight reservation', () => {
  let now = 1_000;
  const store = createJudgeSessionStore({ now: () => now, ttlMs: 100 });
  store.create({ sessionId: 'jss_owner', namespace: 'judge-private' });
  store.reserve('jss_owner', 'chat');
  store.release('jss_owner', 'chat');
  assert.equal(store.get('jss_owner').quota.chatTurnsRemaining, 3);
  now = 1_101;
  assert.throws(() => store.get('jss_owner'), /expired/i);
});

test('sponsored admission has a global session cap', () => {
  const store = createJudgeSessionStore({ maxSessions: 2 });
  store.create({ sessionId: 'jss_one', namespace: 'judge-one' });
  store.create({ sessionId: 'jss_two', namespace: 'judge-two' });
  assert.throws(() => store.create({ sessionId: 'jss_three', namespace: 'judge-three' }), /capacity/i);
});
