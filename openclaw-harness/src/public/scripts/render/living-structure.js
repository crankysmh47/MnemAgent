import { memoryAriaLabel, memoryFormPath, memoryVeinPath, shapeClass } from './memory-form.js';
import { tendrilClass, tendrilStrokeWidth } from './tendril.js';
import { curvePath } from '../tree-geometry.js';

const CATEGORY_COLOR = Object.freeze({ preference: 'var(--living-moss)', persona: 'var(--clay-rose)', system_state: 'var(--mineral-blue)' });
const GROUND_GRASS = Object.freeze([
  { id: 'grass-west', x: 250, y: 653, spread: 27, height: 42, lean: -12 },
  { id: 'grass-left', x: 348, y: 649, spread: 23, height: 36, lean: 10 },
  { id: 'grass-heart-left', x: 438, y: 657, spread: 25, height: 48, lean: -7 },
  { id: 'grass-heart-right', x: 548, y: 654, spread: 26, height: 45, lean: 8 },
  { id: 'grass-east', x: 650, y: 652, spread: 24, height: 38, lean: 11 },
  { id: 'grass-far-east', x: 755, y: 657, spread: 28, height: 43, lean: -10 },
]);
const GROUND_MOSS = Object.freeze([
  { id: 'moss-west', x: 214, y: 668, rx: 78, ry: 12 },
  { id: 'moss-heart', x: 492, y: 668, rx: 122, ry: 15 },
  { id: 'moss-east', x: 800, y: 670, rx: 88, ry: 13 },
]);
const SEED_HEADS = Object.freeze([
  { id: 'seed-west', x: 285, y: 610, r: 3 },
  { id: 'seed-heart-left', x: 414, y: 602, r: 3.5 },
  { id: 'seed-heart-right', x: 574, y: 610, r: 3 },
  { id: 'seed-east', x: 716, y: 614, r: 3 },
]);
const GARDEN_VINES = Object.freeze([
  { id: 'vine-left', points: [[468, 660], [430, 560], [470, 455], [414, 334]] },
  { id: 'vine-center', points: [[510, 650], [550, 535], [475, 420], [530, 274]] },
  { id: 'vine-right', points: [[542, 642], [600, 555], [552, 470], [632, 388]] },
]);
const VINE_LEAVES = Object.freeze([
  { id: 'leaf-left-low', x: 447, y: 525, angle: -36, scale: .75 },
  { id: 'leaf-left-high', x: 437, y: 405, angle: 28, scale: .7 },
  { id: 'leaf-center-low', x: 515, y: 510, angle: 32, scale: .78 },
  { id: 'leaf-center-high', x: 508, y: 360, angle: -34, scale: .68 },
  { id: 'leaf-right-low', x: 576, y: 536, angle: 37, scale: .74 },
  { id: 'leaf-right-high', x: 592, y: 442, angle: -28, scale: .66 },
]);

function gardenBounds(tree = {}) {
  return { width: Math.max(320, Number(tree.bounds?.width) || 1000), height: Math.max(480, Number(tree.bounds?.height) || 720) };
}

function gardenPoint(x, y, bounds) { return { x: x * bounds.width / 1000, y: y * bounds.height / 720 }; }

function grassPath(grass, bounds) {
  const base = gardenPoint(grass.x, grass.y, bounds);
  const sx = bounds.width / 1000;
  const sy = bounds.height / 720;
  const spread = grass.spread * sx;
  const height = grass.height * sy;
  const lean = grass.lean * sx;
  return `M${base.x - spread},${base.y} Q${base.x - spread * .35},${base.y - height * .52} ${base.x + lean},${base.y - height} M${base.x},${base.y} Q${base.x + lean * .25},${base.y - height * .62} ${base.x + lean * .55},${base.y - height * .86} M${base.x + spread},${base.y} Q${base.x + spread * .32},${base.y - height * .48} ${base.x + lean * .82},${base.y - height * .72}`;
}

