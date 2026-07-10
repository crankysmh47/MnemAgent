import { eventGlyph } from './annotations.js';

const eventLabel = event => event?.displayStatement || event?.event_type || event?.eventType || 'Archive settled';

export function createTimeline(root, { onReplay = () => {} } = {}) {
  function render(events = []) {
    if (!root) return;
    while (root.firstChild) root.removeChild(root.firstChild);
    for (const event of [...events].reverse().slice(-24)) {
      const item = document.createElement('button'); item.type = 'button'; item.className = `sediment-event sediment-${eventGlyph(event)}`; item.dataset.eventId = String(event.id ?? ''); item.setAttribute('aria-label', eventLabel(event));
      const glyph = document.createElement('span'); glyph.className = 'sediment-glyph'; glyph.setAttribute('aria-hidden', 'true'); glyph.textContent = { seed: '✦', pulse: '◌', scar: '╳', husk: '⌁', settled: '·' }[eventGlyph(event)];
      const text = document.createElement('span'); text.className = 'sediment-label'; text.textContent = eventLabel(event);
      item.append(glyph, text); item.addEventListener('click', () => onReplay(event)); root.append(item);
    }
  }
  return { render, destroy() { if (root) root.replaceChildren(); } };
}
