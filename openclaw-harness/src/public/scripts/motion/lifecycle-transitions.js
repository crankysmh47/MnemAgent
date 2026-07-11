const DURATIONS = Object.freeze({
  'opening-ground': 500,
  'opening-tree': 700,
  'opening-bloom': 1200,
  'opening-settle': 500,
  arrival: 1200,
  rooting: 1100,
  recall: 900,
  revision: 1400,
  decay: 1200,
  prune: 1100,
});

export function transitionForPhase(phase = 'settled', reducedMotion = false) {
  return { className: `phase-${phase}`, duration: reducedMotion ? Math.min(180, DURATIONS[phase] || 160) : (DURATIONS[phase] || 160) };
}

export function applyLifecycleTransition(root, phase, reducedMotion = false) {
  if (!root) return transitionForPhase(phase, reducedMotion);
  const spec = transitionForPhase(phase, reducedMotion);
  root.dataset.phase = phase;
  root.classList.remove(...Object.keys(DURATIONS).map(name => `phase-${name}`));
  root.classList.add(spec.className);
  return spec;
}
