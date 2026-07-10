const recallTypes = new Set(['injected', 'influenced']);

const eventType = event => event?.eventType || event?.event_type || '';

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

function clear(root) { while (root.firstChild) root.removeChild(root.firstChild); }

export function renderObservation(root, state = {}, narrative = {}) {
  if (!root) return;
  const narrativeRoot = root.querySelector('#narrativeCopy');
  if (narrativeRoot) {
    clear(narrativeRoot);
    const eyebrow = document.createElement('p'); eyebrow.className = 'observation-eyebrow'; eyebrow.textContent = narrative.eyebrow || 'Living observation';
    const title = document.createElement('h2'); title.textContent = narrative.title || 'A living record of what endures.';
    const body = document.createElement('p'); body.textContent = narrative.body || 'Memories settle into related branches as they become useful.';
    narrativeRoot.append(eyebrow, title, body);
  }
  const detail = root.querySelector('#memoryDetail');
  if (detail) {
    clear(detail);
    const memory = state.memories?.find(item => String(item.id) === String(state.selectedMemoryId));
    const heading = document.createElement('h3'); heading.textContent = memory ? memory.statement : 'Select a memory to observe it'; detail.append(heading);
    if (memory) {
      const meta = document.createElement('p'); meta.className = 'memory-detail-meta'; meta.textContent = `${memory.category} · ${memory.lifecycle} · ${Math.round((memory.confidence || 0) * 100)}% confidence`; detail.append(meta);
    }
  }
  const vitalRoot = root.querySelector('#vitalSigns');
  if (vitalRoot) {
    clear(vitalRoot);
    for (const [label, value] of Object.entries(deriveVitalSigns(state))) {
      const term = document.createElement('dt'); term.textContent = label;
      const definition = document.createElement('dd'); definition.textContent = String(value);
      vitalRoot.append(term, definition);
    }
  }
}

export function renderCompanionList(root, memories = [], selectedId = null) {
  if (!root) return;
  clear(root);
  for (const memory of memories) {
    const item = document.createElement('li');
    const button = document.createElement('button'); button.type = 'button'; button.dataset.memoryId = String(memory.id); button.textContent = memory.statement || String(memory.id); button.setAttribute('aria-pressed', String(String(memory.id) === String(selectedId)));
    item.append(button); root.append(item);
  }
}
