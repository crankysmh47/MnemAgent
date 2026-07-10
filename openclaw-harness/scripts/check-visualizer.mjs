import express from 'express';
import { chromium } from 'playwright';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { GRAPH_FIXTURE, METRICS_FIXTURE, EVENTS_FIXTURE } from '../test/fixtures/archive-fixture.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
let server;
let baseUrl = process.env.VISUALIZER_URL;

async function startFixtureServer() {
  const app = express();
  app.use(express.static(path.join(root, 'src', 'public')));
  app.use('/vendor/d3', express.static(path.join(root, 'node_modules', 'd3', 'dist')));
  app.get('/api/graph/:uid', (_req, res) => res.json(GRAPH_FIXTURE));
  app.get('/api/metrics/:uid', (_req, res) => res.json(METRICS_FIXTURE));
  app.get('/api/events/:uid', (_req, res) => res.json(EVENTS_FIXTURE));
  app.get('/api/user/whoami', (_req, res) => res.json({ user_id: 'demo-brain' }));
  app.get('/api/setup/default-user-id', (_req, res) => res.json({ user_id: 'demo-brain' }));
  await new Promise(resolve => { server = app.listen(0, '127.0.0.1', resolve); });
  return `http://127.0.0.1:${server.address().port}/?user=demo-brain`;
}

async function run() {
  if (!baseUrl) baseUrl = await startFixtureServer();
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1080 } });
  const errors = [];
  page.on('console', message => { if (message.type() === 'error') errors.push(`console: ${message.text()}`); });
  page.on('pageerror', error => errors.push(`pageerror: ${error.message}`));
  try {
    await page.goto(baseUrl, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForSelector('.memory-form', { timeout: 15000 });
    const report = await page.evaluate(() => ({
      title: document.title,
      status: document.querySelector('#archiveApp')?.dataset.status,
      memories: document.querySelectorAll('.memory-form').length,
      tendrils: document.querySelectorAll('.tendril').length,
      hasOldGraph: Boolean(document.querySelector('.graph-panel, .stat-card, #eventFeed, canvas')),
      hasStage: Boolean(document.querySelector('#archiveSvg')),
    }));
    if (!report.title.includes('Living Archive')) throw new Error('wrong page title');
    if (!report.memories || !report.tendrils || !report.hasStage || report.hasOldGraph) throw new Error(`semantic surface failed: ${JSON.stringify(report)}`);
    await page.waitForTimeout(500);
    if (process.env.VISUALIZER_SCREENSHOT) await page.screenshot({ path: process.env.VISUALIZER_SCREENSHOT, fullPage: true });
    await page.locator('.memory-form').first().click({ force: true });
    if (!(await page.locator('#memoryDetail').textContent()).trim()) throw new Error('memory focus did not update details');
    await page.locator('.memory-form').first().dblclick({ force: true });
    if (!(await page.locator('.memory-form.is-selected').count())) throw new Error('trace/focus did not select memory');
    await page.locator('#archiveMenuButton').click();
    if (!(await page.locator('#archiveMenu').getAttribute('open'))?.includes('')) throw new Error('archive menu did not open');
    await page.setViewportSize({ width: 390, height: 844 });
    if (await page.locator('.observation-sheet').count() !== 1) throw new Error('mobile observation sheet missing');
    await page.emulateMedia({ reducedMotion: 'reduce' });
    const reduced = await page.locator('#archiveStage').evaluate(node => getComputedStyle(node.querySelector('#archiveWorld')).animationName);
    if (reduced !== 'none') throw new Error(`reduced motion still animates: ${reduced}`);
    console.log(JSON.stringify({ url: baseUrl, report, consoleErrors: errors }, null, 2));
    if (errors.length) process.exitCode = 1;
  } finally {
    await browser.close();
    if (server) await new Promise(resolve => server.close(resolve));
  }
}

run().catch(error => { console.error(error); process.exitCode = 1; if (server) server.close(); });
