import { memoryAriaLabel, memoryFormPath, memoryVeinPath, shapeClass } from './memory-form.js';
import { renderForestScene } from './forest-scene.js';
import { relationshipFocusState, tendrilClass, tendrilStrokeWidth } from './tendril.js';
import { curvePath } from '../tree-geometry.js';
import { memoryLabelPosition, shortMemoryStatement } from './memory-label.js';

const CATEGORY_COLOR = Object.freeze({ preference: 'var(--living-moss)', persona: 'var(--clay-rose)', system_state: 'var(--mineral-blue)' });

function d3Global() {
  if (!globalThis.d3) throw new Error('D3 must be loaded before the Living Archive renderer');
  return globalThis.d3;
}

export function createLivingStructure(svgElement, { onSelect = () => {}, onTrace = () => {}, onHover = () => {} } = {}) {
  const d3 = d3Global();
  const svg = d3.select(svgElement);
  const world = svg.select('#archiveWorld');
  const layers = ['canopy', 'water', 'groundcover', 'roots', 'trunk', 'branches', 'tendrils', 'memories', 'effects', 'annotations'];
  for (const name of layers) if (world.select(`g.${name}`).empty()) world.append('g').attr('class', name);

  function render(snapshot = {}, layout = { nodes: [], paths: [] }, viewState = {}) {
    const memories = Array.isArray(snapshot.memories) ? snapshot.memories : [];
    const relationships = Array.isArray(layout.paths) ? layout.paths : [];
    const nodeById = new Map(layout.nodes.map(node => [String(node.id), node]));
    const selectedId = viewState.selectedMemoryId == null ? null : String(viewState.selectedMemoryId);
    const related = new Set((viewState.relatedMemoryIds || []).map(String));
    const annotationLayer = world.select('g.annotations');
    const clearLabel = () => annotationLayer.selectAll('g.memory-hover-label').remove();
    const showLabel = memory => {
      const node=nodeById.get(String(memory.id)); if(!node) return;
      const text=shortMemoryStatement(memory), labelWidth=Math.min(250,Math.max(112,text.length*6.5+24)), labelHeight=38;
      const at=memoryLabelPosition(node,layout.bounds||{width:1000,height:720},{width:labelWidth,height:labelHeight});
      const x=at.anchor==='start'?0:at.anchor==='end'?-labelWidth:-labelWidth/2;
      const label=annotationLayer.selectAll('g.memory-hover-label').data([{...at,text,labelWidth,labelHeight}],()=> 'active').join(enter=>{const g=enter.append('g').attr('class','memory-hover-label').attr('aria-hidden','true');g.append('rect');g.append('text');return g;});
      label.attr('transform',d=>`translate(${d.x},${d.y})`); label.select('rect').attr('x',x).attr('y',0).attr('width',labelWidth).attr('height',labelHeight).attr('rx',10); label.select('text').attr('x',x+12).attr('y',24).text(text);
    };
    svg.classed('has-memory-focus', Boolean(selectedId));

    const tree = layout.tree || { root: { paths: [] }, trunk: null, branches: [] };
    renderForestScene(world, tree);
    world.select('g.roots').selectAll('path.root-line').data(tree.root?.paths || [], d => d.id).join('path')
      .attr('class', 'root-line').attr('d', curvePath).attr('aria-hidden', 'true');
    world.select('g.trunk').selectAll('path.trunk-line').data(tree.trunk ? [tree.trunk] : [], d => d.id).join('path')
      .attr('class', 'trunk-line').attr('d', curvePath).attr('aria-hidden', 'true');
    world.select('g.branches').selectAll('path.branch').data(tree.branches || [], d => d.id).join('path')
      .attr('class', d => `branch branch-${d.category} branch-level-${d.level || 1}`)
      .attr('data-branch-id', d => d.id).attr('d', curvePath).attr('aria-hidden', 'true');

    const tendrilLayer = world.select('g.tendrils');
    tendrilLayer.selectAll('path.tendril').data(relationships, d => d.id).join(
      enter => enter.append('path'),
      update => update,
      exit => exit.remove(),
    ).attr('class', d => tendrilClass(d, relationshipFocusState(d, selectedId)))
      .attr('d', d => d.d)
      .attr('stroke-width', d => tendrilStrokeWidth(d.weight))
      .attr('fill', 'none')
      .attr('aria-hidden', 'true');

    const memoryLayer = world.select('g.memories');
    memoryLayer.selectAll('g.memory-form').data(memories, d => String(d.id)).join(
      enter => {
        const group = enter.append('g').attr('class', d => shapeClass(d.shape));
        group.append('circle').attr('class', 'memory-hit-area').attr('r', 22);
        const interaction = group.append('g').attr('class', 'memory-interaction');
        interaction.append('path').attr('class', 'memory-body');
        interaction.append('path').attr('class', 'memory-vein');
        interaction.append('circle').attr('class', 'memory-focus-ring').attr('r', d => (nodeById.get(String(d.id))?.radius || 10) + 5);
        return group;
      },
      update => update,
      exit => exit.remove(),
    ).attr('transform', d => {
      const node = nodeById.get(String(d.id));
      return node ? `translate(${node.x},${node.y})` : null;
    }).attr('class', d => {
      const id = String(d.id);
      const quiet = Boolean(selectedId) && id !== selectedId && !related.has(id);
      return `${shapeClass(d.shape)}${id === selectedId ? ' is-selected' : ''}${related.has(id) ? ' is-related' : ''}${quiet ? ' is-quiet' : ''}`;
    })
      .attr('role', 'button')
      .attr('tabindex', 0)
      .attr('aria-label', d => memoryAriaLabel(d))
      .on('click', (_event, d) => onSelect(d.id))
      .on('dblclick', (_event, d) => onTrace(d.id))
      .on('mouseenter', (_event, d) => { showLabel(d); onHover(d.id); })
      .on('mouseleave', () => { clearLabel(); onHover(null); })
      .on('focus', (_event, d) => { showLabel(d); onHover(d.id); })
      .on('blur', () => { clearLabel(); onHover(null); })
      .on('keydown', (event, d) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); onSelect(d.id); } });

    const forms = memoryLayer.selectAll('g.memory-form');
    forms.select('g.memory-interaction').style('--memory-index', (_d, index) => index % 56).style('--memory-angle', d => {
      const angle = nodeById.get(String(d.id))?.angle || 0;
      return `${d.shape === 'leaf' ? angle - 90 : angle * .08}deg`;
    });
    forms.select('circle.memory-hit-area').attr('r', d => Math.max(22, (nodeById.get(String(d.id))?.radius || 10) + 5));
    forms.select('path.memory-body')
      .attr('d', d => memoryFormPath(d.shape, nodeById.get(String(d.id))?.radius))
      .attr('fill', d => CATEGORY_COLOR[d.category] || 'var(--weathered-taupe)')
      .attr('stroke', 'var(--antique-brass)')
      .attr('stroke-width', d => d.lifecycle === 'fading' ? 0.8 : 1.4)
      .attr('opacity', d => d.lifecycle === 'dormant' ? 0.38 : 0.95);
    forms.select('path.memory-vein')
      .attr('d', d => memoryVeinPath(d.shape, nodeById.get(String(d.id))?.radius))
      .attr('fill', 'none').attr('aria-hidden', 'true');
    forms.select('circle.memory-focus-ring')
      .attr('r', d => (nodeById.get(String(d.id))?.radius || 10) + 5)
      .attr('fill', 'none').attr('stroke', 'var(--bone-white)').attr('opacity', 0);
  }

  return { render, setInteractive(enabled) { svg.attr('data-interactive', Boolean(enabled)); }, destroy() { world.selectAll('*').remove(); } };
}
