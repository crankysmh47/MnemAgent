import { loadArchiveSnapshot, resolveUserId } from './api.js';
import { createArchiveStore } from './archive-store.js';
import { normalizeEvent, narrativeCopy, selectNarrative } from './narrative.js';
import { normalizeGraph } from './memory-model.js';
import { computeArchiveLayout } from './layout.js';
import { createLivingStructure } from './render/living-structure.js';
import { renderCompanionList, renderObservation } from './render/annotations.js';
import { createTimeline } from './render/timeline.js';
import { createChoreographer, selectMotionEvent } from './motion/choreographer.js';
import { createAmbientMotion } from './motion/ambient-motion.js';
import { applyLifecycleTransition } from './motion/lifecycle-transitions.js';
import { createArchiveNavigation } from './interactions/archive-navigation.js';
import { createMemoryFocus, filterMemory } from './interactions/memory-focus.js';
import { createArchiveMenu } from './interactions/archive-menu.js';

export function structuralKey(snapshot = {}) {
  const memories = snapshot.memories || snapshot.beliefs || [];
  const relationships = snapshot.relationships || snapshot.edges || [];
  return `${memories.map(memory => String(memory.id)).sort().join('|')}#${relationships.map(edge => `${edge.source}-${edge.target}`).sort().join('|')}`;
}

export function statusFromSnapshot(snapshot = {}) {
  if (!snapshot.graph) return 'error';
  const beliefs = snapshot.graph.beliefs || snapshot.graph.memories || [];
  if (!Array.isArray(beliefs)) return 'error';
  if (!beliefs.length) return 'empty';
  return Object.keys(snapshot.failures || {}).length ? 'degraded' : 'ready';
}

export function shouldSeedDemo(userId, status = {}) { return userId === 'demo-brain' && Number(status.beliefs) < 8; }

function viewportSize(svg) { return { width: Math.max(640, svg?.clientWidth || 1000), height: Math.max(500, svg?.clientHeight || 720) }; }

export async function bootstrapArchive() {
  if (typeof document === 'undefined') return null;
  const app = document.querySelector('#archiveApp');
  const svg = document.querySelector('#archiveSvg');
  const userId = await resolveUserId(location.search, window.localStorage);
  const store = createArchiveStore();
  store.dispatch({ type: 'LOAD_STARTED' });
  const renderer = createLivingStructure(svg, { onSelect: id => store.dispatch({ type: 'SELECT_MEMORY', memoryId: id }), onTrace: id => store.dispatch({ type: 'TRACE_MEMORY', memoryId: id }) });
  const timeline = createTimeline(document.querySelector('#sedimentTimeline'), { onReplay: event => choreographer.replay(event) });
  const choreographer = createChoreographer({ root: document.querySelector('#archiveStage'), store, reducedMotion: window.matchMedia?.('(prefers-reduced-motion: reduce)').matches || false });
  const ambient = createAmbientMotion(document.querySelector('#archiveStage'), store);
  const navigation = createArchiveNavigation(svg, document.querySelector('#archiveWorld'), store);
  const focus = createMemoryFocus(document.querySelector('#archiveStage'), store);
  const menu = createArchiveMenu(document.querySelector('#archiveMenu'), store, { onReplayOpening: () => choreographer.playOpening(store.getState().graph.memories[0]?.id), onReset: () => navigation.reset(), onRetry: () => refresh(true), onExport: () => exportState(store.getState()) });
  let lastStructure = '';
  let seenIds = new Set();
  let abortController = null;
  store.subscribe(() => renderState());

  function renderState() {
    const state = store.getState();
    const size = viewportSize(svg);
    const visible = state.graph.memories.filter(memory => filterMemory(memory, { categories: state.filters.category === 'all' ? [] : [state.filters.category], lifecycles: state.filters.lifecycle === 'all' ? [] : [state.filters.lifecycle] }));
    const layout = computeArchiveLayout(visible, state.graph.relationships, { ...size, selectedMemoryId: state.selectedMemoryId });
    renderer.render({ memories: visible }, layout, state);
    renderObservation(document.querySelector('#observationMargin'), { ...state, memories: visible, relationships: state.graph.relationships }, narrativeCopy(state.narrative || {}, state.graph.memories.find(memory => String(memory.id) === String(state.selectedMemoryId))));
    renderCompanionList(document.querySelector('#memoryCompanionList'), visible, state.selectedMemoryId);
    timeline.render(state.events);
    app.dataset.status = state.status;
    document.querySelector('#liveState').textContent = state.status === 'ready' ? 'Archive alive' : state.status;
    document.querySelector('#archiveStatus').textContent = `${visible.length} memories, ${state.graph.relationships.length} relationships, status ${state.status}`;
  }

  async function refresh(structural = false) {
    abortController?.abort(); abortController = new AbortController();
    try {
      const raw = await loadArchiveSnapshot(userId, { since: store.getState().events.at(-1)?.timestamp, signal: abortController.signal });
      const graph = raw.graph ? normalizeGraph(raw.graph) : null;
      const snapshot = { ...raw, graph, status: statusFromSnapshot(raw) };
      store.dispatch({ type: graph ? 'SNAPSHOT_RECEIVED' : 'SNAPSHOT_FAILED', snapshot, failures: raw.failures });
      if (graph) {
        const eventsPayload = Array.isArray(raw.events) ? raw.events : raw.events?.events;
        const events = (eventsPayload || []).map(normalizeEvent);
        const decision = selectNarrative(events, seenIds); seenIds = decision.seenIds;
        store.dispatch({ type: 'EVENTS_RECEIVED', events });
        store.dispatch({ type: 'SNAPSHOT_RECEIVED', snapshot: { ...snapshot, graph, events, status: snapshot.status } });
        store.dispatch({ type: 'NARRATIVE_RECEIVED', narrative: decision });
        renderState();
        if (!store.getState().openingComplete && graph.memories.length) choreographer.playOpening(graph.memories[0].id);
        else if (decision.featured) choreographer.enqueue(decision);
        if (snapshot.status === 'ready') ambient.start();
      } else renderState();
    } catch (error) {
      if (error.name !== 'AbortError') { console.error('Archive refresh failed:', error); store.dispatch({ type: 'SNAPSHOT_FAILED', error: error.message }); renderState(); }
    }
    return store.getState();
  }

  const onResize = () => renderState();
  window.addEventListener('resize', onResize);
  await refresh(true);
  const poll = window.setInterval(() => refresh(false), 15000);
  return { store, refresh, changeUser: () => refresh(true), destroy() { window.clearInterval(poll); window.removeEventListener('resize', onResize); ambient.destroy(); choreographer.destroy(); renderer.destroy(); timeline.destroy(); navigation.destroy(); focus.destroy(); menu.destroy(); abortController?.abort(); } };
}

function exportState(state) { const blob = new Blob([JSON.stringify(state, null, 2)], { type: 'application/json' }); const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = 'mnemagent-living-archive.json'; link.click(); URL.revokeObjectURL(link.href); }

if (typeof document !== 'undefined') bootstrapArchive().catch(error => { const status = document.querySelector('#archiveStatus'); if (status) status.textContent = `Archive failed to awaken: ${error.message}`; });
