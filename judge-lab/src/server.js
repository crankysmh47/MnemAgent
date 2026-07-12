import { loadConfig } from './config.js';

export function createRequestPolicy(env = process.env) {
  const config = loadConfig(env);
  return {
    timeoutMs: config.timeoutMs,
    acceptsBodyBytes(size) {
      return Number.isSafeInteger(size) && size >= 0 && size <= config.maxBodyBytes;
    },
  };
}
