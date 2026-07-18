import { createHmac, timingSafeEqual } from 'node:crypto';

const TTL_SECONDS = 300;
function sign(payload, secret) { return createHmac('sha256', secret).update(payload).digest('base64url'); }

export function createApproval({ runId, diffHash, metadataHash, secret, now = Math.floor(Date.now() / 1000) }) {
  const expiresAt = now + TTL_SECONDS;
  const payload = `${runId}:${diffHash}:${metadataHash}:${expiresAt}`;
  return { expiresAt, token: sign(payload, secret) };
}

export function verifyApproval({ token, expiresAt, runId, diffHash, metadataHash, secret, now = Math.floor(Date.now() / 1000) }) {
  if (now > expiresAt) throw new Error('Approval expired.');
  const expected = sign(`${runId}:${diffHash}:${metadataHash}:${expiresAt}`, secret);
  if (token.length !== expected.length || !timingSafeEqual(Buffer.from(token), Buffer.from(expected))) throw new Error('Approval is invalid for the current diff.');
  return true;
}