function gardenCurvePath(vine, bounds) {
  const [start, control1, control2, end] = vine.points.map(([x, y]) => gardenPoint(x, y, bounds));
  return `M${start.x},${start.y} C${control1.x},${control1.y} ${control2.x},${control2.y} ${end.x},${end.y}`;
}

function leafTransform(leaf, bounds) {
  const point = gardenPoint(leaf.x, leaf.y, bounds);
  return `translate(${point.x},${point.y}) rotate(${leaf.angle}) scale(${leaf.scale})`;
}

function renderGarden(world, tree) {
  const bounds = gardenBounds(tree);
  const ground = world.select('g.groundcover');
  ground.selectAll('path.ground-grass').data(GROUND_GRASS, d => d.id).join('path')
    .attr('class', 'ground-grass').attr('d', d => grassPath(d, bounds)).attr('fill', 'none').attr('aria-hidden', 'true');
  ground.selectAll('ellipse.ground-moss').data(GROUND_MOSS, d => d.id).join('ellipse')
    .attr('class', 'ground-moss').attr('cx', d => gardenPoint(d.x, d.y, bounds).x).attr('cy', d => gardenPoint(d.x, d.y, bounds).y)
    .attr('rx', d => d.rx * bounds.width / 1000).attr('ry', d => d.ry * bounds.height / 720).attr('aria-hidden', 'true');
  ground.selectAll('circle.seed-head').data(SEED_HEADS, d => d.id).join('circle')
    .attr('class', 'seed-head').attr('cx', d => gardenPoint(d.x, d.y, bounds).x).attr('cy', d => gardenPoint(d.x, d.y, bounds).y)
    .attr('r', d => d.r * bounds.width / 1000).attr('aria-hidden', 'true');

  const vines = world.select('g.vines');
  vines.selectAll('path.garden-vine').data(GARDEN_VINES, d => d.id).join('path')
    .attr('class', 'garden-vine').attr('d', d => gardenCurvePath(d, bounds)).attr('fill', 'none').attr('aria-hidden', 'true');
  vines.selectAll('path.vine-leaf').data(VINE_LEAVES, d => d.id).join('path')
    .attr('class', 'vine-leaf').attr('d', 'M0,0 C5,-7 13,-7 15,0 C10,7 4,7 0,0Z').attr('transform', d => leafTransform(d, bounds)).attr('aria-hidden', 'true');
}

function d3Global() {
  if (!globalThis.d3) throw new Error('D3 must be loaded before the Living Archive renderer');
  return globalThis.d3;
}

export function createLivingStructure(svgElement, { onSelect = () => {}, onTrace = () => {} } = {}) {
  const d3 = d3Global();
  const svg = d3.select(svgElement);
  const world = svg.select('#archiveWorld');
  const layers = ['groundcover', 'roots', 'trunk', 'branches', 'vines', 'tendrils', 'memories', 'effects', 'annotations'];
  for (const name of layers) if (world.select(`g.${name}`).empty()) world.append('g').attr('class', name);

  function render(snapshot = {}, layout = { nodes: [], paths: [] }, viewState = {}) {
    const memories = Array.isArray(snapshot.memories) ? snapshot.memories : [];
    const relationships = Array.isArray(layout.paths) ? layout.paths : [];
    const nodeById = new Map(layout.nodes.map(node => [String(node.id), node]));
    const selectedId = viewState.selectedMemoryId == null ? null : String(viewState.selectedMemoryId);
    const related = new Set((viewState.relatedMemoryIds || []).map(String));

    const tree = layout.tree || { root: { paths: [] }, trunk: null, branches: [] };
    renderGarden(world, tree);
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
    ).attr('class', d => tendrilClass(d, related.has(String(d.source)) || related.has(String(d.target)) ? 'active' : 'quiet'))
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
      .on('keydown', (event, d) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); onSelect(d.id); } });

    const forms = memoryLayer.selectAll('g.memory-form');
    forms.select('g.memory-interaction').style('--memory-angle', d => {
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
