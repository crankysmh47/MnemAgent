const recallTypes = new Set(['injected', 'influenced']);

export const MATERIAL_LEGEND = Object.freeze([
  { key: 'leaf', label: 'Preference', description: 'A learned preference or recurring choice.' },
  { key: 'pearl', label: 'Persona', description: 'A trait that shapes how the agent understands you.' },
  { key: 'mineral', label: 'System state', description: 'A durable fact about work, tools, or context.' },
  { key: 'scar', label: 'Revision', description: 'A belief changed by newer evidence.' },
  { key: 'husk', label: 'Fading', description: 'A memory becoming quieter through disuse.' },
]);

const eventType = event => event?.eventType || event?.event_type || event?.type || '';

export function deriveVitalSigns(state = {}) {
  const memories = Array.isArray(state.memories) ? state.memories.filter(memory => memory.visible !== false).length : 0;
  const relationships = Array.isArray(state.relationships) ? state.relationships.length : 0;
  const seen = new Set();
  const recalls = (Array.isArray(state.events) ? state.events : []).filter(event => {
    const id = String(event?.id ?? `${event?.timestamp || ''}:${eventType(event)}`);
    if (seen.has(id) || !recallTypes.has(eventType(event))) return false;
    seen.add(id);
    return true;
  }).length;
  return { memories, relationships, recalls };
}

export function eventGlyph(event = {}) {
  return ({ new_belief: 'seed', injected: 'pulse', influenced: 'pulse', contradiction: 'scar', decayed: 'husk', pruned: 'husk' })[eventType(event)] || 'settled';
}

export function renderMaterialLegend(root) {
  if (!root) return;
  clear(root);
  const heading = document.createElement('h3'); heading.textContent = 'How to read the archive'; root.append(heading);
  const list = document.createElement('ul'); list.className = 'material-legend-list';
  for (const item of MATERIAL_LEGEND) { const row=document.createElement('li'); const mark=document.createElement('span'); mark.className=`material-mark material-${item.key}`; mark.setAttribute('aria-hidden','true'); const copy=document.createElement('span'); const label=document.createElement('strong'); label.textContent=item.label; const description=document.createElement('small'); description.textContent=item.description; copy.append(label,description); row.append(mark,copy); list.append(row); }
  root.append(list);
}

function clear(root) { while (root.firstChild) root.removeChild(root.firstChild); }

function observationRegion(root, id, role, tag = 'section') { const existing=root.querySelector(`#${id}, [data-observation-role="${role}"]`); if(existing) return existing; const region=document.createElement(tag); region.dataset.observationRole=role; if(role==='detail') region.setAttribute('aria-label','Selected memory'); if(role==='vitals') region.setAttribute('aria-label','Archive vital signs'); root.append(region); return region; }

export function renderObservation(root, state = {}, narrative = {}) {
  if (!root) return;
  const narrativeRoot = observationRegion(root,'narrativeCopy','narrative');
  if (narrativeRoot) {
    clear(narrativeRoot);
    const eyebrow = document.createElement('p'); eyebrow.className = 'observation-eyebrow'; eyebrow.textContent = narrative.eyebrow || 'Living observation';
    const title = document.createElement('h2'); title.textContent = narrative.title || 'A living record of what endures.';
    const body = document.createElement('p'); body.textContent = narrative.body || 'Memories settle into related branches as they become useful.';
    narrativeRoot.append(eyebrow, title, body);
    if(narrative.guidance){ const guidance=document.createElement('p'); guidance.className='observation-guidance'; guidance.textContent=narrative.guidance; narrativeRoot.append(guidance); }
  }
  const detail = observationRegion(root,'memoryDetail','detail');
  if (detail) {
    clear(detail);
    const memory = state.memories?.find(item => String(item.id) === String(state.selectedMemoryId));
    const heading = document.createElement('h3'); heading.textContent = memory ? memory.statement : 'Select a memory to observe it'; detail.append(heading);
    if (memory) {
      const meta = document.createElement('p'); meta.className = 'memory-detail-meta'; meta.textContent = `${memory.category} · ${memory.lifecycle} · ${Math.round((memory.confidence || 0) * 100)}% confidence`; detail.append(meta);
    }
  }
  const vitalRoot = observationRegion(root,'vitalSigns','vitals','dl');
  if (vitalRoot) {
    clear(vitalRoot);
    for (const [label, value] of Object.entries(deriveVitalSigns(state))) {
      const term = document.createElement('dt'); term.textContent = label;
      const definition = document.createElement('dd'); definition.textContent = String(value);
      vitalRoot.append(term, definition);
    }
  }
}

export function renderCompanionList(root, memories = [], selectedId = null, onSelect = () => {}) {
  if (!root) return;
  clear(root);
  for (const memory of memories) {
    const item = document.createElement('li');
    const button = document.createElement('button'); button.type = 'button'; button.dataset.memoryId = String(memory.id); button.textContent = memory.statement || String(memory.id); button.setAttribute('aria-pressed', String(String(memory.id) === String(selectedId))); button.addEventListener('click',()=>onSelect(memory.id));
    item.append(button); root.append(item);
  }
}
