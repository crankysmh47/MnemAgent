const HANGING_VINES = Object.freeze([
  { id: 'canopy-left-outer', duration: 10.5, delay: -3.2, response: 3.2, points: [[18,0],[28,72],[76,138],[58,226]], leaves: [{id:'lo-1',x:35,y:76,angle:28,scale:1.15},{id:'lo-2',x:62,y:142,angle:-34,scale:1.04},{id:'lo-3',x:57,y:201,angle:31,scale:.94}] },
  { id: 'canopy-left-inner', duration: 8.7, delay: -5.1, response: 2.6, points: [[118,0],[104,56],[128,112],[102,174]], leaves: [{id:'li-1',x:108,y:58,angle:-30,scale:1.04},{id:'li-2',x:119,y:111,angle:32,scale:.96},{id:'li-3',x:106,y:160,angle:-28,scale:.88}] },
  { id: 'canopy-right-inner', duration: 9.4, delay: -1.8, response: -2.6, points: [[882,0],[896,58],[870,112],[898,178]], leaves: [{id:'ri-1',x:892,y:61,angle:28,scale:1.04},{id:'ri-2',x:878,y:114,angle:-32,scale:.96},{id:'ri-3',x:894,y:163,angle:28,scale:.88}] },
  { id: 'canopy-right-outer', duration: 11.2, delay: -6.4, response: -3.2, points: [[982,0],[968,78],[924,145],[946,238]], leaves: [{id:'ro-1',x:963,y:80,angle:-28,scale:1.15},{id:'ro-2',x:935,y:148,angle:34,scale:1.04},{id:'ro-3',x:944,y:211,angle:-31,scale:.94}] },
]);

const GRASS_BLADES = Object.freeze(Array.from({ length: 24 }, (_, index) => ({
  id: `blade-${index}`,
  x: 135 + index * 32,
  y: 652 + (index % 3) * 3,
  height: 30 + (index * 11 % 34),
  lean: -10 + (index * 7 % 21),
})));

const MOSS_PATCHES = Object.freeze([
  { id: 'moss-left', x: 248, y: 653, rx: 96, ry: 19 },
  { id: 'moss-heart', x: 500, y: 657, rx: 148, ry: 23 },
  { id: 'moss-right', x: 760, y: 653, rx: 100, ry: 19 },
]);

function sceneBounds(tree = {}) {
  return { width: Math.max(320, Number(tree.bounds?.width) || 1000), height: Math.max(480, Number(tree.bounds?.height) || 720) };
}

function point(x, y, bounds) { return { x: x * bounds.width / 1000, y: y * bounds.height / 720 }; }

function curvePath(points, bounds) {
  const [start, control1, control2, end] = points.map(([x, y]) => point(x, y, bounds));
  return `M${start.x},${start.y} C${control1.x},${control1.y} ${control2.x},${control2.y} ${end.x},${end.y}`;
}

function grassBladePath(blade, bounds) {
  const base = point(blade.x, blade.y, bounds);
  const tip = point(blade.x + blade.lean, blade.y - blade.height, bounds);
  return `M${base.x},${base.y} Q${base.x + (tip.x - base.x) * .18},${base.y - (base.y - tip.y) * .55} ${tip.x},${tip.y}`;
}

function leafTransform(leaf, bounds) {
  const at = point(leaf.x, leaf.y, bounds);
  const scale = leaf.scale * Math.min(bounds.width / 1000, bounds.height / 720);
  return `translate(${at.x},${at.y}) rotate(${leaf.angle}) scale(${scale})`;
}

