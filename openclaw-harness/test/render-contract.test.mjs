import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const root = new URL('../src/public/', import.meta.url);
const html = fs.readFileSync(new URL('index.html', root), 'utf8');
const tokens = fs.readFileSync(new URL('styles/tokens.css', root), 'utf8');
const responsive = fs.readFileSync(new URL('styles/responsive.css', root), 'utf8');
const motion = fs.readFileSync(new URL('styles/motion.css', root), 'utf8');
const stageCss = fs.readFileSync(new URL('styles/archive-stage.css', root), 'utf8');
const rendererSource = fs.readFileSync(new URL('scripts/render/living-structure.js', root), 'utf8');
const mainSource = fs.readFileSync(new URL('scripts/main.js', root), 'utf8');
const forestScenePath = new URL('scripts/render/forest-scene.js', root);
const forestSceneSource = fs.existsSync(forestScenePath) ? fs.readFileSync(forestScenePath, 'utf8') : '';

test('living archive static contract', () => {
  for (const id of [
    'archiveApp', 'archiveStage', 'archiveSvg', 'archiveWorld',
    'observationMargin', 'narrativeCopy', 'memoryDetail', 'vitalSigns',
    'materialLegend', 'sedimentTimeline', 'archiveMenu', 'archiveStatus',
    'memoryCompanionList', 'observationSheet', 'archiveLoader',
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

test('initial loading state is accessible and choreographs current forest layers', () => {
  assert.match(html, /id="archiveLoader"/);
  assert.match(html, /role="status"/);
  assert.match(html, /Awakening the archive/);
  assert.match(mainSource, /data-loading/);
  for (const selector of ['g.water', 'g.groundcover', 'g.roots', 'g.trunk', 'g.branches', 'g.memories', 'g.tendrils', 'g.canopy']) {
    assert.match(motion, new RegExp(selector.replace('.', '\\.')));
  }
  assert.match(rendererSource, /--memory-index/);
  assert.match(motion, /var\(--memory-index/);
  assert.match(motion, /data-opening="true"[\s\S]*g\.memories \.memory-interaction/);
  assert.doesNotMatch(motion, /data-opening="true"[^\n]*\.memory-form\s*\{/);
  assert.match(motion, /prefers-reduced-motion[\s\S]*archive-loader/);
});

test('archive header uses the official logo and exposes the repository', () => {
  assert.equal(fs.existsSync(new URL('assets/logo.jpg', root)), true);
  assert.match(html, /src="\/assets\/logo\.jpg"/);
  assert.match(html, /alt="MnemAgent logo"/);
  assert.match(html, /href="https:\/\/github\.com\/crankysmh47\/MnemAgent"/);
  assert.match(html, /aria-label="Open MnemAgent on GitHub"/);
  assert.match(html, /target="_blank"/);
  assert.match(html, /rel="noopener noreferrer"/);
  assert.doesNotMatch(html, /id="liveState"/);
  assert.doesNotMatch(mainSource, /liveState/);
});

test('memory interaction motion is isolated from placement transforms', () => {
  assert.match(rendererSource, /memory-interaction/);
  assert.match(stageCss, /\.memory-form:hover \.memory-interaction/);
  assert.doesNotMatch(stageCss, /\.memory-form:hover\s*,/);
});

test('renderer exposes botanical structure layers', () => {
  for (const layer of ['roots','trunk','branches']) assert.match(rendererSource, new RegExp(`['"]${layer}['"]`));
});

test('renderer exposes a restrained interactive forest frame', () => {
  assert.match(rendererSource, /\['canopy', 'water', 'groundcover', 'roots', 'trunk', 'branches', 'tendrils', 'memories', 'effects', 'annotations'\]/);
  for (const className of ['hanging-vine', 'hanging-vine-hit', 'forest-water', 'forest-ripple', 'grass-bank', 'grass-blade']) {
    assert.match(forestSceneSource, new RegExp(className));
    assert.match(stageCss, new RegExp(`\\.${className}`));
  }
  assert.doesNotMatch(rendererSource, /garden-vine|vine-leaf/);
  assert.match(motion, /vine-sway/);
  assert.match(stageCss, /hanging-vine:hover/);
  assert.match(motion, /prefers-reduced-motion[\s\S]*hanging-vine/);
});

test('forest observatory polish stays subordinate to the centered tree', () => {
  assert.equal((html.match(/class="dappled-light /g) || []).length, 2);
  for (const token of ['forest-water-wash','memory-hover-label']) assert.match(rendererSource + forestSceneSource, new RegExp(token));
  assert.match(stageCss, /\.forest-water-wash/);
  assert.match(stageCss, /\.memory-hover-label/);
  assert.match(motion, /seed-turn 1\.4s/);
  assert.match(motion, /leaf-fall/);
  assert.doesNotMatch(stageCss + motion, /#archiveWorld\s*\{[^}]*transform:\s*translate/s);
});

test('vine interaction keeps a stable hit area and never replaces the ambient animation', () => {
  assert.match(forestSceneSource, /hanging-vine-motion/);
  assert.match(forestSceneSource, /hanging-vine-response/);
  assert.match(motion, /\.hanging-vine-motion\s*\{[^}]*animation:\s*vine-sway/s);
  assert.match(stageCss, /\.hanging-vine:hover\s+\.hanging-vine-response/);
  assert.doesNotMatch(motion, /\.hanging-vine:hover\s*\{[^}]*animation(?:-name|-duration)?:/s);
  assert.match(stageCss, /\.hanging-vine-hit\s*\{[^}]*pointer-events:\s*stroke/s);
});
