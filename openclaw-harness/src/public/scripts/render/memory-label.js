export function shortMemoryStatement(memory = {}, maxLength = 110) {
  const statement = String(memory?.statement || '').trim() || 'Memory details unavailable';
  const limit = Math.max(8, Number(maxLength) || 110);
  if (statement.length <= limit) return statement;
  const slice = statement.slice(0, limit - 1);
  const boundary = slice.lastIndexOf(' ');
  return `${slice.slice(0, boundary > limit * .55 ? boundary : slice.length).trimEnd()}…`;
}

export function memoryLabelPosition(node = {}, bounds = {}, size = {}) {
  const width = Number(size.width) || 220, height = Number(size.height) || 38;
  const stageWidth = Number(bounds.width) || 1000, stageHeight = Number(bounds.height) || 720;
  const x = Math.max(8, Math.min(stageWidth - 8, Number(node.x) || 0));
  const radius = Number(node.radius) || 10;
  const above = (Number(node.y) || 0) - radius - height - 8;
  const y = above >= 8 ? above : Math.min(stageHeight - height - 8, (Number(node.y) || 0) + radius + 10);
  const anchor = x < width / 2 + 8 ? 'start' : x > stageWidth - width / 2 - 8 ? 'end' : 'middle';
  return { x, y, anchor };
}