export function renderForestScene(world, tree = {}) {
  const bounds = sceneBounds(tree);
  const canopy = world.select('g.canopy');
  const vines = canopy.selectAll('g.hanging-vine').data(HANGING_VINES, d => d.id).join(
    enter => {
      const group = enter.append('g').attr('class', 'hanging-vine');
      group.append('path').attr('class', 'hanging-vine-hit');
      const motion = group.append('g').attr('class', 'hanging-vine-motion');
      const response = motion.append('g').attr('class', 'hanging-vine-response');
      response.append('path').attr('class', 'hanging-vine-stem');
      return group;
    },
    update => update,
    exit => exit.remove(),
  ).attr('data-vine-id', d => d.id).attr('aria-hidden', 'true')
    .style('--vine-duration', d => `${d.duration}s`).style('--vine-delay', d => `${d.delay}s`)
    .style('--vine-response-angle', d => `${d.response}deg`);
  vines.select('path.hanging-vine-hit').attr('d', d => curvePath(d.points, bounds)).attr('fill', 'none');
  const vineResponses = vines.select('g.hanging-vine-response');
  vineResponses.select('path.hanging-vine-stem').attr('d', d => curvePath(d.points, bounds)).attr('fill', 'none');
  vineResponses.selectAll('path.hanging-leaf').data(d => d.leaves, d => d.id).join('path')
    .attr('class', 'hanging-leaf').attr('d', 'M0,0 C5,-8 14,-8 16,0 C11,8 4,8 0,0Z')
    .attr('transform', d => leafTransform(d, bounds));

  const water = world.select('g.water');
  const waterPath = `M${point(82,662,bounds).x},${point(82,662,bounds).y} C${point(265,610,bounds).x},${point(265,610,bounds).y} ${point(730,610,bounds).x},${point(730,610,bounds).y} ${point(920,662,bounds).x},${point(920,662,bounds).y} C${point(748,700,bounds).x},${point(748,700,bounds).y} ${point(252,700,bounds).x},${point(252,700,bounds).y} ${point(82,662,bounds).x},${point(82,662,bounds).y}Z`;
  water.selectAll('path.forest-water').data([{ id:'reflecting-pool', d:waterPath }], d => d.id).join('path')
    .attr('class', 'forest-water').attr('d', d => d.d).attr('aria-hidden', 'true');
  const ripples = [
    { id:'ripple-left', d:`M${point(170,650,bounds).x},${point(170,650,bounds).y} Q${point(330,636,bounds).x},${point(330,636,bounds).y} ${point(470,650,bounds).x},${point(470,650,bounds).y}` },
    { id:'ripple-right', d:`M${point(530,665,bounds).x},${point(530,665,bounds).y} Q${point(680,650,bounds).x},${point(680,650,bounds).y} ${point(830,665,bounds).x},${point(830,665,bounds).y}` },
  ];
  water.selectAll('path.forest-ripple').data(ripples, d => d.id).join('path')
    .attr('class', 'forest-ripple').attr('d', d => d.d).attr('fill', 'none').attr('aria-hidden', 'true');

  const ground = world.select('g.groundcover');
  const bankPath = `M${point(72,667,bounds).x},${point(72,667,bounds).y} Q${point(245,612,bounds).x},${point(245,612,bounds).y} ${point(400,654,bounds).x},${point(400,654,bounds).y} Q${point(505,606,bounds).x},${point(505,606,bounds).y} ${point(620,652,bounds).x},${point(620,652,bounds).y} Q${point(790,616,bounds).x},${point(790,616,bounds).y} ${point(928,668,bounds).x},${point(928,668,bounds).y} L${point(928,720,bounds).x},${point(928,720,bounds).y} L${point(72,720,bounds).x},${point(72,720,bounds).y}Z`;
  ground.selectAll('path.grass-bank').data([{ id:'grass-bank', d:bankPath }], d => d.id).join('path')
    .attr('class', 'grass-bank').attr('d', d => d.d).attr('aria-hidden', 'true');
  ground.selectAll('path.grass-blade').data(GRASS_BLADES, d => d.id).join('path')
    .attr('class', 'grass-blade').attr('d', d => grassBladePath(d, bounds)).attr('fill', 'none').attr('aria-hidden', 'true');
  ground.selectAll('ellipse.forest-moss').data(MOSS_PATCHES, d => d.id).join('ellipse')
    .attr('class', 'forest-moss').attr('cx', d => point(d.x,d.y,bounds).x).attr('cy', d => point(d.x,d.y,bounds).y)
    .attr('rx', d => d.rx * bounds.width / 1000).attr('ry', d => d.ry * bounds.height / 720).attr('aria-hidden', 'true');
}
