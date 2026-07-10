const EMPTY_FILTERS = Object.freeze({ category: "all", lifecycle: "all", query: "" });

export function createInitialState(userId = "") {
  return { userId: String(userId || ""), status: "idle", graph: { memories: [], relationships: [], totalTurns: 0 }, metrics: null, events: [], failures: {}, selectedMemoryId: null, tracedMemoryId: null, filters: { ...EMPTY_FILTERS }, zoom: 1, motion: true, openingComplete: false, documentVisible: true };
}

const memoriesOf = state => Array.isArray(state?.graph?.memories) ? state.graph.memories : [];
export function archiveReducer(state = createInitialState(), action = {}) {
  const current = state || createInitialState();
  switch (action.type) {
    case "LOAD_STARTED": return { ...current, status: "loading", failures: {} };
    case "SNAPSHOT_RECEIVED": {
      const snapshot = action.snapshot || {};
      const graph = snapshot.graph || current.graph;
      const ids = new Set(memoriesOf({ graph }).map(m => m.id));
      return { ...current, status: snapshot.status || "ok", graph, metrics: snapshot.metrics ?? current.metrics, events: Array.isArray(snapshot.events) ? snapshot.events : current.events, failures: snapshot.failures || {}, selectedMemoryId: ids.has(current.selectedMemoryId) ? current.selectedMemoryId : null, tracedMemoryId: ids.has(current.tracedMemoryId) ? current.tracedMemoryId : null };
    }
    case "SNAPSHOT_FAILED": return { ...current, status: "error", failures: { ...current.failures, ...(action.failures || {}), error: action.error || current.failures.error } };
    case "SELECT_MEMORY": return { ...current, selectedMemoryId: action.memoryId ?? null };
    case "TRACE_MEMORY": return { ...current, tracedMemoryId: action.memoryId ?? null };
    case "CLEAR_FOCUS": return { ...current, selectedMemoryId: null, tracedMemoryId: null };
    case "SET_FILTERS": return { ...current, filters: { ...current.filters, ...(action.filters || {}) } };
    case "SET_ZOOM": return { ...current, zoom: Number.isFinite(Number(action.zoom)) ? Number(action.zoom) : current.zoom };
    case "SET_MOTION": return { ...current, motion: Boolean(action.motion) };
    case "OPENING_FINISHED": return { ...current, openingComplete: true };
    case "EVENTS_RECEIVED": return { ...current, events: Array.isArray(action.events) ? action.events : current.events };
    case "NARRATIVE_RECEIVED": return { ...current, narrative: action.narrative || null };
    case "SET_DOCUMENT_VISIBLE": return { ...current, documentVisible: Boolean(action.visible) };
    default: return current;
  }
}

export function createArchiveStore(initialState = createInitialState()) {
  let state = initialState; const listeners = new Set();
  return { getState: () => state, dispatch(action) { state = archiveReducer(state, action); listeners.forEach(fn => fn(state)); return action; }, subscribe(fn) { listeners.add(fn); return () => listeners.delete(fn); } };
}
