import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { test } from 'node:test';
import sessionModule from '../src/judge-session-store.js';

const { createJudgeSessionStore } = sessionModule;

test('sponsored session enforces chat, coding, publication, and allowance quotas', () => {
  const store = createJudgeSessionStore({ now: () => 1_000, ttlMs: 3_600_000 });
  const session = store.create({ sessionId: 'jss_owner', namespace: 'judge-private' });
  assert.deepEqual(session.quota, { chatTurnsRemaining: 30, codingRunsRemaining: 5, publicationsRemaining: 5, reservedUsdRemaining: 0.55 });
  for (let i = 0; i < 30; i += 1) store.reserve('jss_owner', 'chat');
  assert.throws(() => store.reserve('jss_owner', 'chat'), /allowance/i);
  for (let i = 0; i < 5; i += 1) store.reserve('jss_owner', 'coding');
  assert.throws(() => store.reserve('jss_owner', 'coding'), /allowance/i);
  for (let i = 0; i < 5; i += 1) store.consumePublication('jss_owner');
  assert.throws(() => store.consumePublication('jss_owner'), /allowance/i);
  assert.deepEqual(store.get('jss_owner').quota, { chatTurnsRemaining: 0, codingRunsRemaining: 0, publicationsRemaining: 0, reservedUsdRemaining: 0 });
});

test('sponsored sessions expire and release restores only an in-flight reservation', () => {
  let now = 1_000;
  const store = createJudgeSessionStore({ now: () => now, ttlMs: 100 });
  store.create({ sessionId: 'jss_owner', namespace: 'judge-private' });
  store.reserve('jss_owner', 'chat');
  store.release('jss_owner', 'chat');
  assert.equal(store.get('jss_owner').quota.chatTurnsRemaining, 30);
  now = 1_101;
  assert.throws(() => store.get('jss_owner'), /expired/i);
});

test('sponsored admission has a global session cap', () => {
  const store = createJudgeSessionStore({ maxSessions: 2 });
  store.create({ sessionId: 'jss_one', namespace: 'judge-one' });
  store.create({ sessionId: 'jss_two', namespace: 'judge-two' });
  assert.throws(() => store.create({ sessionId: 'jss_three', namespace: 'judge-three' }), /capacity/i);
});

test('default sponsored sessions remain valid for seven days', () => {
  let now = 1_000;
  const store = createJudgeSessionStore({ now: () => now });
  const session = store.create({ sessionId: 'jss_week', namespace: 'judge-week' });

  assert.equal(session.expiresAt, 1_000 + (7 * 24 * 60 * 60 * 1000));
  now = session.expiresAt - 1;
  assert.equal(store.get('jss_week').namespace, 'judge-week');
  now = session.expiresAt;
  assert.throws(() => store.get('jss_week'), /expired/i);
});

test('persisted quotas survive store recreation without refreshing allowance', () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'mnemagent-judge-store-'));
  const persistencePath = path.join(directory, 'sessions.json');
  const options = { now: () => 1_000, persistencePath };
  try {
    const first = createJudgeSessionStore(options);
    first.create({ sessionId: 'jss_persisted', namespace: 'judge-persisted' });
    first.reserve('jss_persisted', 'chat');
    first.settle('jss_persisted', 'chat');
    first.consumePublication('jss_persisted');

    const restored = createJudgeSessionStore(options);
    assert.deepEqual(restored.get('jss_persisted').quota, {
      chatTurnsRemaining: 29,
      codingRunsRemaining: 5,
      publicationsRemaining: 4,
      reservedUsdRemaining: 0.54,
    });
  } finally {
    fs.rmSync(directory, { recursive: true, force: true });
  }
});

test('store recreation refunds interrupted reservations and discards expired sessions', () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'mnemagent-judge-store-'));
  const persistencePath = path.join(directory, 'sessions.json');
  let now = 1_000;
  const options = { now: () => now, ttlMs: 100, persistencePath };
  try {
    const first = createJudgeSessionStore(options);
    first.create({ sessionId: 'jss_interrupted', namespace: 'judge-interrupted' });
    first.reserve('jss_interrupted', 'coding');

    const recovered = createJudgeSessionStore(options);
    assert.deepEqual(recovered.get('jss_interrupted').quota, {
      chatTurnsRemaining: 30,
      codingRunsRemaining: 5,
      publicationsRemaining: 5,
      reservedUsdRemaining: 0.55,
    });

    now = 1_101;
    const expired = createJudgeSessionStore(options);
    assert.throws(() => expired.get('jss_interrupted'), /expired/i);
  } finally {
    fs.rmSync(directory, { recursive: true, force: true });
  }
});
