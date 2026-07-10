const point = (x, y, sx, sy) => ({ x: x * sx, y: y * sy });

function curve(id, category, values, sx, sy, level = 1) {
  const [start, control1, control2, end] = values;
  return {
    id,
    category,
    level,
    start: point(start[0], start[1], sx, sy),
    control1: point(control1[0], control1[1], sx, sy),
    control2: point(control2[0], control2[1], sx, sy),
    end: point(end[0], end[1], sx, sy),
  };
}

export function cubicPoint(curveValue, tValue) {
  const t = Math.max(0, Math.min(1, Number(tValue) || 0));
  const u = 1 - t;
  return {
    x: u*u*u*curveValue.start.x + 3*u*u*t*curveValue.control1.x + 3*u*t*t*curveValue.control2.x + t*t*t*curveValue.end.x,
    y: u*u*u*curveValue.start.y + 3*u*u*t*curveValue.control1.y + 3*u*t*t*curveValue.control2.y + t*t*t*curveValue.end.y,
  };
}

export function curvePath(curveValue) {
  const { start, control1, control2, end } = curveValue;
  return `M${start.x},${start.y} C${control1.x},${control1.y} ${control2.x},${control2.y} ${end.x},${end.y}`;
}

export function createTreeSkeleton({ width = 1000, height = 720 } = {}) {
  const safeWidth = Math.max(320, Number(width) || 1000);
  const safeHeight = Math.max(480, Number(height) || 720);
  const sx = safeWidth / 1000;
  const sy = safeHeight / 720;
  const root = { x: 500 * sx, y: 650 * sy };
  const crown = { x: 500 * sx, y: 82 * sy };
  const trunk = curve('trunk', 'trunk', [[500,650],[470,535],[535,400],[500,245]], sx, sy, 0);
  const roots = [
    curve('root-left-far','root',[[500,650],[410,635],[255,670],[100,690]],sx,sy,0),
    curve('root-left','root',[[500,650],[440,625],[355,620],[275,680]],sx,sy,0),
    curve('root-center','root',[[500,650],[505,665],[505,685],[500,710]],sx,sy,0),
    curve('root-right','root',[[500,650],[565,625],[660,625],[745,682]],sx,sy,0),
    curve('root-right-far','root',[[500,650],[600,635],[760,665],[910,692]],sx,sy,0),
  ];
  const specs = [
    ['preference-0','preference',[[492,520],[395,470],[250,420],[135,330]],1],
    ['preference-1','preference',[[495,445],[390,395],[260,300],[175,210]],1],
    ['preference-2','preference',[[498,365],[420,300],[360,185],[320,105]],2],
    ['preference-3','preference',[[500,300],[445,245],[415,155],[410,82]],2],
    ['persona-0','persona',[[505,510],[465,405],[430,285],[390,165]],1],
    ['persona-1','persona',[[502,430],[500,335],[500,205],[510,82]],1],
    ['persona-2','persona',[[503,355],[540,285],[585,190],[625,112]],2],
    ['system_state-0','system_state',[[508,525],[610,475],[750,430],[860,340]],1],
    ['system_state-1','system_state',[[507,450],[620,400],[750,305],[825,215]],1],
    ['system_state-2','system_state',[[504,370],[590,315],[675,205],[705,112]],2],
    ['system_state-3','system_state',[[501,305],[555,250],[610,155],[600,78]],2],
    ['system_state-4','system_state',[[500,485],[430,420],[275,355],[145,270]],2],
    ['system_state-5','system_state',[[501,390],[475,315],[455,190],[465,92]],2],
  ];
  const branches = specs.map(([id, category, values, level]) => curve(id, category, values, sx, sy, level));
  return { root: { ...root, paths: roots }, trunk, branches, crown, bounds: { width: safeWidth, height: safeHeight } };
}
