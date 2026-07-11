import { loadArchiveSnapshot, resolveUserId } from './api.js';
import { createArchiveStore } from './archive-store.js';
import { normalizeEvent, narrativeCopy, selectNarrative } from './narrative.js';
import { normalizeGraph } from './memory-model.js';
import { computeArchiveLayout } from './layout.js';
import { createLivingStructure } from './render/living-structure.js';
import { renderCompanionList, renderMaterialLegend, renderObservation } from './render/annotations.js';
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

export function relatedMemoryIds(memoryId, relationships = []) { const related=new Set(); if(memoryId==null) return related; const id=String(memoryId); for(const edge of relationships){ if(String(edge.source)===id) related.add(String(edge.target)); else if(String(edge.target)===id) related.add(String(edge.source)); } return related; }

export function selectRenderableRelationships(relationships = [], focusedId = null, limit = 96) { const priority={cluster:4,concept:3,bridge:2,affinity:1,related:0}; const sorted=[...relationships].sort((a,b)=>(priority[b.kind]||0)-(priority[a.kind]||0)||(Number(b.weight)||0)-(Number(a.weight)||0)); if(focusedId==null) return sorted.slice(0,limit); const id=String(focusedId); const incident=sorted.filter(edge=>String(edge.source)===id||String(edge.target)===id); const incidentKeys=new Set(incident.map(edge=>`${edge.source}|${edge.target}|${edge.kind}`)); const context=sorted.filter(edge=>!incidentKeys.has(`${edge.source}|${edge.target}|${edge.kind}`)).slice(0,Math.max(18,limit-incident.length)); return [...incident,...context].slice(0,Math.max(limit,incident.length)); }

function viewportSize(svg) { return { width: Math.max(640, svg?.clientWidth || 1000), height: Math.max(500, svg?.clientHeight || 720) }; }

