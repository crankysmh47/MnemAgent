export function createAmbientMotion(root, store) {
  let running = false;
  const update = () => { if (root) root.dataset.ambient = running ? 'breathing' : 'still'; };
  const visibility = () => { running = document.visibilityState === 'visible' && store?.getState?.().motionEnabled !== false; update(); };
  return { start() { running = true; update(); document.addEventListener?.('visibilitychange', visibility); }, stop() { running = false; update(); document.removeEventListener?.('visibilitychange', visibility); }, destroy() { this.stop(); } };
}
