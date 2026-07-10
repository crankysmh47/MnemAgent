const RELATION_KINDS = new Set(['cluster', 'concept', 'bridge', 'affinity']);

export function tendrilClass(relationship = {}, state = 'quiet') {
  const kind = RELATION_KINDS.has(relationship.kind) ? relationship.kind : 'affinity';
  const safeState = state === 'active' ? 'is-active' : 'is-quiet';
  return `tendril tendril-${kind} ${safeState}`;
}

export function tendrilStrokeWidth(weight = 0.5) {
  return 0.8 + Math.max(0, Math.min(1, Number(weight) || 0)) * 1.8;
}