export async function bootstrapArchive() {
  if (typeof document === 'undefined') return null;
  const app = document.querySelector('#archiveApp');
  const svg = document.querySelector('#archiveSvg');
  const stage = document.querySelector('#archiveStage');
  const loader = document.querySelector('#archiveLoader');
  stage.setAttribute('data-loading', 'true');
  let currentUserId = await resolveUserId(location.search, window.localStorage);
  const store = createArchiveStore();
  store.dispatch({ type: 'LOAD_STARTED' });
  const renderer = createLivingStructure(svg, { onSelect: id => store.dispatch({ type: 'SELECT_MEMORY', memoryId: id }), onTrace: id => store.dispatch({ type: 'TRACE_MEMORY', memoryId: id }) });
  const timeline = createTimeline(document.querySelector('#sedimentTimeline'), { onReplay: event => choreographer.replay(event) });
  const choreographer = createChoreographer({ root: stage, store, reducedMotion: window.matchMedia?.('(prefers-reduced-motion: reduce)').matches || false });
  const ambient = createAmbientMotion(stage, store);
  const navigation = createArchiveNavigation(svg, document.querySelector('#archiveWorld'), store);
  const focus = createMemoryFocus(document.querySelector('#archiveStage'), store);
  const menu = createArchiveMenu(document.querySelector('#archiveMenu'), store, { userId:currentUserId, onUserChange: userId => { if(!userId||userId===currentUserId) return; window.localStorage.setItem('mnemos_user_id',userId); const next=new URL(location.href); next.searchParams.set('user',userId); location.assign(next.toString()); }, onReplayOpening: () => choreographer.playOpening(store.getState().graph.memories[0]?.id), onReset: () => navigation.reset(), onRetry: () => refresh(true), onExport: () => exportState(store.getState()) });
  let lastStructure = '';
  let seenIds = new Set();
  let abortController = null;
  store.subscribe(() => renderState());

  function renderState() {
    const state = store.getState();
    const size = viewportSize(svg);
    const visible = state.graph.memories.filter(memory => filterMemory(memory, { categories: state.filters.category === 'all' ? [] : [state.filters.category], lifecycles: state.filters.lifecycle === 'all' ? [] : [state.filters.lifecycle] }));
    const focusedMemoryId=state.tracedMemoryId??state.selectedMemoryId;
    const renderRelationships=selectRenderableRelationships(state.graph.relationships,focusedMemoryId,96);
    const related=[...relatedMemoryIds(focusedMemoryId,state.graph.relationships)];
    const layout = computeArchiveLayout(visible, renderRelationships, { ...size, selectedMemoryId: focusedMemoryId });
    renderer.render({ memories: visible }, layout, { ...state, selectedMemoryId:focusedMemoryId, relatedMemoryIds:related });
    const observationState={ ...state, memories: visible, relationships: renderRelationships };
    const copy=narrativeCopy(state.narrative || {}, state.graph.memories.find(memory => String(memory.id) === String(focusedMemoryId)));
    renderObservation(document.querySelector('#observationMargin'), observationState, copy);
    renderObservation(document.querySelector('#observationSheetContent'), observationState, copy);
    renderMaterialLegend(document.querySelector('#materialLegend'));
    renderCompanionList(document.querySelector('#memoryCompanionList'), visible, focusedMemoryId, memoryId=>store.dispatch({type:'SELECT_MEMORY',memoryId}));
    timeline.render(state.events);
    app.dataset.status = state.status;
    document.querySelector('#archiveStatus').textContent = `${visible.length} memories, ${renderRelationships.length} active relationships, status ${state.status}`;
  }

  async function refresh(structural = false) {
    abortController?.abort(); abortController = new AbortController();
    try {
      const latestTimestamp=store.getState().events.map(event=>event.timestamp).filter(Boolean).sort().at(-1);
      const raw = await loadArchiveSnapshot(currentUserId, { since: latestTimestamp, signal: abortController.signal });
      const graph = raw.graph ? normalizeGraph(raw.graph) : null;
      const snapshot = { ...raw, graph, status: statusFromSnapshot(raw) };
      store.dispatch({ type: graph ? 'SNAPSHOT_RECEIVED' : 'SNAPSHOT_FAILED', snapshot, failures: raw.failures });
      if (graph) {
        const eventsPayload = Array.isArray(raw.events) ? raw.events : raw.events?.events;
        const incoming = (eventsPayload || []).map(normalizeEvent);
        const eventMap=new Map([...incoming,...store.getState().events].map(event=>[String(event.id),event]));
        const events=[...eventMap.values()].sort((a,b)=>String(b.timestamp||'').localeCompare(String(a.timestamp||''))).slice(0,100);
        const decision = selectNarrative(incoming, seenIds); seenIds = decision.seenIds;
        store.dispatch({ type: 'EVENTS_RECEIVED', events });
        store.dispatch({ type: 'SNAPSHOT_RECEIVED', snapshot: { ...snapshot, graph, events, status: snapshot.status } });
        if(decision.featured) store.dispatch({ type: 'NARRATIVE_RECEIVED', narrative: decision });
        renderState();
        if (!store.getState().openingComplete && graph.memories.length) {
          stage.setAttribute('data-loading', 'false');
          loader?.setAttribute('aria-hidden', 'true');
          choreographer.playOpening(graph.memories[0].id);
        }
        else if (decision.featured) choreographer.enqueue(decision);
        if (snapshot.status === 'ready') ambient.start();
      } else {
        stage.setAttribute('data-loading', 'false');
        loader?.setAttribute('aria-hidden', 'true');
        renderState();
      }
    } catch (error) {
      if (error.name !== 'AbortError') { console.error('Archive refresh failed:', error); stage.setAttribute('data-loading', 'false'); loader?.setAttribute('aria-hidden', 'true'); store.dispatch({ type: 'SNAPSHOT_FAILED', error: error.message }); renderState(); }
    }
    return store.getState();
  }

  const onResize = () => renderState();
  window.addEventListener('resize', onResize);
  await refresh(true);
  const poll = window.setInterval(() => refresh(false), 15000);
  return { store, refresh, changeUser: userId => { if(userId) currentUserId=String(userId); return refresh(true); }, destroy() { window.clearInterval(poll); window.removeEventListener('resize', onResize); ambient.destroy(); choreographer.destroy(); renderer.destroy(); timeline.destroy(); navigation.destroy(); focus.destroy(); menu.destroy(); abortController?.abort(); } };
}

function exportState(state) { const blob = new Blob([JSON.stringify(state, null, 2)], { type: 'application/json' }); const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = 'mnemagent-living-archive.json'; link.click(); URL.revokeObjectURL(link.href); }

if (typeof document !== 'undefined') bootstrapArchive().catch(error => { const status = document.querySelector('#archiveStatus'); if (status) status.textContent = `Archive failed to awaken: ${error.message}`; });
