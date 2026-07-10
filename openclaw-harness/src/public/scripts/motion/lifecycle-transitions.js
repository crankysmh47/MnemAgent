const DURATIONS = Object.freeze({
  'opening-skeleton': 2000,
  'opening-branches': 3000,
  'opening-root': 3000,
  'opening-annotations': 2000,
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
