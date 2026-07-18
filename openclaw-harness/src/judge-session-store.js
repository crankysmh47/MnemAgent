const CHAT_RESERVE_USD = 0.01;
const CODING_RESERVE_USD = 0.05;

function snapshot(entry) {
  return {
    sessionId: entry.sessionId,
    namespace: entry.namespace,
    expiresAt: entry.expiresAt,
    quota: { ...entry.quota },
  };
}

function createJudgeSessionStore({ now = Date.now, ttlMs = 60 * 60 * 1000, maxSessions = Number(process.env.JUDGE_MAX_SPONSORED_SESSIONS || 12) } = {}) {
  const sessions = new Map();
  let admittedSessions = 0;
  const requireSession = sessionId => {
    const entry = sessions.get(sessionId);
    if (!entry || entry.expiresAt <= now()) {
      sessions.delete(sessionId);
      throw new Error('Judge session expired.');
    }
    return entry;
  };
  return {
    create({ sessionId, namespace }) {
      if (!sessionId || !namespace) throw new Error('Judge session identity is required.');
      if (admittedSessions >= maxSessions) throw new Error('Sponsored demo capacity has been reached.');
      const entry = {
        sessionId,
        namespace,
        expiresAt: now() + ttlMs,
        quota: { chatTurnsRemaining: 3, codingRunsRemaining: 1, publicationsRemaining: 1, reservedUsdRemaining: 0.1 },
        inFlight: { chat: 0, coding: 0 },
      };
      sessions.set(sessionId, entry);
      admittedSessions += 1;
      return snapshot(entry);
    },
    get(sessionId) { return snapshot(requireSession(sessionId)); },
    reserve(sessionId, kind) {
      const entry = requireSession(sessionId);
      const field = kind === 'chat' ? 'chatTurnsRemaining' : kind === 'coding' ? 'codingRunsRemaining' : null;
      const cost = kind === 'chat' ? CHAT_RESERVE_USD : kind === 'coding' ? CODING_RESERVE_USD : 0;
      if (!field || entry.quota[field] < 1 || entry.quota.reservedUsdRemaining + Number.EPSILON < cost) throw new Error('Sponsored allowance exhausted.');
      entry.quota[field] -= 1;
      entry.quota.reservedUsdRemaining = Number((entry.quota.reservedUsdRemaining - cost).toFixed(2));
      entry.inFlight[kind] += 1;
      return snapshot(entry);
    },
    release(sessionId, kind) {
      const entry = requireSession(sessionId);
      if (!entry.inFlight[kind]) return snapshot(entry);
      const field = kind === 'chat' ? 'chatTurnsRemaining' : 'codingRunsRemaining';
      const cost = kind === 'chat' ? CHAT_RESERVE_USD : CODING_RESERVE_USD;
      entry.inFlight[kind] -= 1;
      entry.quota[field] += 1;
      entry.quota.reservedUsdRemaining = Number(Math.min(0.1, entry.quota.reservedUsdRemaining + cost).toFixed(2));
      return snapshot(entry);
    },
    settle(sessionId, kind) {
      const entry = requireSession(sessionId);
      if (entry.inFlight[kind]) entry.inFlight[kind] -= 1;
      return snapshot(entry);
    },
    consumePublication(sessionId) {
      const entry = requireSession(sessionId);
      if (entry.quota.publicationsRemaining < 1) throw new Error('Sponsored publication allowance exhausted.');
      entry.quota.publicationsRemaining -= 1;
      return snapshot(entry);
    },
  };
}

module.exports = { createJudgeSessionStore };
