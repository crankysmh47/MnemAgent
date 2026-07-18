import assert from 'node:assert/strict';
import { createHmac } from 'node:crypto';
import { test } from 'node:test';
import hmacModule from '../src/internal-hmac.js';

const { createInternalHmacVerifier } = hmacModule;

test('internal callback verifier accepts one current signature and rejects replay', () => {
  const secret = 's'.repeat(64);
  const verifier = createInternalHmacVerifier({ secret, now: () => 1_000 });
  const body = '{"runId":"run_1"}';
  const path = '/api/judge/internal/events';
  const nonce = 'nonce-1';
  const signature = createHmac('sha256', secret).update(`POST\n${path}\n1000\n${nonce}\n${body}`).digest('hex');
  const request = { method: 'POST', path, body, headers: { 'x-mnemcode-timestamp': '1000', 'x-mnemcode-nonce': nonce, 'x-mnemcode-signature': signature } };
  assert.doesNotThrow(() => verifier.verify(request));
  assert.throws(() => verifier.verify(request), /replay/i);
});
