import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const root = new URL('../src/public/', import.meta.url);
const html = fs.readFileSync(new URL('index.html', root), 'utf8');
const tokens = fs.readFileSync(new URL('styles/tokens.css', root), 'utf8');
const responsive = fs.readFileSync(new URL('styles/responsive.css', root), 'utf8');
const motion = fs.readFileSync(new URL('styles/motion.css', root), 'utf8');

test('living archive static contract', () => {
  for (const id of [
    'archiveApp', 'archiveStage', 'archiveSvg', 'archiveWorld',
    'observationMargin', 'narrativeCopy', 'memoryDetail', 'vitalSigns',
    'materialLegend', 'sedimentTimeline', 'archiveMenu', 'archiveStatus',
    'memoryCompanionList', 'observationSheet',
  ]) {
    assert.equal((html.match(new RegExp(`id="${id}"`, 'g')) || []).length, 1, id);
  }

  assert.equal((html.match(/d3\.min\.js/g) || []).length, 1);
  assert.match(html, /src="\/vendor\/d3\/d3\.min\.js"/);
  assert.match(html, /type="module" src="\/scripts\/main\.js"/);
  assert.doesNotMatch(html, /chart\.js/i);

  for (const hex of ['#151714', '#EEE8DA', '#F6F1E7', '#B68A4A', '#69765A', '#94A67C', '#A86758', '#637985', '#8B8171']) {
    assert.match(tokens, new RegExp(hex, 'i'));
  }

  const samples = fs.readFileSync(new URL('assets/material-samples.svg', root), 'utf8');
  for (const label of ['Leaf', 'Pearl', 'Mineral', 'Scar', 'Husk']) {
    assert.match(samples, new RegExp(`<title>${label}</title>`));
  }
  assert.match(html, /class="skip-link"/);
  assert.match(html, /id="memoryCompanionList"/);
  assert.match(responsive, /max-width:\s*1099px/);
  assert.match(responsive, /max-width:\s*700px/);
  assert.match(responsive, /min-width:\s*44px/);
  assert.match(motion, /prefers-reduced-motion/);
});
