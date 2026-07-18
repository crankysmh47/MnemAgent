const { createHmac, timingSafeEqual } = require('node:crypto');

function createInternalHmacVerifier({ secret, now = () => Math.floor(Date.now() / 1000), skewSeconds = 60 } = {}) {
  if (String(secret || '').length < 32) throw new Error('Strong internal HMAC secret is required.');
  const nonces = new Set();
  return {
    verify({ method, path, body, headers }) {
      const timestamp = Number(headers['x-mnemcode-timestamp']);
      const nonce = String(headers['x-mnemcode-nonce'] || '');
      const signature = String(headers['x-mnemcode-signature'] || '');
      if (!Number.isInteger(timestamp) || Math.abs(now() - timestamp) > skewSeconds || !nonce || nonces.has(nonce)) throw new Error(nonces.has(nonce) ? 'Internal request replay rejected.' : 'Internal request timestamp rejected.');
      const expected = createHmac('sha256', secret).update(`${method}\n${path}\n${timestamp}\n${nonce}\n${body}`).digest('hex');
      if (signature.length !== expected.length || !timingSafeEqual(Buffer.from(signature), Buffer.from(expected))) throw new Error('Internal request signature rejected.');
      nonces.add(nonce);
      if (nonces.size > 10_000) nonces.clear();
    },
  };
}

module.exports = { createInternalHmacVerifier };
