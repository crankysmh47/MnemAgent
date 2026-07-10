import { normalizeCategory } from './memory-model.js';

export function hashString(value = '') {
  let h = 2166136261;
  for (const c of String(value)) { h ^= c.charCodeAt(0); h = Math.imul(h, 16777619); }
  return h >>> 0;
}
export function seededRandom(seed = 0) {
  let s = hashString(seed) || 1;
  return () => { s = Math.imul(1664525, s) + 1013904223 >>> 0; return s / 4294967296; };
}
export function relationshipPath(source, target, bend = 0.18) {
  const dx = target.x - source.x, dy = target.y - source.y, nx = -dy * bend, ny = dx * bend;
  const c1x = source.x + dx * 0.35 + nx, c1y = source.y + dy * 0.35 + ny;
  const c2x = source.x + dx * 0.65 + nx, c2y = source.y + dy * 0.65 + ny;
  return `M${source.x},${source.y} C${c1x},${c1y} ${c2x},${c2y} ${target.x},${target.y}`;
}

const ANGLES = { preference: -145, persona: -90, system_state: -35 };
const rad = d => d * Math.PI / 180;
export function computeArchiveLayout(memories = [], relationships = [], { width = 1000, height = 720, selectedMemoryId = null } = {}) {
  const sx = width / 1000, sy = height / 720, marginX = width * .06, marginY = height * .08;
  const root = { x: 430 * sx, y: 620 * sy };
  const withIds = (Array.isArray(memories) ? memories : []).map(m => ({ ...m, id: String(m.id || `memory-${hashString(`${m.category}|${m.source || m.entity_source}|${m.relation}|${m.target || m.entity_target}`)}`) }));
  const sorted = withIds.slice().sort((a,b) => String(a.id).localeCompare(String(b.id)));
  const collapsedSet = sorted.length > 80 ? new Set(sorted.filter(m => String(m.id) !== String(selectedMemoryId) && Number(m.vitality ?? m.node_weight) < .45).slice(20).map(m => String(m.id))) : new Set();
  const nodes = sorted.map((m, i) => {
    const id = String(m.id ?? `memory-${i}`), category = normalizeCategory(m.category), vitality = Math.max(0, Math.min(1, Number(m.vitality ?? m.node_weight) || 0));
    const r = seededRandom(id), angle = rad(ANGLES[category] + (r() - .5) * 24), radius = 120 + (1 - vitality) * 220 + r() * 65;
    const x = root.x + Math.cos(angle) * radius * sx, y = root.y + Math.sin(angle) * radius * sy;
    return { id, category, grove: category, x: Math.max(marginX, Math.min(width-marginX, x)), y: Math.max(marginY, Math.min(height-marginY, y)), vitality, radius: 10 + vitality * 8, collapsed: collapsedSet.has(id) };
  });
  for (let it=0; it<32; it++) for (let i=0;i<nodes.length;i++) for (let j=i+1;j<nodes.length;j++) { const a=nodes[i],b=nodes[j], dx=b.x-a.x,dy=b.y-a.y,d=Math.hypot(dx,dy)||1,min=a.radius+b.radius+5; if(d<min){const q=(min-d)/d*.5; a.x=Math.max(marginX, a.x-dx*q); a.y=Math.max(marginY,a.y-dy*q); b.x=Math.min(width-marginX,b.x+dx*q); b.y=Math.min(height-marginY,b.y+dy*q);} }
  const byId = new Map(nodes.map(n => [n.id,n]));
  const paths = (Array.isArray(relationships)?relationships:[]).slice().sort((a,b) => `${a.source}:${a.target}`.localeCompare(`${b.source}:${b.target}`)).map((r,i) => { const s=byId.get(String(r.source)), t=byId.get(String(r.target)); return s&&t ? { id: `${s.id}-${t.id}-${i}`, source:s.id, target:t.id, d:relationshipPath(s,t) } : null; }).filter(Boolean);
  const groves = Object.keys(ANGLES).map(category => { const members=nodes.filter(n=>n.category===category), hidden=members.filter(n=>n.collapsed), all=members.map(n=>n.id); const centroid = hidden.length ? { x:hidden.reduce((s,n)=>s+n.x,0)/hidden.length, y:hidden.reduce((s,n)=>s+n.y,0)/hidden.length } : null; return { category, members: members.filter(n=>!n.collapsed).map(n=>n.id), collapsed: hidden.length > 0, count: members.length, aggregate: hidden.length ? { centroid, representative: hidden[0].id, memberIds: hidden.map(n=>n.id), count: hidden.length } : null }; });
  return { nodes, paths, groves, bounds: { width, height, marginX, marginY }, center: root };
}
