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
  app.get('/api/judge/scenarios', (_req, res) => res.json({
    model: 'deepseek-api/deepseek-v4-flash',
    repository: 'crankysmh47/MnemBench',
    scenarios: [{ issueNumber: 1, title: 'Fix inverted contradiction score', outcome: 'Test-first bounded fix' }],
  }));
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
    const loadingStarted=Date.now();
    await page.goto(baseUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(900);
    if ((await page.locator('#archiveStage').getAttribute('data-loading')) !== 'true') throw new Error('loader left before one full spinner turn');
    await page.waitForFunction(() => document.querySelector('#archiveStage')?.dataset.loading === 'false', null, { timeout: 10000 });
    if (Date.now()-loadingStarted < 1400) throw new Error('loader minimum hold was shorter than 1400ms');
    await page.waitForSelector('.memory-form', { timeout: 15000 });
    await page.waitForFunction(() => document.querySelector('#archiveStage')?.dataset.opening === 'false', null, { timeout: 10000 });
    const report = await page.evaluate(() => ({
      title: document.title,
      status: document.querySelector('#archiveApp')?.dataset.status,
      memories: document.querySelectorAll('.memory-form').length,
      interactions: document.querySelectorAll('.memory-interaction').length,
      tendrils: document.querySelectorAll('.tendril').length,
      roots: document.querySelectorAll('.root-line').length,
      branches: document.querySelectorAll('.branch').length,
      trunks: document.querySelectorAll('.trunk-line').length,
      hangingVines: document.querySelectorAll('.hanging-vine').length,
      waterBodies: document.querySelectorAll('.forest-water').length,
      grassBlades: document.querySelectorAll('.grass-blade').length,
      waterWashes: document.querySelectorAll('.forest-water-wash').length,
      firstLabel: document.querySelector('.memory-form')?.getAttribute('aria-label') || '',
      hasOldGraph: Boolean(document.querySelector('.graph-panel, .stat-card, #eventFeed, canvas')),
      hasStage: Boolean(document.querySelector('#archiveSvg')),
    }));
    if (!report.title.includes('Living Archive')) throw new Error('wrong page title');
    if (!report.memories || report.interactions !== report.memories || !report.tendrils || report.tendrils > 96 || report.roots < 5 || report.branches < 9 || report.trunks !== 1 || report.hangingVines !== 4 || report.waterBodies !== 1 || report.waterWashes !== 2 || report.grassBlades < 18 || !report.firstLabel || report.firstLabel.includes('Unnamed memory') || !report.hasStage || report.hasOldGraph) throw new Error(`semantic surface failed: ${JSON.stringify(report)}`);
    await page.waitForTimeout(500);
    if (process.env.VISUALIZER_SCREENSHOT) await page.screenshot({ path: process.env.VISUALIZER_SCREENSHOT, fullPage: true });
    const firstVine = page.locator('.hanging-vine').first();
    const firstVineMotion = firstVine.locator('.hanging-vine-motion');
    const firstVineResponse = firstVine.locator('.hanging-vine-response');
    if (!(await firstVineMotion.evaluate(node => getComputedStyle(node).animationName)).includes('vine-sway')) throw new Error('hanging vine is not gently animated');
    const responseBeforeHover = await firstVineResponse.evaluate(node => getComputedStyle(node).transform);
    await page.locator('.hanging-leaf').first().hover({ force: true });
    await page.waitForTimeout(700);
    const vineHoverState = await firstVine.evaluate(node => ({ groupHovered: node.matches(':hover'), animationName: getComputedStyle(node.querySelector('.hanging-vine-motion')).animationName, responseTransform: getComputedStyle(node.querySelector('.hanging-vine-response')).transform }));
    if (!vineHoverState.groupHovered || vineHoverState.animationName !== 'vine-sway' || vineHoverState.responseTransform === responseBeforeHover) throw new Error(`hanging vine did not react smoothly to hover: ${JSON.stringify(vineHoverState)}`);
    const firstMemory = page.locator('.memory-form').first();
    const placementBeforeHover = await firstMemory.getAttribute('transform');
    await firstMemory.hover({ force: true });
    await page.waitForTimeout(220);
    const hoverLabels=page.locator('.memory-hover-label');
    if(await hoverLabels.count()!==1 || !(await hoverLabels.textContent()).trim()) throw new Error('memory hover note did not appear');
    const placementAfterHover = await firstMemory.getAttribute('transform');
    if (placementBeforeHover !== placementAfterHover) throw new Error('hover changed the memory placement transform');
    await firstMemory.click({ force: true });
    if (!(await page.locator('#memoryDetail').textContent()).trim()) throw new Error('memory focus did not update details');
    await page.waitForTimeout(240);
    if (!(await page.locator('#archiveSvg').getAttribute('class'))?.includes('has-memory-focus')) throw new Error('memory focus did not enter focus mode');
    const quietMemoryOpacity = Number(await page.locator('.memory-form.is-quiet').first().evaluate(node => getComputedStyle(node).opacity));
    const quietTendrilOpacity = Number(await page.locator('.tendril.is-quiet').first().evaluate(node => getComputedStyle(node).opacity));
    if (quietMemoryOpacity > 0.08 || quietTendrilOpacity > 0.04) throw new Error(`memory chain background remained too dense: memories ${quietMemoryOpacity}, tendrils ${quietTendrilOpacity}`);
    if (process.env.VISUALIZER_FOCUS_SCREENSHOT) await page.screenshot({ path: process.env.VISUALIZER_FOCUS_SCREENSHOT, fullPage: true });
    await firstMemory.dblclick({ force: true });
    if (!(await page.locator('.memory-form.is-selected').count())) throw new Error('trace/focus did not select memory');
    await page.locator('#archiveMenuButton').click();
    if (!(await page.locator('#archiveMenu').getAttribute('open'))?.includes('')) throw new Error('archive menu did not open');
    await page.keyboard.press('Escape');
    await page.setViewportSize({ width: 1920, height: 997 });
    const desktopFit=await page.evaluate(()=>({innerHeight:window.innerHeight,documentHeight:document.documentElement.scrollHeight,timelineBottom:document.querySelector('#sedimentTimeline')?.getBoundingClientRect().bottom,stageHeight:document.querySelector('#archiveStage')?.getBoundingClientRect().height}));
    if(desktopFit.documentHeight>desktopFit.innerHeight+1 || desktopFit.timelineBottom>desktopFit.innerHeight+1 || desktopFit.stageHeight<420) throw new Error(`desktop archive escaped viewport: ${JSON.stringify(desktopFit)}`);
    await page.setViewportSize({ width: 1920, height: 700 });
    const observation=page.locator('#observationMargin');
    await observation.hover(); await page.mouse.wheel(0,500); await page.waitForTimeout(80);
    const panelScroll=await observation.evaluate(node=>({top:node.scrollTop,max:node.scrollHeight-node.clientHeight,pageTop:window.scrollY}));
    if(panelScroll.max>0 && panelScroll.top===0 || panelScroll.pageTop!==0) throw new Error(`observation scroll was not contained: ${JSON.stringify(panelScroll)}`);
    await page.locator('#archiveStage').hover(); await page.mouse.wheel(0,400); await page.waitForTimeout(80);
    if(await page.evaluate(()=>window.scrollY)!==0) throw new Error('stage wheel moved the whole document');
    await page.setViewportSize({ width: 390, height: 844 });
    if (await page.locator('.observation-sheet').count() !== 1) throw new Error('mobile observation sheet missing');
    await page.emulateMedia({ reducedMotion: 'reduce' });
    const reduced = await page.locator('#archiveStage').evaluate(node => getComputedStyle(node.querySelector('#archiveWorld')).animationName);
    if (reduced !== 'none') throw new Error(`reduced motion still animates: ${reduced}`);
    if ((await firstVineMotion.evaluate(node => getComputedStyle(node).animationName)) !== 'none') throw new Error('reduced motion did not stop hanging vines');
    console.log(JSON.stringify({ url: baseUrl, report, consoleErrors: errors }, null, 2));
    if (errors.length) process.exitCode = 1;
  } finally {
    await browser.close();
    if (server) await new Promise(resolve => server.close(resolve));
  }
}

run().catch(error => { console.error(error); process.exitCode = 1; if (server) server.close(); });
