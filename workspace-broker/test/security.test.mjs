import assert from 'node:assert/strict';
import { test } from 'node:test';
import { createHmacHeaders, verifyHmacRequest } from '../src/hmac.js';
import { createApproval, verifyApproval } from '../src/approval.js';

test('signed broker requests cannot be replayed', () => {
  const secret = 'a'.repeat(32);
  const body = JSON.stringify({ issueNumber: 1 });
  const headers = createHmacHeaders({ method: 'POST', path: '/v1/workspaces', body, secret, now: 1000, nonce: 'nonce-12345678' });
  const nonces = new Set();
  assert.equal(verifyHmacRequest({ method: 'POST', path: '/v1/workspaces', body, headers, secret, now: 1000, nonces }), true);
  assert.throws(() => verifyHmacRequest({ method: 'POST', path: '/v1/workspaces', body, headers, secret, now: 1000, nonces }), /replay/i);
});

test('approval is invalidated when the diff changes or expires', () => {
  const secret = 'b'.repeat(32);
  const approval = createApproval({ runId: 'run_1', diffHash: 'diff-a', metadataHash: 'meta-a', secret, now: 1000 });
  assert.equal(verifyApproval({ ...approval, runId: 'run_1', diffHash: 'diff-a', metadataHash: 'meta-a', secret, now: 1100 }), true);
  assert.throws(() => verifyApproval({ ...approval, runId: 'run_1', diffHash: 'diff-b', metadataHash: 'meta-a', secret, now: 1100 }), /invalid/i);
  assert.throws(() => verifyApproval({ ...approval, runId: 'run_1', diffHash: 'diff-a', metadataHash: 'meta-a', secret, now: 1401 }), /expired/i);
});
