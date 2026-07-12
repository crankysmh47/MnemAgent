import assert from 'node:assert/strict';
import { test } from 'node:test';
import auth from '../src/judge-auth.js';

const { createJudgeAuth } = auth;

test('judge auth signs secure cookies and verifies CSRF-bound sessions', () => {
  const service = createJudgeAuth({ accessCode: 'correct horse battery staple', sessionSecret: 's'.repeat(48), secure: true, now: () => 1_000_000 });
  const issued = service.login({ accessCode: 'correct horse battery staple', ip: '127.0.0.1' });
  assert.match(issued.cookie, /HttpOnly/);
  assert.match(issued.cookie, /Secure/);
  assert.match(issued.cookie, /SameSite=Strict/);
  const session = service.verify({ cookieHeader: issued.cookie, csrfHeader: issued.csrf, origin: 'https://demo.example', host: 'demo.example', mutable: true });
  assert.equal(session.namespace, 'judge');
});

test('judge auth locks an IP after five failed attempts', () => {
  const service = createJudgeAuth({ accessCode: 'correct horse battery staple', sessionSecret: 's'.repeat(48), now: () => 1_000_000 });
  for (let attempt = 0; attempt < 4; attempt += 1) assert.throws(() => service.login({ accessCode: 'wrong', ip: '10.0.0.1' }), /invalid/i);
  assert.throws(() => service.login({ accessCode: 'wrong', ip: '10.0.0.1' }), /locked/i);
  assert.throws(() => service.login({ accessCode: 'correct horse battery staple', ip: '10.0.0.1' }), /locked/i);
});

test('mutable requests reject missing CSRF and cross-origin requests', () => {
  const service = createJudgeAuth({ accessCode: 'correct horse battery staple', sessionSecret: 's'.repeat(48), now: () => 1_000_000 });
  const issued = service.login({ accessCode: 'correct horse battery staple', ip: '127.0.0.1' });
  assert.throws(() => service.verify({ cookieHeader: issued.cookie, origin: 'https://demo.example', host: 'demo.example', mutable: true }), /csrf/i);
  assert.throws(() => service.verify({ cookieHeader: issued.cookie, csrfHeader: issued.csrf, origin: 'https://evil.example', host: 'demo.example', mutable: true }), /origin/i);
});
