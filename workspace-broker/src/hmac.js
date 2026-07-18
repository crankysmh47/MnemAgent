import { createHmac, timingSafeEqual } from 'node:crypto';

function signature({ method, path, timestamp, nonce, body, secret }) {
  return createHmac('sha256', secret).update(`${method}\n${path}\n${timestamp}\n${nonce}\n${body}`).digest('hex');
}

export function createHmacHeaders({ method, path, body = '', secret, now = Math.floor(Date.now() / 1000), nonce }) {
  return {
    'x-mnemcode-timestamp': String(now),
    'x-mnemcode-nonce': nonce,
    'x-mnemcode-signature': signature({ method, path, timestamp: now, nonce, body, secret }),
  };
}

export function verifyHmacRequest({ method, path, body = '', headers, secret, now = Math.floor(Date.now() / 1000), nonces }) {
  const timestamp = Number(headers['x-mnemcode-timestamp']);
  const nonce = String(headers['x-mnemcode-nonce'] || '');
  const supplied = String(headers['x-mnemcode-signature'] || '');
  if (!Number.isInteger(timestamp) || Math.abs(now - timestamp) > 60 || !/^[A-Za-z0-9_-]{8,100}$/.test(nonce)) throw new Error('Invalid broker signature timestamp or nonce.');
  if (nonces.has(nonce)) throw new Error('Broker request replay detected.');
  const expected = signature({ method, path, timestamp, nonce, body, secret });
  if (supplied.length !== expected.length || !timingSafeEqual(Buffer.from(supplied), Buffer.from(expected))) throw new Error('Invalid broker signature.');
  nonces.add(nonce);
  return true;
}
