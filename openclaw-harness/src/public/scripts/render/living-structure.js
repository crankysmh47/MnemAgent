import { memoryAriaLabel, memoryFormPath, shapeClass } from './memory-form.js';
import { tendrilClass, tendrilStrokeWidth } from './tendril.js';

const CATEGORY_COLOR = Object.freeze({ preference: 'var(--living-moss)', persona: 'var(--clay-rose)', system_state: 'var(--mineral-blue)' });

function d3Global() {
  if (!globalThis.d3) throw new Error('D3 must be loaded before the Living Archive renderer');
  return globalThis.d3;
}

export function createLivingStructure(svgElement, { onSelect = () => {}, onTrace = () => {} } = {}) {
  const d3 = d3Global();
  const svg = d3.select(svgElement);
  const world = svg.select('#archiveWorld');
  const layers = ['skeleton', 'membranes', 'tendrils', 'memories', 'effects', 'annotations'];
  for (const name of layers) if (world.select(`g.${name}`).empty()) world.append('g').attr('class', name);

  function render(snapshot = {}, layout = { nodes: [], paths: [] }, viewState = {}) {
    const memories = Array.isArray(snapshot.memories) ? snapshot.memories : [];
    const relationships = Array.isArray(layout.paths) ? layout.paths : [];
    const nodeById = new Map(layout.nodes.map(node => [String(node.id), node]));
    const selectedId = viewState.selectedMemoryId == null ? null : String(viewState.selectedMemoryId);
    const related = new Set((viewState.relatedMemoryIds || []).map(String));

    const tendrilLayer = world.select('g.tendrils');
    tendrilLayer.selectAll('path.tendril').data(relationships, d => d.id).join(
      enter => enter.append('path'),
      update => update,
      exit => exit.remove(),
    ).attr('class', d => tendrilClass(d, related.has(String(d.source)) || related.has(String(d.target)) ? 'active' : 'quiet'))
      .attr('d', d => d.d)
      .attr('stroke-width', d => tendrilStrokeWidth(d.weight))
      .attr('fill', 'none')
      .attr('aria-hidden', 'true');

    const memoryLayer = world.select('g.memories');
    memoryLayer.selectAll('g.memory-form').data(memories, d => String(d.id)).join(
      enter => {
        const group = enter.append('g').attr('class', d => shapeClass(d.shape));
        group.append('path').attr('class', 'memory-body');
        group.append('circle').attr('class', 'memory-focus-ring').attr('r', d => d.radius + 5);
        return group;
      },
      update => update,
      exit => exit.remove(),
    ).attr('transform', d => {
      const node = nodeById.get(String(d.id));
      return node ? `translate(${node.x},${node.y})` : null;
    }).attr('class', d => `${shapeClass(d.shape)}${String(d.id) === selectedId ? ' is-selected' : ''}${related.has(String(d.id)) ? ' is-related' : ''}${d.collapsed ? ' is-quiet' : ''}`)
      .attr('role', 'button')
      .attr('tabindex', 0)
      .attr('aria-label', d => memoryAriaLabel(d))
      .on('click', (_event, d) => onSelect(d.id))
      .on('dblclick', (_event, d) => onTrace(d.id))
      .on('keydown', (event, d) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); onSelect(d.id); } });

    memoryLayer.selectAll('g.memory-form').select('path.memory-body')
      .attr('d', d => memoryFormPath(d.shape, d.radius))
      .attr('fill', d => CATEGORY_COLOR[d.category] || 'var(--weathered-taupe)')
      .attr('stroke', 'var(--antique-brass)')
      .attr('stroke-width', d => d.lifecycle === 'fading' ? 0.8 : 1.4)
      .attr('opacity', d => d.lifecycle === 'dormant' ? 0.38 : 0.95);
    memoryLayer.selectAll('g.memory-form').select('circle.memory-focus-ring')
      .attr('fill', 'none').attr('stroke', 'var(--bone-white)').attr('opacity', 0);
    world.select('g.skeleton').selectAll('*').remove();
    world.select('g.skeleton').append('path').attr('class', 'root-crown').attr('d', 'M430,620 C390,570 350,520 330,450 M430,620 C430,550 430,480 430,390 M430,620 C470,565 520,520 575,455').attr('fill', 'none').attr('stroke', 'var(--antique-brass)').attr('stroke-width', 2);
  }

  return { render, setInteractive(enabled) { svg.attr('data-interactive', Boolean(enabled)); }, destroy() { world.selectAll('*').remove(); } };
}
