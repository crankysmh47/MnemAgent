const { createHmac, randomBytes, timingSafeEqual } = require('node:crypto');

const SESSION_SECONDS = 7 * 24 * 60 * 60;
const LOCK_SECONDS = 30 * 60;

function safeEqual(left, right) {
  const a = createHmac('sha256', 'mnemcode-access').update(String(left)).digest();
  const b = createHmac('sha256', 'mnemcode-access').update(String(right)).digest();
  return timingSafeEqual(a, b);
}

function createJudgeAuth({ accessCode, sessionSecret, secure = false, now = () => Math.floor(Date.now() / 1000) }) {
  if (String(accessCode || '').length < 16 || String(sessionSecret || '').length < 32) throw new Error('Strong judge authentication secrets are required.');
  const attempts = new Map();
  const sign = value => createHmac('sha256', sessionSecret).update(value).digest('base64url');
  return {
    login({ accessCode: supplied, ip = 'unknown' }) {
      const state = attempts.get(ip) || { failures: 0, lockedUntil: 0 };
      if (state.lockedUntil > now()) throw new Error('Judge access is temporarily locked.');
      if (!safeEqual(supplied, accessCode)) {
        state.failures += 1;
        if (state.failures >= 5) state.lockedUntil = now() + LOCK_SECONDS;
        attempts.set(ip, state);
        throw new Error(state.lockedUntil ? 'Judge access is temporarily locked.' : 'Invalid judge access code.');
      }
      attempts.delete(ip);
      const csrf = randomBytes(24).toString('base64url');
      const sessionId = `jss_${randomBytes(12).toString('hex')}`;
      const namespace = `judge-${randomBytes(8).toString('hex')}`;
      const payload = Buffer.from(JSON.stringify({ sessionId, namespace, exp: now() + SESSION_SECONDS, csrf })).toString('base64url');
      const token = `${payload}.${sign(payload)}`;
      const flags = [`mnemcode_judge=${token}`, 'Path=/', 'HttpOnly', 'SameSite=Strict', `Max-Age=${SESSION_SECONDS}`];
      if (secure) flags.push('Secure');
      return { csrf, sessionId, namespace, expiresAt: (now() + SESSION_SECONDS) * 1000, cookie: flags.join('; ') };
    },
    verify({ cookieHeader = '', csrfHeader, origin, host, mutable = false }) {
      const token = /(?:^|;\s*)mnemcode_judge=([^;]+)/.exec(cookieHeader)?.[1];
      if (!token) throw new Error('Judge session is required.');
      const [payload, suppliedSignature] = token.split('.');
      const expected = sign(payload || '');
      if (!suppliedSignature || suppliedSignature.length !== expected.length || !timingSafeEqual(Buffer.from(suppliedSignature), Buffer.from(expected))) throw new Error('Judge session is invalid.');
      const session = JSON.parse(Buffer.from(payload, 'base64url').toString('utf8'));
      if (!/^jss_[a-f0-9]{24}$/.test(session.sessionId || '') || !/^judge-[a-f0-9]{16}$/.test(session.namespace || '') || session.exp < now()) throw new Error('Judge session expired.');
      if (mutable) {
        if (!safeEqual(csrfHeader || '', session.csrf)) throw new Error('CSRF validation failed.');
        let originHost;
        try { originHost = new URL(origin).host; } catch { throw new Error('Origin validation failed.'); }
        if (originHost !== host) throw new Error('Origin validation failed.');
      }
      return session;
    },
  };
}

module.exports = { createJudgeAuth };
