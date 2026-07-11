export function createFallingLeaves({ root = null, reducedMotion = false, random = Math.random, schedule = (fn, ms) => setTimeout(fn, ms), cancel = id => clearTimeout(id) } = {}) {
  let running = false, visible = true, timer = null;
  const active = new Set();
  const nextDelay = () => 7000 + Math.round(Math.max(0, Math.min(1, random())) * 5000);
  const remove = leaf => { active.delete(leaf); leaf?.remove?.(); };
  const spawn = () => {
    if (!running || !visible || reducedMotion) return;
    if (active.size < 2 && root?.ownerDocument) {
      const leaf = root.ownerDocument.createElementNS('http://www.w3.org/2000/svg', 'path');
      const startX = 260 + random() * 500;
      leaf.setAttribute('class', 'falling-leaf'); leaf.setAttribute('aria-hidden', 'true');
      leaf.setAttribute('d', 'M0 0 C5 -8 14 -8 16 0 C11 8 4 8 0 0Z');
      leaf.style.setProperty('--leaf-x', `${startX}px`); leaf.style.setProperty('--leaf-drift', `${-45 + random() * 90}px`);
      root.append(leaf); active.add(leaf);
      leaf.addEventListener?.('animationend', () => remove(leaf), { once: true });
      schedule(() => remove(leaf), 6500);
    }
    timer = schedule(spawn, nextDelay());
  };
  return {
    start() { if (running || reducedMotion) return; running = true; timer = schedule(spawn, nextDelay()); },
    stop() { running = false; if (timer != null) cancel(timer); timer = null; for (const leaf of [...active]) remove(leaf); },
    setVisible(value) { visible = Boolean(value); if (!visible) this.stop(); },
    isRunning() { return running; },
    destroy() { this.stop(); },
  };
}
