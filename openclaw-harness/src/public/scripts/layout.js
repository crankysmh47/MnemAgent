import { normalizeCategory } from './memory-model.js';
import { createTreeSkeleton, cubicPoint } from './tree-geometry.js';

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

const CATEGORIES = ['preference', 'persona', 'system_state'];
export function computeArchiveLayout(memories = [], relationships = [], { width = 1000, height = 720, selectedMemoryId = null } = {}) {
  const marginX = width * .06, marginY = height * .06;
  const tree = createTreeSkeleton({ width, height });
  const withIds = (Array.isArray(memories) ? memories : []).map(m => ({ ...m, id: String(m.id || `memory-${hashString(`${m.category}|${m.source || m.entity_source}|${m.relation}|${m.target || m.entity_target}`)}`) }));
  const sorted = withIds.slice().sort((a,b) => String(a.id).localeCompare(String(b.id)));
  const collapsedSet = sorted.length > 80 ? new Set(sorted.filter(m => String(m.id) !== String(selectedMemoryId) && Number(m.vitality ?? m.node_weight) < .45).slice(20).map(m => String(m.id))) : new Set();
  const nodes = [];
  for (const category of CATEGORIES) {
    const members = sorted.filter(memory => normalizeCategory(memory.category) === category);
    const branches = tree.branches.filter(branch => branch.category === category);
    members.forEach((memory, index) => {
      const id = String(memory.id), vitality = Math.max(0, Math.min(1, Number(memory.vitality ?? memory.node_weight) || 0));
      const branchIndex = index % branches.length, branch = branches[branchIndex];
      const branchSlot = Math.floor(index / branches.length);
      const branchCount = Math.ceil((members.length - branchIndex) / branches.length);
      const ratio = branchCount <= 1 ? .62 : branchSlot / (branchCount - 1);
      const random = seededRandom(id), branchT = Math.max(.22, Math.min(.96, .25 + ratio * .69 + (random() - .5) * .025));
      const position = cubicPoint(branch, branchT);
      const nearby = cubicPoint(branch, Math.min(1, branchT + .012));
      const dx = nearby.x - position.x, dy = nearby.y - position.y, magnitude = Math.hypot(dx, dy) || 1;
      const offset = (random() - .5) * 22;
      const x = position.x + (-dy / magnitude) * offset, y = position.y + (dx / magnitude) * offset;
      nodes.push({ ...memory, id, category, grove: category, x, y, vitality, radius: 14 + vitality * 10, branchId: branch.id, branchT, angle: Math.atan2(dy, dx) * 180 / Math.PI, collapsed: collapsedSet.has(id) });
    });
  }
  nodes.sort((a,b) => String(a.id).localeCompare(String(b.id)));
  const clampNode = node => {
    const inset = .01;
    node.x = Math.max(marginX + node.radius + inset, Math.min(width - marginX - node.radius - inset, node.x));
    node.y = Math.max(marginY + node.radius + inset, Math.min(height - marginY - node.radius - inset, node.y));
  };
  nodes.forEach(clampNode);
  for (let it=0; it<12; it++) {
    for (let i=0;i<nodes.length;i++) for (let j=i+1;j<nodes.length;j++) {
      const a=nodes[i],b=nodes[j], dx=b.x-a.x,dy=b.y-a.y,d=Math.hypot(dx,dy)||1,min=a.radius+b.radius+5;
      if(d<min){ const q=(min-d)/d*.28; a.x-=dx*q; a.y-=dy*q; b.x+=dx*q; b.y+=dy*q; clampNode(a); clampNode(b); }
    }
  }
  const byId = new Map(nodes.map(n => [n.id,n]));
  const paths = (Array.isArray(relationships)?relationships:[]).slice().sort((a,b) => `${a.source}:${a.target}`.localeCompare(`${b.source}:${b.target}`)).map((r,i) => { const s=byId.get(String(r.source)), t=byId.get(String(r.target)); return s&&t ? { id: `${s.id}-${t.id}-${i}`, source:s.id, target:t.id, kind:r.kind, weight:r.weight, d:relationshipPath(s,t) } : null; }).filter(Boolean);
  const groves = CATEGORIES.map(category => { const members=nodes.filter(n=>n.category===category), hidden=members.filter(n=>n.collapsed); const centroid = hidden.length ? { x:hidden.reduce((s,n)=>s+n.x,0)/hidden.length, y:hidden.reduce((s,n)=>s+n.y,0)/hidden.length } : null; return { category, members: members.filter(n=>!n.collapsed).map(n=>n.id), collapsed: hidden.length > 0, count: members.length, aggregate: hidden.length ? { centroid, representative: hidden[0].id, memberIds: hidden.map(n=>n.id), count: hidden.length } : null }; });
  return { nodes, paths, groves, bounds: { width, height, marginX, marginY }, center: tree.root, tree };
}
