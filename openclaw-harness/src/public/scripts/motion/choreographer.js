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
    const duration = reducedMotion ? Math.min(180, phase === 'opening-skeleton' ? 20 : 160) : ({ 'opening-skeleton': 2000, 'opening-branches': 3000, 'opening-root': 3000, 'opening-annotations': 2000 }[phase] || 160);
    if (root) { root.dataset.phase = phase; root.classList.add(`phase-${phase}`); }
    const timer = setTimeout(() => { timers.delete(timer); callback(); }, duration); timers.add(timer); return timer;
  };
  return {
    playOpening(memoryId) { currentAbort?.abort(); currentAbort = new AbortController(); play('opening-skeleton', () => play('opening-branches', () => play('opening-root', () => play('opening-annotations', () => { openingComplete = true; store?.dispatch({ type: 'OPENING_FINISHED', memoryId }); })))); return memoryId; },
    enqueue(decision) { if (decision?.featured) play(decision.featured.eventType || decision.featured.event_type); },
    replay(event) { if (event) play(event.eventType || event.event_type); },
    cancel() { currentAbort?.abort(); for (const timer of timers) clearTimeout(timer); timers.clear(); },
    isOpeningComplete() { return openingComplete; },
    destroy() { this.cancel(); },
  };
}
