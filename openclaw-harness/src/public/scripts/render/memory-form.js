const SHAPE_PATHS = Object.freeze({
  leaf: size => `M0,${-size} C${size * 0.86},${-size * 0.7} ${size * 0.92},${size * 0.35} 0,${size} C${-size * 0.92},${size * 0.35} ${-size * 0.86},${-size * 0.7} 0,${-size} Z`,
  pearl: size => `M0,${-size} C${size * 0.62},${-size} ${size},${-size * 0.62} ${size},0 C${size},${size * 0.62} ${size * 0.62},${size} 0,${size} C${-size * 0.62},${size} ${-size},${size * 0.62} ${-size},0 C${-size},${-size * 0.62} ${-size * 0.62},${-size} 0,${-size} Z`,
  mineral: size => `M0,${-size} L${size * 0.86},${-size * 0.22} L${size * 0.58},${size} L${-size * 0.58},${size} L${-size * 0.86},${-size * 0.22} Z`,
  husk: size => `M${-size * 0.72},${size} L${-size * 0.72},${-size * 0.45} C${-size * 0.25},${-size * 1.05} ${size * 0.25},${-size * 1.05} ${size * 0.72},${-size * 0.45} L${size * 0.72},${size}`,
});

export function memoryFormPath(shape = 'pearl', size = 12) {
  const safeSize = Number.isFinite(Number(size)) ? Math.max(2, Number(size)) : 12;
  return (SHAPE_PATHS[shape] || SHAPE_PATHS.pearl)(safeSize);
}

export function memoryAriaLabel(memory = {}) {
  const confidence = Math.round(Math.max(0, Math.min(1, Number(memory.confidence) || 0)) * 100);
  const recalls = Number(memory.injectionCount) || 0;
  return `${memory.statement || 'Unnamed memory'}; ${memory.category || 'system state'}; ${memory.lifecycle || 'settled'}; ${confidence}% confidence; ${recalls} recalls`;
}

export const shapeClass = shape => `memory-form memory-form-${SHAPE_PATHS[shape] ? shape : 'pearl'}`;
