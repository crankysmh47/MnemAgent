import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequestPolicy } from '../src/server.js';

test('rejects bodies larger than the configured limit', () => {
  const policy = createRequestPolicy({ MAX_BODY_BYTES: '10' });
  assert.equal(policy.acceptsBodyBytes(10), true);
  assert.equal(policy.acceptsBodyBytes(11), false);
});
