import { applyLifecycleTransition } from './lifecycle-transitions.js';

const PRIORITY = Object.freeze({ contradiction: 60, pruned: 50, new_belief: 40, injected: 30, influenced: 25, decayed: 20 });

export function selectMotionEvent(events = [], seenIds = new Set()) {
  const unseen = (Array.isArray(events) ? events : []).filter(event => !seenIds.has(String(event?.id ?? '')));
  const ordered = unseen.slice().sort((a, b) => (PRIORITY[b?.eventType || b?.event_type] || 0) - (PRIORITY[a?.eventType || a?.event_type] || 0));
  return { featured: ordered[0] || null, quiet: ordered.slice(1), pulseLimit: 3 };
}

export function createChoreographer({ root = null, store = null, reducedMotion = false } = {}) {
  let openingComplete = false;
  let currentAbort = null;
  const timers = new Set();
  const play = (phase, callback = () => {}) => {
    const { duration } = applyLifecycleTransition(root, phase, reducedMotion);
    const timer = setTimeout(() => { timers.delete(timer); callback(); }, duration);
    timers.add(timer);
    return timer;
  };
  return {
    playOpening(memoryId) {
      this.cancel();
      currentAbort = new AbortController();
      openingComplete = false;
      play('opening-ground', () => play('opening-tree', () => play('opening-bloom', () => play('opening-settle', () => {
        openingComplete = true;
        if (root) applyLifecycleTransition(root, 'settled', reducedMotion);
        store?.dispatch({ type: 'OPENING_FINISHED', memoryId });
      }))));
      return memoryId;
    },
    enqueue(decision) { if (decision?.featured) play(decision.featured.eventType || decision.featured.event_type); },
    replay(event) { if (event) play(event.eventType || event.event_type); },
    cancel() { currentAbort?.abort(); currentAbort = null; for (const timer of timers) clearTimeout(timer); timers.clear(); },
    isOpeningComplete() { return openingComplete; },
    destroy() { this.cancel(); },
  };
}
