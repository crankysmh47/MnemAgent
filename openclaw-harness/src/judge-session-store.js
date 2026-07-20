const fs = require('node:fs');
const path = require('node:path');

const CHAT_RESERVE_USD = 0.01;
const CODING_RESERVE_USD = 0.05;
const CHAT_TURN_LIMIT = 30;
const CODING_RUN_LIMIT = 5;
const PUBLICATION_LIMIT = 5;
const SESSION_RESERVE_USD = 0.55;
const DEFAULT_TTL_MS = 7 * 24 * 60 * 60 * 1000;

function snapshot(entry) {
  return {
    sessionId: entry.sessionId,
    namespace: entry.namespace,
    expiresAt: entry.expiresAt,
    quota: { ...entry.quota },
  };
}

function createJudgeSessionStore({
  now = Date.now,
  ttlMs = DEFAULT_TTL_MS,
  maxSessions = Number(process.env.JUDGE_MAX_SPONSORED_SESSIONS || 12),
  persistencePath = process.env.JUDGE_SESSION_STORE_PATH || '',
} = {}) {
  const sessions = new Map();
  const statePath = String(persistencePath || '').trim();

  const persist = () => {
    if (!statePath) return;
    fs.mkdirSync(path.dirname(statePath), { recursive: true });
    const temporaryPath = `${statePath}.${process.pid}.${Date.now()}.tmp`;
    const payload = JSON.stringify({ version: 1, sessions: [...sessions.values()] });
    try {
      fs.writeFileSync(temporaryPath, payload, { encoding: 'utf8', mode: 0o600 });
      fs.renameSync(temporaryPath, statePath);
    } finally {
      fs.rmSync(temporaryPath, { force: true });
    }
  };

  const restore = () => {
    if (!statePath || !fs.existsSync(statePath)) return;
    const parsed = JSON.parse(fs.readFileSync(statePath, 'utf8'));
    if (parsed?.version !== 1 || !Array.isArray(parsed.sessions)) throw new Error('Judge session state is invalid.');
    let changed = false;
    for (const candidate of parsed.sessions) {
      if (!candidate?.sessionId || !candidate?.namespace || !Number.isFinite(candidate.expiresAt)) {
        changed = true;
        continue;
      }
      if (candidate.expiresAt <= now()) {
        changed = true;
        continue;
      }
      const quota = {
        chatTurnsRemaining: Number(candidate.quota?.chatTurnsRemaining),
        codingRunsRemaining: Number(candidate.quota?.codingRunsRemaining),
        publicationsRemaining: Number(candidate.quota?.publicationsRemaining),
        reservedUsdRemaining: Number(candidate.quota?.reservedUsdRemaining),
      };
      if (Object.values(quota).some(value => !Number.isFinite(value))) throw new Error('Judge session quota state is invalid.');
      const interruptedChat = Math.max(0, Number(candidate.inFlight?.chat) || 0);
      const interruptedCoding = Math.max(0, Number(candidate.inFlight?.coding) || 0);
      if (interruptedChat || interruptedCoding) {
        quota.chatTurnsRemaining = Math.min(CHAT_TURN_LIMIT, quota.chatTurnsRemaining + interruptedChat);
        quota.codingRunsRemaining = Math.min(CODING_RUN_LIMIT, quota.codingRunsRemaining + interruptedCoding);
        quota.reservedUsdRemaining = Number(Math.min(
          SESSION_RESERVE_USD,
          quota.reservedUsdRemaining + (interruptedChat * CHAT_RESERVE_USD) + (interruptedCoding * CODING_RESERVE_USD),
        ).toFixed(2));
        changed = true;
      }
      sessions.set(candidate.sessionId, {
        sessionId: candidate.sessionId,
        namespace: candidate.namespace,
        expiresAt: candidate.expiresAt,
        quota,
        inFlight: { chat: 0, coding: 0 },
      });
    }
    if (changed) persist();
  };

  restore();

  const requireSession = sessionId => {
    const entry = sessions.get(sessionId);
    if (!entry || entry.expiresAt <= now()) {
      sessions.delete(sessionId);
      persist();
      throw new Error('Judge session expired.');
    }
    return entry;
  };
  return {
    create({ sessionId, namespace }) {
      if (!sessionId || !namespace) throw new Error('Judge session identity is required.');
      for (const [existingId, existing] of sessions) {
        if (existing.expiresAt <= now()) sessions.delete(existingId);
      }
      if (sessions.size >= maxSessions) throw new Error('Sponsored demo capacity has been reached.');
      const entry = {
        sessionId,
        namespace,
        expiresAt: now() + ttlMs,
        quota: {
          chatTurnsRemaining: CHAT_TURN_LIMIT,
          codingRunsRemaining: CODING_RUN_LIMIT,
          publicationsRemaining: PUBLICATION_LIMIT,
          reservedUsdRemaining: SESSION_RESERVE_USD,
        },
        inFlight: { chat: 0, coding: 0 },
      };
      sessions.set(sessionId, entry);
      persist();
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
      persist();
      return snapshot(entry);
    },
    release(sessionId, kind) {
      const entry = requireSession(sessionId);
      if (!entry.inFlight[kind]) return snapshot(entry);
      const field = kind === 'chat' ? 'chatTurnsRemaining' : 'codingRunsRemaining';
      const cost = kind === 'chat' ? CHAT_RESERVE_USD : CODING_RESERVE_USD;
      entry.inFlight[kind] -= 1;
      entry.quota[field] += 1;
      entry.quota.reservedUsdRemaining = Number(Math.min(SESSION_RESERVE_USD, entry.quota.reservedUsdRemaining + cost).toFixed(2));
      persist();
      return snapshot(entry);
    },
    settle(sessionId, kind) {
      const entry = requireSession(sessionId);
      if (entry.inFlight[kind]) entry.inFlight[kind] -= 1;
      persist();
      return snapshot(entry);
    },
    consumePublication(sessionId) {
      const entry = requireSession(sessionId);
      if (entry.quota.publicationsRemaining < 1) throw new Error('Sponsored publication allowance exhausted.');
      entry.quota.publicationsRemaining -= 1;
      persist();
      return snapshot(entry);
    },
  };
}

module.exports = { createJudgeSessionStore };
