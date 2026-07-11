export function nextEscapeState(state = {}) {
  if (state.tracedMemoryId != null) return { ...state, tracedMemoryId: null };
  if (state.selectedMemoryId != null) return { ...state, selectedMemoryId: null };
  return { ...state, menuOpen: false };
}

export function filterMemory(memory = {}, filters = {}) {
  const categories = Array.isArray(filters.categories) ? filters.categories : [];
  const lifecycles = Array.isArray(filters.lifecycles) ? filters.lifecycles : [];
  return (!categories.length || categories.includes(memory.category)) && (!lifecycles.length || lifecycles.includes(memory.lifecycle));
}

export function createMemoryFocus(stage, store) {
  const keydown = event => { if (event.key === 'Escape') store?.dispatch({ type: 'CLEAR_FOCUS' }); };
  stage?.addEventListener('keydown', keydown);
  return { destroy() { stage?.removeEventListener('keydown', keydown); } };
}
