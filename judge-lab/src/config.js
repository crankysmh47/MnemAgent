const DEFAULT_TIMEOUT_MS = 2_000;
const DEFAULT_MAX_BODY_BYTES = 16_384;

export function parsePositiveInteger(value, fallback) {
  if (value === undefined || value === '') return fallback;
  if (!/^\d+$/.test(String(value))) throw new Error('must be a positive integer');
  const parsed = Number(value);
  if (!Number.isSafeInteger(parsed) || parsed < 1) throw new Error('must be a positive integer');
  return parsed;
}

export function loadConfig(env = process.env) {
  return {
    timeoutMs: parsePositiveInteger(env.REQUEST_TIMEOUT_MS, DEFAULT_TIMEOUT_MS),
    maxBodyBytes: parsePositiveInteger(env.MAX_BODY_BYTES, DEFAULT_MAX_BODY_BYTES),
  };
}
