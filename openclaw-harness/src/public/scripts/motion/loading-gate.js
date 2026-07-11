export function createLoadingGate({ minimumMs = 1400, now = () => Date.now(), wait = ms => new Promise(resolve => setTimeout(resolve, ms)) } = {}) {
  const startedAt = now();
  let signalReady;
  let released = false;
  const readiness = new Promise(resolve => { signalReady = resolve; });
  return {
    ready() { signalReady(); },
    async release() {
      await readiness;
      const remaining = Math.max(0, minimumMs - (now() - startedAt));
      if (remaining) await wait(remaining);
      released = true;
      return true;
    },
    isReleased() { return released; },
  };
}
