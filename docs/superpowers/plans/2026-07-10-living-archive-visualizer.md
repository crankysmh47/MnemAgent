# Living Archive Visualizer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the existing visualizer with a cohesive Living Archive experience that teaches first-time viewers how MnemAgent memories arrive, connect, strengthen, change, and fade.

**Architecture:** Keep the Express harness and its existing APIs, but replace the monolithic visualizer with native browser ES modules, semantic HTML, modular CSS, SVG, and vendored D3. Pure modules normalize data, reduce state, select narratives, and compute deterministic layouts; focused renderers and a choreography layer turn that state into one continuous organic-cybernetic composition.

**Tech Stack:** Node.js CommonJS server, native browser ES modules, D3 7.9.0, SVG, CSS, Node built-in test runner, Playwright 1.53.2.

## Global Constraints

- Treat `docs/superpowers/specs/2026-07-10-living-archive-visualizer-design.md` as authoritative.
- Discard the existing visual design, layout, metaphors, components, chart treatment, brain silhouette, terminal feed, and manual node arrangement.
- Preserve only useful backend contracts: `/api/graph/:uid`, `/api/events/:uid`, `/api/metrics/:uid`, `/api/user/whoami`, `/api/setup/default-user-id`, `/api/demo/status`, and `/api/demo/seed`.
- Use the exact palette in the design specification, including lichen green `#94A67C`.
- Use antique brass as a material, never as neon emission or bloom.
- Preserve the fixed visual hierarchy: archive, changing memory, narrative annotation, vital signs, controls.
- Introduce no frontend framework and no frontend build pipeline.
- Use D3 only for selections, joins, zoom behavior, and path/layout assistance.
- Keep the Express server CommonJS; scope browser `.js` files as ES modules with `src/public/scripts/package.json`.
- Category and lifecycle state must use shape, text, and material treatment in addition to color.
- Opening choreography must not block input and must not replay after polling or resize.
- Reduced-motion mode must retain all information and interactions.
- Do not mutate backend data from the visualizer.
- Do not auto-seed any user except `demo-brain`.
- At most one task may be in progress at a time. Finish its tests and commit before starting the next task.

---

## File Map

### Existing files to replace or modify

- `openclaw-harness/src/public/index.html` — replace with the semantic Living Archive shell.
- `openclaw-harness/src/public/favicon.svg` — replace with the simplified brass seal.
- `openclaw-harness/src/public/visualizer.css` — delete after modular styles are active.
- `openclaw-harness/src/public/mnemagent-logo-square.png` — delete after the seal is active.
- `openclaw-harness/src/index.js` — remove Chart.js serving and disable caching for module/assets during development.
- `openclaw-harness/package.json` — add test scripts and Playwright development dependency; remove Chart.js.
- `openclaw-harness/package-lock.json` — regenerate only through npm commands.
- `openclaw-harness/scripts/check-visualizer.mjs` — replace the old brain/node assertions with Living Archive semantic, interaction, accessibility, and console checks.
- `docs/assets/visualizer-snapshot.png` — replace after the final browser verification.

### New application files

- `openclaw-harness/src/public/assets/mnemagent-seal.svg` — one-color logo seal.
- `openclaw-harness/src/public/assets/paper-grain.svg` — subtle reusable texture.
- `openclaw-harness/src/public/assets/material-samples.svg` — legend samples for leaf, pearl, mineral, scar, and husk.
- `openclaw-harness/src/public/styles/tokens.css` — palette, typography, dimensions, easing, layers.
- `openclaw-harness/src/public/styles/base.css` — reset, page, header, controls, focus, state utilities.
- `openclaw-harness/src/public/styles/archive-stage.css` — central SVG composition and memory forms.
- `openclaw-harness/src/public/styles/observation-margin.css` — annotations, details, vital signs, legend.
- `openclaw-harness/src/public/styles/sediment-timeline.css` — bottom lifecycle history.
- `openclaw-harness/src/public/styles/motion.css` — opening, ambient, lifecycle, and reduced-motion rules.
- `openclaw-harness/src/public/styles/responsive.css` — desktop, tablet, and mobile composition.
- `openclaw-harness/src/public/scripts/package.json` — scopes browser modules as ESM for Node tests.
- `openclaw-harness/src/public/scripts/api.js` — validated HTTP reads and partial-failure snapshot loading.
- `openclaw-harness/src/public/scripts/memory-model.js` — normalization and derived visual/lifecycle state.
- `openclaw-harness/src/public/scripts/archive-store.js` — reducer, subscriptions, and stable view state.
- `openclaw-harness/src/public/scripts/narrative.js` — lifecycle event mapping and first-viewer copy.
- `openclaw-harness/src/public/scripts/layout.js` — deterministic groves, nodes, tendrils, and bounds.
- `openclaw-harness/src/public/scripts/render/memory-form.js` — category form geometry.
- `openclaw-harness/src/public/scripts/render/tendril.js` — relationship path geometry and styling.
- `openclaw-harness/src/public/scripts/render/living-structure.js` — stable D3 joins for the archive SVG.
- `openclaw-harness/src/public/scripts/render/annotations.js` — observation margin and accessible companion list.
- `openclaw-harness/src/public/scripts/render/timeline.js` — sediment event joins and replay controls.
- `openclaw-harness/src/public/scripts/motion/choreographer.js` — opening and event queue ownership.
- `openclaw-harness/src/public/scripts/motion/lifecycle-transitions.js` — event-specific SVG transitions.
- `openclaw-harness/src/public/scripts/motion/ambient-motion.js` — page visibility and motion preference.
- `openclaw-harness/src/public/scripts/interactions/archive-navigation.js` — zoom, pan, and reset.
- `openclaw-harness/src/public/scripts/interactions/memory-focus.js` — hover, focus, trace, Escape.
- `openclaw-harness/src/public/scripts/interactions/archive-menu.js` — filters, user, export, replay, motion.
- `openclaw-harness/src/public/scripts/main.js` — startup, polling, orchestration, and cleanup.

### New tests and fixtures

- `openclaw-harness/test/fixtures/archive-fixture.mjs` — graph, metrics, events, and degraded fixtures.
- `openclaw-harness/test/memory-model.test.mjs` — normalization and lifecycle derivation.
- `openclaw-harness/test/archive-store.test.mjs` — reducer and view-state preservation.
- `openclaw-harness/test/narrative.test.mjs` — event priority, copy, and burst behavior.
- `openclaw-harness/test/layout.test.mjs` — determinism, bounds, groves, and paths.
- `openclaw-harness/test/api.test.mjs` — URLs, validation, and partial failure.
- `openclaw-harness/test/render-contract.test.mjs` — static shell, tokens, and required modules.

---

### Task 1: Establish the isolated module and test foundation

**Files:**
- Create: `openclaw-harness/src/public/scripts/package.json`
- Create: `openclaw-harness/test/fixtures/archive-fixture.mjs`
- Modify: `openclaw-harness/package.json`
- Modify: `openclaw-harness/package-lock.json`
- Modify: `openclaw-harness/src/index.js`

**Interfaces:**
- Produces: Browser `.js` modules importable by Node tests as ESM.
- Produces: `GRAPH_FIXTURE`, `METRICS_FIXTURE`, `EVENTS_FIXTURE`, and `EMPTY_FIXTURE` named fixture exports.
- Preserves: CommonJS execution of `openclaw-harness/src/index.js`.

- [ ] **Step 1: Add the browser-module scope**

Create `src/public/scripts/package.json` exactly as:

```json
{
  "type": "module"
}
```

- [ ] **Step 2: Add deterministic fixture data**

Create `test/fixtures/archive-fixture.mjs` with six beliefs: two preferences, two persona memories, and two system states. Use IDs `1..6`; weights `0.94`, `0.88`, `0.76`, `0.68`, `0.48`, `0.31`; and at least one `cluster`, `concept`, and `bridge` edge. Export metrics with `total_beliefs: 6`, `total_turns: 12`, and events with IDs `101..106` covering `new_belief`, `injected`, `influenced`, `contradiction`, `decayed`, and `pruned`.

The first belief must be:

```js
{
  id: 1,
  user_id: "demo-brain",
  category: "preference",
  entity_source: "interface",
  relation: "prefers",
  entity_target: "quiet motion",
  base_utility_q: 0.91,
  injection_count: 7,
  influence_count: 4,
  node_weight: 0.94,
  conviction_score: 0.96,
  created_at: "2026-07-10T08:00:00Z",
  last_accessed: "2026-07-10T08:10:00Z"
}
```

- [ ] **Step 3: Update package scripts and dependencies**

Run from `openclaw-harness`:

```powershell
npm uninstall chart.js
npm install --save-dev playwright@1.53.2
npx playwright install chromium
```

Then add these scripts without changing `start` or `dev`:

```json
"test": "node --test test/*.test.mjs",
"test:visualizer": "node scripts/check-visualizer.mjs",
"test:all": "npm test && npm run test:visualizer"
```

- [ ] **Step 4: Update static asset serving**

Delete the `/vendor/chart.js` route from `src/index.js`. Extend the no-cache predicate so `.js`, `.svg`, and `.png` requests receive the same development cache headers as `.html` and `.css`. Keep `/vendor/d3` unchanged.

- [ ] **Step 5: Verify the foundation**

Run:

```powershell
npm test
node -e "require('./src/index.js'); setTimeout(() => process.exit(0), 250)"
```

Expected: Node reports zero tests without an error; the server prints its normal startup line and no ESM/CommonJS exception.

- [ ] **Step 6: Commit**

```powershell
git add openclaw-harness/package.json openclaw-harness/package-lock.json openclaw-harness/src/index.js openclaw-harness/src/public/scripts/package.json openclaw-harness/test/fixtures/archive-fixture.mjs
git commit -m "test: establish visualizer module foundation"
```

---

### Task 2: Normalize API memory data into explicit visual states

**Files:**
- Create: `openclaw-harness/src/public/scripts/memory-model.js`
- Create: `openclaw-harness/test/memory-model.test.mjs`

**Interfaces:**
- Consumes: Raw graph beliefs and edges from Task 1 fixtures.
- Produces: `normalizeCategory(value): "preference"|"persona"|"system_state"`.
- Produces: `deriveLifecycle(memory): "new"|"rooted"|"vivid"|"stable"|"fading"|"dormant"`.
- Produces: `normalizeMemory(raw): NormalizedMemory`.
- Produces: `normalizeRelationship(raw, validIds): NormalizedRelationship|null`.
- Produces: `normalizeGraph(raw): { memories, relationships, totalTurns }`.
- Produces: `statementFor(memory): string`.

- [ ] **Step 1: Write failing normalization tests**

Test exact category aliases, clamping, shape selection, lifecycle thresholds, readable statements, invalid edges, and non-array payloads. Assert these thresholds:

```js
assert.equal(deriveLifecycle({ nodeWeight: 0.90, injectionCount: 4 }), "vivid");
assert.equal(deriveLifecycle({ nodeWeight: 0.70, injectionCount: 1 }), "stable");
assert.equal(deriveLifecycle({ nodeWeight: 0.45, injectionCount: 0 }), "fading");
assert.equal(deriveLifecycle({ nodeWeight: 0.20, injectionCount: 0 }), "dormant");
```

Assert shape mapping `preference → leaf`, `persona → pearl`, `system_state → mineral`.

- [ ] **Step 2: Run the focused test and confirm failure**

Run:

```powershell
node --test test/memory-model.test.mjs
```

Expected: FAIL with `ERR_MODULE_NOT_FOUND` for `memory-model.js`.

- [ ] **Step 3: Implement the pure memory model**

Use these exact rules:

```js
const CATEGORY_ALIASES = new Map([
  ["preference", "preference"],
  ["preferences", "preference"],
  ["persona", "persona"],
  ["system", "system_state"],
  ["system_state", "system_state"]
]);

export const clamp01 = value => Math.max(0, Math.min(1, Number(value) || 0));
```

`normalizeMemory` must return stable string IDs, preserve raw source/relation/target, derive `confidence` from `conviction_score ?? node_weight`, derive `vitality` from `node_weight`, and never throw for missing optional fields. Unsupported categories become `system_state`, not an invented fourth category.

- [ ] **Step 4: Run the focused and full unit suites**

```powershell
node --test test/memory-model.test.mjs
npm test
```

Expected: all normalization tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add openclaw-harness/src/public/scripts/memory-model.js openclaw-harness/test/memory-model.test.mjs
git commit -m "feat: normalize living archive memory data"
```

---

### Task 3: Create validated API reads with partial-failure recovery

**Files:**
- Create: `openclaw-harness/src/public/scripts/api.js`
- Create: `openclaw-harness/test/api.test.mjs`

**Interfaces:**
- Produces: `requestJson(path, { signal } = {}): Promise<object>`.
- Produces: `resolveUserId(locationSearch, storage): Promise<string>`.
- Produces: `loadArchiveSnapshot(userId, { since, signal } = {}): Promise<RawArchiveSnapshot>`.
- `RawArchiveSnapshot` contains `graph`, `metrics`, `events`, `failures`, and `status`.

- [ ] **Step 1: Write failing API tests using a stubbed `globalThis.fetch`**

Cover URL encoding, `?user=` precedence, local-storage fallback, `whoami` fallback, event `since` encoding, error payload messages, and partial failure. Assert that graph success plus metrics failure produces:

```js
{
  status: "degraded",
  failures: { metrics: "metrics unavailable" }
}
```

while all three failures produce `status: "error"`.

- [ ] **Step 2: Run the focused test and confirm failure**

```powershell
node --test test/api.test.mjs
```

Expected: FAIL with `ERR_MODULE_NOT_FOUND` for `api.js`.

- [ ] **Step 3: Implement concurrent snapshot loading**

Use `Promise.allSettled` for graph, metrics, and events. `requestJson` must throw `Error(data.error || "Request failed with HTTP <status>")`. Treat graph as the only source required for a usable archive; missing metrics or events yields `degraded`, while missing graph yields `error`.

Resolve user identity in this order:

1. Non-empty `?user=` value.
2. Non-empty `mnemos_user_id` local-storage value.
3. `/api/user/whoami` `user_id`.
4. `/api/setup/default-user-id` `user_id`.
5. Empty string.

- [ ] **Step 4: Verify tests**

```powershell
node --test test/api.test.mjs
npm test
```

Expected: all API tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add openclaw-harness/src/public/scripts/api.js openclaw-harness/test/api.test.mjs
git commit -m "feat: add resilient archive data loading"
```

---

### Task 4: Build the archive store and lifecycle narrative selector

**Files:**
- Create: `openclaw-harness/src/public/scripts/archive-store.js`
- Create: `openclaw-harness/src/public/scripts/narrative.js`
- Create: `openclaw-harness/test/archive-store.test.mjs`
- Create: `openclaw-harness/test/narrative.test.mjs`

**Interfaces:**
- Produces: `createInitialState(userId): ArchiveState`.
- Produces: `archiveReducer(state, action): ArchiveState`.
- Produces: `createArchiveStore(initialState): { getState, dispatch, subscribe }`.
- Produces: `normalizeEvent(raw): ArchiveEvent`.
- Produces: `eventIdentity(raw): string`.
- Produces: `selectNarrative(events, seenIds): NarrativeDecision`.
- Produces: `narrativeCopy(decision, memory): { eyebrow, title, body }`.

- [ ] **Step 1: Write reducer tests**

Test `LOAD_STARTED`, `SNAPSHOT_RECEIVED`, `SNAPSHOT_FAILED`, `SELECT_MEMORY`, `TRACE_MEMORY`, `CLEAR_FOCUS`, `SET_FILTERS`, `SET_ZOOM`, `SET_MOTION`, `OPENING_FINISHED`, `EVENTS_RECEIVED`, and `SET_DOCUMENT_VISIBLE`.

Assert that `SNAPSHOT_RECEIVED` preserves `selectedMemoryId`, `tracedMemoryId`, `zoom`, filters, and `openingComplete` when those values remain valid. If a selected memory disappears, selection becomes `null`.

- [ ] **Step 2: Write narrative tests**

Use this exact priority:

```js
export const EVENT_PRIORITY = Object.freeze({
  contradiction: 60,
  pruned: 50,
  new_belief: 40,
  injected: 30,
  influenced: 25,
  decayed: 20
});
```

Assert that one event receives `featured: true`, later events remain `featured: false`, duplicate identities are ignored, and unknown events map to a quiet `settled` glyph.

- [ ] **Step 3: Run both tests and confirm failure**

```powershell
node --test test/archive-store.test.mjs test/narrative.test.mjs
```

Expected: both test files FAIL because their modules do not exist.

- [ ] **Step 4: Implement immutable state and narrative mapping**

Use a `Set` clone for seen event IDs. Never store DOM nodes, D3 selections, timers, or abort controllers in the store. Map events as follows:

```js
const EVENT_PHASE = Object.freeze({
  new_belief: "arrival",
  injected: "recall",
  influenced: "recall",
  contradiction: "revision",
  decayed: "decay",
  pruned: "prune"
});
```

Narrative copy must use plain language first and put technical event names only in metadata.

- [ ] **Step 5: Verify tests**

```powershell
node --test test/archive-store.test.mjs test/narrative.test.mjs
npm test
```

Expected: all store and narrative tests PASS.

- [ ] **Step 6: Commit**

```powershell
git add openclaw-harness/src/public/scripts/archive-store.js openclaw-harness/src/public/scripts/narrative.js openclaw-harness/test/archive-store.test.mjs openclaw-harness/test/narrative.test.mjs
git commit -m "feat: add archive state and lifecycle narrative"
```

---

### Task 5: Compute a deterministic organic layout

**Files:**
- Create: `openclaw-harness/src/public/scripts/layout.js`
- Create: `openclaw-harness/test/layout.test.mjs`

**Interfaces:**
- Produces: `hashString(value): number`.
- Produces: `seededRandom(seed): () => number`.
- Produces: `computeArchiveLayout(memories, relationships, { width, height }): ArchiveLayout`.
- Produces: `relationshipPath(source, target, bend): string`.
- `ArchiveLayout` contains `nodes`, `paths`, `groves`, `bounds`, and `center`.

- [ ] **Step 1: Write deterministic layout tests**

Assert:

- Two calls with the same fixture and dimensions are deeply equal.
- Input order does not change positions.
- Every node remains inside 6% horizontal and 8% vertical stage margins.
- Categories occupy distinct but overlapping angular groves.
- All path strings contain finite numbers and begin with `M`.
- At more than 80 memories, `groves` contains collapsed distant groups while selected and high-vitality memories remain individual.

- [ ] **Step 2: Run the layout test and confirm failure**

```powershell
node --test test/layout.test.mjs
```

Expected: FAIL with `ERR_MODULE_NOT_FOUND` for `layout.js`.

- [ ] **Step 3: Implement normalized-coordinate layout**

Compute in a `1000 × 720` internal coordinate system, then scale to the supplied viewport. Place a brass root crown near `(430, 620)`. Assign base grove angles `preference: -145°`, `persona: -90°`, `system_state: -35°`; use identity hashes for small angular and radial variation; and bias higher vitality toward the centerline. Run a fixed 32-iteration collision relaxation with no time-based randomness.

Use cubic tendrils:

```js
export function relationshipPath(source, target, bend = 0.18) {
  const dx = target.x - source.x;
  const dy = target.y - source.y;
  const nx = -dy * bend;
  const ny = dx * bend;
  const c1x = source.x + dx * 0.35 + nx;
  const c1y = source.y + dy * 0.35 + ny;
  const c2x = source.x + dx * 0.65 + nx;
  const c2y = source.y + dy * 0.65 + ny;
  return `M${source.x},${source.y} C${c1x},${c1y} ${c2x},${c2y} ${target.x},${target.y}`;
}
```

- [ ] **Step 4: Verify tests**

```powershell
node --test test/layout.test.mjs
npm test
```

Expected: deterministic layout tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add openclaw-harness/src/public/scripts/layout.js openclaw-harness/test/layout.test.mjs
git commit -m "feat: add deterministic living archive layout"
```

---

### Task 6: Replace the page shell, assets, and visual tokens

**Files:**
- Replace: `openclaw-harness/src/public/index.html`
- Replace: `openclaw-harness/src/public/favicon.svg`
- Create: `openclaw-harness/src/public/assets/mnemagent-seal.svg`
- Create: `openclaw-harness/src/public/assets/paper-grain.svg`
- Create: `openclaw-harness/src/public/assets/material-samples.svg`
- Create: `openclaw-harness/src/public/styles/tokens.css`
- Create: `openclaw-harness/src/public/styles/base.css`
- Create: `openclaw-harness/test/render-contract.test.mjs`

**Interfaces:**
- Produces required DOM IDs: `archiveApp`, `archiveStage`, `archiveSvg`, `archiveWorld`, `observationMargin`, `narrativeCopy`, `memoryDetail`, `vitalSigns`, `materialLegend`, `sedimentTimeline`, `archiveMenu`, `archiveStatus`, `memoryCompanionList`, and `observationSheet`.
- Produces CSS tokens consumed by every later style file.

- [ ] **Step 1: Write the static contract test**

Read `index.html` and `tokens.css` with `node:fs`. Assert every required ID occurs exactly once, D3 loads only from `/vendor/d3/d3.min.js`, `main.js` uses `type="module"`, Chart.js is absent, and every palette hex from the design specification appears in `tokens.css`.

- [ ] **Step 2: Run the test and confirm failure**

```powershell
node --test test/render-contract.test.mjs
```

Expected: FAIL because the old shell does not satisfy the Living Archive contract.

- [ ] **Step 3: Replace `index.html` with the semantic shell**

Use this top-level structure:

```html
<body>
  <a class="skip-link" href="#archiveStage">Skip to the living archive</a>
  <div id="archiveApp" class="archive-app" data-status="loading">
    <header class="archive-header">
      <a class="archive-brand" href="/" aria-label="MnemAgent Living Archive home">
        <img src="/assets/mnemagent-seal.svg" alt="" />
        <span>MnemAgent</span>
      </a>
      <output id="liveState" aria-label="Archive connection status">Awakening</output>
      <button id="archiveMenuButton" type="button" aria-controls="archiveMenu" aria-expanded="false">Archive controls</button>
    </header>
    <main class="archive-composition">
      <section id="archiveStage" class="archive-stage" aria-labelledby="archiveTitle">
        <h1 id="archiveTitle" class="sr-only">MnemAgent Living Archive</h1>
        <svg id="archiveSvg" viewBox="0 0 1000 720" role="img" aria-describedby="archiveStatus">
          <defs id="archiveDefs"></defs>
          <g id="archiveWorld"></g>
        </svg>
        <p id="archiveStatus" class="sr-only" aria-live="polite"></p>
        <ol id="memoryCompanionList" class="sr-only"></ol>
      </section>
      <aside id="observationMargin" class="observation-margin" aria-label="Archive observation">
        <p class="observation-eyebrow">Living observation</p>
        <section id="narrativeCopy" aria-live="polite"></section>
        <section id="memoryDetail" aria-label="Selected memory"></section>
        <dl id="vitalSigns" aria-label="Archive vital signs"></dl>
        <section id="materialLegend" aria-label="Memory material legend"></section>
      </aside>
    </main>
    <nav id="sedimentTimeline" class="sediment-timeline" aria-label="Memory history"></nav>
    <dialog id="archiveMenu" class="archive-menu" aria-labelledby="archiveMenuTitle">
      <form method="dialog">
        <h2 id="archiveMenuTitle">Archive controls</h2>
        <label for="userId">Memory owner</label>
        <input id="userId" name="userId" autocomplete="off" />
        <fieldset id="categoryFilters"><legend>Memory forms</legend></fieldset>
        <fieldset id="lifecycleFilters"><legend>Vitality</legend></fieldset>
        <button id="motionToggle" type="button" aria-pressed="false">Reduce motion</button>
        <button id="replayOpening" type="button">Replay awakening</button>
        <button id="resetArchiveView" type="button">Reset view</button>
        <button id="exportArchive" type="button">Export archive data</button>
        <button id="retryArchive" type="button">Retry connection</button>
        <button value="close">Close controls</button>
      </form>
    </dialog>
    <section id="observationSheet" class="observation-sheet" aria-labelledby="observationSheetTitle">
      <h2 id="observationSheetTitle">Memory observation</h2>
      <div id="observationSheetContent"></div>
    </section>
  </div>
  <script src="/vendor/d3/d3.min.js"></script>
  <script type="module" src="/scripts/main.js"></script>
</body>
```

- [ ] **Step 4: Define exact tokens and base treatment**

Define the nine palette colors with names from the design spec. Also define `--font-display`, `--font-body`, `--font-mono`, `--ease-organic: cubic-bezier(.22,.61,.36,1)`, `--header-h: 58px`, `--timeline-h: 72px`, `--observation-w: clamp(300px, 31vw, 460px)`, and z-index layers `stage: 1`, `annotation: 3`, `header: 5`, `dialog: 10`.

Load Cormorant Garamond, Manrope, and IBM Plex Mono with `<link>` elements, but keep visible system fallbacks. Base focus uses a two-pixel bone-white outline plus a four-pixel antique-brass outer shadow.

- [ ] **Step 5: Create restrained SVG assets**

The seal uses one fill color via `currentColor`, a head profile, one incomplete ring, three branch traces, and no gradients. `paper-grain.svg` uses one low-opacity `feTurbulence` texture. `material-samples.svg` defines five labeled symbols: `sample-leaf`, `sample-pearl`, `sample-mineral`, `sample-scar`, and `sample-husk`.

- [ ] **Step 6: Verify static contract and HTML parsing**

```powershell
node --test test/render-contract.test.mjs
npm test
```

Expected: static contract and all pure tests PASS.

- [ ] **Step 7: Commit**

```powershell
git add openclaw-harness/src/public/index.html openclaw-harness/src/public/favicon.svg openclaw-harness/src/public/assets openclaw-harness/src/public/styles/tokens.css openclaw-harness/src/public/styles/base.css openclaw-harness/test/render-contract.test.mjs
git commit -m "feat: establish living archive visual system"
```

---

### Task 7: Render the living structure, memories, and tendrils

**Files:**
- Create: `openclaw-harness/src/public/scripts/render/memory-form.js`
- Create: `openclaw-harness/src/public/scripts/render/tendril.js`
- Create: `openclaw-harness/src/public/scripts/render/living-structure.js`
- Create: `openclaw-harness/src/public/styles/archive-stage.css`
- Modify: `openclaw-harness/test/layout.test.mjs`

**Interfaces:**
- Produces: `memoryFormPath(shape, size): string`.
- Produces: `memoryAriaLabel(memory): string`.
- Produces: `tendrilClass(relationship, state): string`.
- Produces: `createLivingStructure(svgElement, { onSelect, onTrace }): LivingStructureController`.
- Controller methods: `render(snapshot, layout, viewState)`, `setInteractive(enabled)`, `destroy()`.

- [ ] **Step 1: Add failing geometry-contract tests**

Assert that leaf, pearl, and mineral paths are closed; husk paths are open; all numeric values are finite; and `memoryAriaLabel` contains statement, category, lifecycle, confidence percentage, and recall count.

- [ ] **Step 2: Run the focused test and confirm failure**

```powershell
node --test test/layout.test.mjs
```

Expected: FAIL because the render geometry exports do not exist.

- [ ] **Step 3: Implement form and tendril primitives**

Use shape-first category encoding. Each `.memory-form` group contains a hit target, material body, edge condition, category mark, and focus ring. Each `.tendril` contains a quiet base path and a separate pulse path. Use D3 keyed joins with memory ID and relationship ID; never clear `archiveWorld.innerHTML` during updates.

- [ ] **Step 4: Implement the archive controller**

Create stable layers in this order: `skeleton`, `membranes`, `tendrils`, `memories`, `effects`, `annotations`. Render an incomplete brass root crown and three main branches before data joins. Keep excluded memories in the DOM with `.is-quiet`; remove only memories absent from the normalized graph.

- [ ] **Step 5: Style the stage as one organism**

Implement one shared lighting direction from upper left. Preference leaves use moss with lichen edges, persona pearls use clay rose and bone highlights, system minerals use mineral blue with brass facets. Fading forms use weathered taupe, dry edges, lower saturation, and less movement. Do not use drop-shadow glows larger than four pixels.

- [ ] **Step 6: Verify pure tests and inspect one static render**

```powershell
npm test
```

Expected: all tests PASS. Open the page with temporary fixture injection only through browser dev tools; verify the SVG tree retains keyed nodes after calling `render` twice.

- [ ] **Step 7: Commit**

```powershell
git add openclaw-harness/src/public/scripts/render openclaw-harness/src/public/styles/archive-stage.css openclaw-harness/test/layout.test.mjs
git commit -m "feat: render living archive organism"
```

---

### Task 8: Build the observation margin and sediment timeline

**Files:**
- Create: `openclaw-harness/src/public/scripts/render/annotations.js`
- Create: `openclaw-harness/src/public/scripts/render/timeline.js`
- Create: `openclaw-harness/src/public/styles/observation-margin.css`
- Create: `openclaw-harness/src/public/styles/sediment-timeline.css`
- Modify: `openclaw-harness/test/narrative.test.mjs`

**Interfaces:**
- Produces: `renderObservation(root, state, narrative): void`.
- Produces: `renderCompanionList(root, memories, selectedId): void`.
- Produces: `deriveVitalSigns(state): { memories, relationships, recalls }`.
- Produces: `eventGlyph(event): "seed"|"pulse"|"scar"|"husk"|"settled"`.
- Produces: `createTimeline(root, { onReplay }): TimelineController` with `render(events)` and `destroy()`.

- [ ] **Step 1: Add failing annotation and glyph tests**

Assert exact event glyph mapping, counts derived from visible state, plain-language labels, and event timestamps formatted without throwing on invalid input. Define `recalls` as the deduplicated count of `injected` and `influenced` events retained in the current event buffer; do not infer recent recalls from `total_turns`.

- [ ] **Step 2: Run and confirm failure**

```powershell
node --test test/narrative.test.mjs
```

Expected: FAIL because annotation and timeline exports do not exist.

- [ ] **Step 3: Implement observation rendering**

The default heading is `A living record of what endures.` Selected memory details show statement first, followed by category, vitality, confidence, recalls, and influence. Missing metrics display `Unavailable` beside a disconnected-joint symbol. Do not render cards around each measurement.

- [ ] **Step 4: Implement timeline rendering**

Render newest events at the right. Cap visible desktop glyphs at 24 and mobile glyphs at 12, but retain an accessible event list. Replay buttons must dispatch visual replay only and must never call a POST endpoint.

- [ ] **Step 5: Style editorial annotations and sediment**

Use botanical leader lines, display typography for narrative headings, body typography for explanations, and mono only for timestamps and numerical precision. The bottom timeline must look like material accumulating at the edge of the scene, not a toolbar.

- [ ] **Step 6: Verify tests**

```powershell
npm test
```

Expected: all tests PASS.

- [ ] **Step 7: Commit**

```powershell
git add openclaw-harness/src/public/scripts/render/annotations.js openclaw-harness/src/public/scripts/render/timeline.js openclaw-harness/src/public/styles/observation-margin.css openclaw-harness/src/public/styles/sediment-timeline.css openclaw-harness/test/narrative.test.mjs
git commit -m "feat: add archive observation and sediment history"
```

---

### Task 9: Add meaningful opening, lifecycle, and ambient motion

**Files:**
- Create: `openclaw-harness/src/public/scripts/motion/choreographer.js`
- Create: `openclaw-harness/src/public/scripts/motion/lifecycle-transitions.js`
- Create: `openclaw-harness/src/public/scripts/motion/ambient-motion.js`
- Create: `openclaw-harness/src/public/styles/motion.css`
- Modify: `openclaw-harness/test/narrative.test.mjs`

**Interfaces:**
- Produces: `createChoreographer({ root, store, reducedMotion }): Choreographer`.
- Choreographer methods: `playOpening(memoryId)`, `enqueue(decision)`, `replay(event)`, `cancel()`, `destroy()`.
- Produces: `transitionForPhase(phase, reducedMotion): TransitionSpec`.
- Produces: `createAmbientMotion(root, store): { start, stop, destroy }`.

- [ ] **Step 1: Add failing transition-spec tests**

Assert opening phases end at `2000`, `5000`, `8000`, and `10000` milliseconds; event priority order matches Task 4; reduced motion yields duration at most `180ms`; and concurrent traveling pulses are capped at three.

- [ ] **Step 2: Run and confirm failure**

```powershell
node --test test/narrative.test.mjs
```

Expected: FAIL because transition specs do not exist.

- [ ] **Step 3: Implement a single-owner choreography queue**

Only `choreographer.js` may start lifecycle animation. It must cancel stale work through `AbortController`, ignore polling updates while the same event is playing, and mark the opening complete even if the user interacts during it. User input may shorten the opening but never be blocked.

- [ ] **Step 4: Implement lifecycle transitions**

Use CSS classes and SVG stroke-dash transitions for arrival, rooting, recall, revision, decay, and prune. Revision must leave `.revision-scar` in the settled DOM. Prune must animate toward the corresponding sediment glyph. Reduced motion applies state classes immediately after a short dissolve.

- [ ] **Step 5: Implement ambient ownership**

Start breathing only when document visibility is `visible`, motion is enabled, and the archive has data. Stop on hidden, reduced motion, empty, fatal error, or `destroy`. Use CSS variables to offset memory phases; do not create a `requestAnimationFrame` loop for basic breathing.

- [ ] **Step 6: Verify tests**

```powershell
npm test
```

Expected: transition and unit tests PASS.

- [ ] **Step 7: Commit**

```powershell
git add openclaw-harness/src/public/scripts/motion openclaw-harness/src/public/styles/motion.css openclaw-harness/test/narrative.test.mjs
git commit -m "feat: choreograph the memory lifecycle"
```

---

### Task 10: Add focus, trace, navigation, filters, and archive controls

**Files:**
- Create: `openclaw-harness/src/public/scripts/interactions/archive-navigation.js`
- Create: `openclaw-harness/src/public/scripts/interactions/memory-focus.js`
- Create: `openclaw-harness/src/public/scripts/interactions/archive-menu.js`
- Modify: `openclaw-harness/src/public/styles/base.css`
- Modify: `openclaw-harness/test/archive-store.test.mjs`

**Interfaces:**
- Produces: `createArchiveNavigation(svg, world, store): NavigationController`.
- Produces: `createMemoryFocus(stage, store): FocusController`.
- Produces: `createArchiveMenu(dialog, store, callbacks): MenuController`.
- Navigation controller methods: `reset()`, `focusBounds(bounds)`, `destroy()`.
- Menu callbacks: `onUserChange`, `onExport`, `onReplayOpening`, `onRetry`.

- [ ] **Step 1: Add failing interaction-state tests**

Assert single-click focus, explicit trace action, double-click trace, Escape priority `trace → focus → menu`, category and lifecycle filter behavior, motion persistence, and reset behavior. Filters must quiet excluded memories instead of removing them from store state.

- [ ] **Step 2: Run and confirm failure**

```powershell
node --test test/archive-store.test.mjs
```

Expected: FAIL on the new interaction reducer expectations.

- [ ] **Step 3: Implement D3 zoom without node dragging**

Attach zoom only to `archiveSvg`, ignore wheel events originating outside `archiveStage`, constrain scale to `0.7..3.2`, and dispatch the transform to the store. Do not attach any drag behavior to `.memory-form`.

- [ ] **Step 4: Implement pointer and keyboard focus**

Enter or Space selects a focused memory, `T` starts trace for the selected memory, and Escape unwinds the active layer. Related memories and paths receive `.is-related`; unrelated content receives `.is-quiet`, never blur.

- [ ] **Step 5: Implement the archive menu**

Include labeled controls for user ID, three category filters, lifecycle filters `vivid`, `stable`, `fading`, motion toggle, replay opening, reset view, export JSON, retry, and diagnostics disclosure. Persist only user ID and motion preference in local storage.

- [ ] **Step 6: Verify tests**

```powershell
npm test
```

Expected: all store and unit tests PASS.

- [ ] **Step 7: Commit**

```powershell
git add openclaw-harness/src/public/scripts/interactions openclaw-harness/src/public/styles/base.css openclaw-harness/test/archive-store.test.mjs
git commit -m "feat: add archive exploration controls"
```

---

### Task 11: Orchestrate startup, live updates, and designed failure states

**Files:**
- Create: `openclaw-harness/src/public/scripts/main.js`
- Modify: `openclaw-harness/src/public/scripts/api.js`
- Modify: `openclaw-harness/src/public/styles/base.css`
- Modify: `openclaw-harness/test/api.test.mjs`

**Interfaces:**
- Produces: `bootstrapArchive(): Promise<ArchiveApplication>`.
- `ArchiveApplication` exposes `refresh({ structural })`, `changeUser(userId)`, and `destroy()` for browser tests.
- Publishes the controller as `window.__mnemArchive` only in non-production diagnostics; do not expose mutable store internals.

- [ ] **Step 1: Add failing polling and recovery tests**

Using fake fetch responses, assert initial graph/metrics/events concurrency, a 15-second regular poll interval, event `since` based on the newest processed timestamp, no opening replay, selection/zoom preservation, and abort of the previous user's requests after user change.

- [ ] **Step 2: Run and confirm failure**

```powershell
node --test test/api.test.mjs
```

Expected: FAIL on orchestration helper expectations.

- [ ] **Step 3: Implement startup orchestration**

Resolve user ID, create the store, create render/motion/interaction controllers, load a snapshot, normalize it, compute layout, render, then start polling. For `demo-brain` only, call `/api/demo/status`; if fewer than eight beliefs exist, POST `/api/demo/seed` with `{ "force": false }` once and reload.

- [ ] **Step 4: Implement stable live updates**

Structural changes are determined by sorted memory IDs plus relationship IDs. Metric-only updates render annotations only. Event bursts go through `selectNarrative`. Existing layout positions remain stable by deterministic ID; do not use current DOM coordinates as source data.

- [ ] **Step 5: Implement state views**

Map status to one of `loading`, `ready`, `empty`, `filtered-empty`, `degraded`, or `error`. Loading shows the dormant skeleton. Empty shows the waiting root crown. Degraded keeps the graph and marks missing observations. Error shows the disconnected brass joint and Retry. All state messages use plain language, while diagnostics contain endpoint errors.

- [ ] **Step 6: Verify tests**

```powershell
npm test
```

Expected: all unit tests PASS.

- [ ] **Step 7: Commit**

```powershell
git add openclaw-harness/src/public/scripts/main.js openclaw-harness/src/public/scripts/api.js openclaw-harness/src/public/styles/base.css openclaw-harness/test/api.test.mjs
git commit -m "feat: connect living archive to live memory data"
```

---

### Task 12: Complete responsiveness and accessibility

**Files:**
- Create: `openclaw-harness/src/public/styles/responsive.css`
- Modify: `openclaw-harness/src/public/styles/motion.css`
- Modify: `openclaw-harness/src/public/scripts/render/annotations.js`
- Modify: `openclaw-harness/src/public/scripts/interactions/archive-navigation.js`
- Modify: `openclaw-harness/test/render-contract.test.mjs`

**Interfaces:**
- Preserves all earlier renderer/controller signatures.
- Produces desktop `>=1100px`, tablet `700..1099px`, and mobile `<700px` layouts.

- [ ] **Step 1: Add failing accessibility/static tests**

Assert the presence of a skip link, live status, labeled menu/dialog, accessible companion list, observation sheet heading, `prefers-reduced-motion`, three exact responsive breakpoints, and 44-pixel mobile target rules.

- [ ] **Step 2: Run and confirm failure**

```powershell
node --test test/render-contract.test.mjs
```

Expected: FAIL on responsive and accessibility requirements.

- [ ] **Step 3: Implement responsive composition**

Desktop uses stage plus observation margin. Tablet uses archive above an editorial band. Mobile gives the archive the initial viewport and uses a native-feeling pull-up observation sheet. Keep the timeline attached to the bottom in all modes. On touch devices, permit page scroll when the gesture begins outside the archive.

- [ ] **Step 4: Implement complete keyboard and screen-reader behavior**

Add a skip link to `archiveStage`. Maintain a sorted companion list of memory buttons. Announce only initial readiness, selected-memory changes, featured lifecycle events, and error recovery. Tooltips may mirror companion content but cannot contain unique information.

- [ ] **Step 5: Finish reduced-motion behavior**

Under reduced motion, stop breathing, drifting, stroke travel, scale growth, and smooth zoom. Use a maximum `180ms` dissolve and static revision scars. Confirm that replay still selects and explains the event.

- [ ] **Step 6: Verify tests**

```powershell
npm test
```

Expected: all static and unit tests PASS.

- [ ] **Step 7: Commit**

```powershell
git add openclaw-harness/src/public/styles/responsive.css openclaw-harness/src/public/styles/motion.css openclaw-harness/src/public/scripts/render/annotations.js openclaw-harness/src/public/scripts/interactions/archive-navigation.js openclaw-harness/test/render-contract.test.mjs
git commit -m "feat: complete accessible responsive archive"
```

---

### Task 13: Replace browser verification with Living Archive checks

**Files:**
- Replace: `openclaw-harness/scripts/check-visualizer.mjs`
- Modify: `openclaw-harness/test/fixtures/archive-fixture.mjs`

**Interfaces:**
- Command: `npm run test:visualizer`.
- Default behavior: start an ephemeral local Express fixture server, serve `src/public` and vendored D3, and answer the visualizer APIs from `archive-fixture.mjs`.
- Optional environment: `VISUALIZER_URL`; when set, skip the fixture server and verify that running deployment instead.
- Exit `0` only when semantic, interaction, responsive, reduced-motion, and console checks pass.

- [ ] **Step 1: Replace old assertions with a failing Living Archive smoke script**

The script must import Express, Playwright, `node:path`, `node:url`, and the archive fixtures. When `VISUALIZER_URL` is absent, listen on port `0`, serve `src/public`, mount D3 at `/vendor/d3`, and implement fixture responses for graph, metrics, events, whoami, default-user, and demo status. Close both Chromium and the fixture server in `finally`.

Launch Chromium, capture console and page errors, load the selected URL, and assert:

- Page title contains `MnemAgent` and `Living Archive`.
- `#archiveSvg`, `#observationMargin`, and `#sedimentTimeline` are visible.
- At least one `.memory-form` and one `.tendril` exist.
- No `.graph-panel`, `.stat-card`, `#eventFeed`, `canvas`, or Chart.js script exists.
- Selecting a memory updates `#memoryDetail`.
- Trace mode marks related forms or tendrils.
- Escape exits trace mode.
- Archive menu opens, filters quiet forms, and Clear filters restores them.
- Reduced motion removes active ambient animation.
- At `390 × 844`, the observation sheet is available and controls meet 44-pixel minimums.
- No console error or uncaught page error occurs.

- [ ] **Step 2: Run against the assembled app with fixture APIs**

Run:

```powershell
cd openclaw-harness
npm run test:visualizer
```

Expected: PASS if Tasks 1–12 satisfy the browser contract; otherwise FAIL with the first unmet Living Archive selector or behavior.

- [ ] **Step 3: Fix only issues exposed by the smoke script**

Keep fixes inside the responsible modules. Do not add test-only classes or bypass animations with arbitrary sleeps. Expose settled states through `data-phase`, `data-status`, and `aria-expanded` attributes so the script can wait deterministically.

- [ ] **Step 4: Run all browser and unit checks**

```powershell
npm run test:all
```

Expected: unit suite PASS; smoke script reports desktop and mobile checks PASS; console error count is zero.

Then start the documented demo stack and run:

```powershell
$env:VISUALIZER_URL='http://127.0.0.1:3000/?user=demo-brain'
npm run test:visualizer
Remove-Item Env:VISUALIZER_URL
```

Expected: the same browser checks PASS against live API data.

- [ ] **Step 5: Commit**

```powershell
git add openclaw-harness/scripts/check-visualizer.mjs openclaw-harness/test/fixtures/archive-fixture.mjs openclaw-harness/src/public
git commit -m "test: verify living archive experience"
```

---

### Task 14: Remove obsolete visualizer assets and perform final visual QA

**Files:**
- Delete: `openclaw-harness/src/public/visualizer.css`
- Delete: `openclaw-harness/src/public/mnemagent-logo-square.png`
- Replace: `docs/assets/visualizer-snapshot.png`

**Interfaces:**
- Preserves all public APIs and URL behavior.
- Produces the final README snapshot at `1440 × 1080` using `demo-brain`.

- [ ] **Step 1: Prove obsolete assets are unreferenced**

```powershell
rg -n "visualizer\.css|mnemagent-logo-square|chart\.js|catChart|ucbChart|graph-panel|eventFeed" openclaw-harness README.md docs -g '!docs/superpowers/**'
```

Expected: only historical prose or no results; no runtime HTML, CSS, or JS reference remains.

- [ ] **Step 2: Delete obsolete runtime files**

```powershell
git rm openclaw-harness/src/public/visualizer.css openclaw-harness/src/public/mnemagent-logo-square.png
```

- [ ] **Step 3: Run full automated verification**

```powershell
cd openclaw-harness
npm run test:all
cd ..
python -m pytest tests -q
```

Expected: visualizer unit and browser checks PASS; Python test suite PASS.

- [ ] **Step 4: Perform the whole-image review at four states**

Inspect at `1440 × 1080`, `1280 × 800`, `768 × 1024`, and `390 × 844`. Review default archive, selected memory, revision event, and empty archive. Reject the result if any of these occur:

- The observation margin competes with the archive.
- Individual sections read as cards.
- Brass resembles neon.
- The timeline resembles a toolbar or terminal.
- Selected focus hides the whole organism.
- Organic decoration reduces label legibility.
- Mobile opens on controls instead of the archive.

- [ ] **Step 5: Capture the final snapshot**

Use Playwright after the archive reaches `data-status="ready"` and `data-phase="ambient"`. Set viewport `1440 × 1080`, hide only the pointer, and write the screenshot directly to `docs/assets/visualizer-snapshot.png`. Do not crop away the header, observation margin, or sediment timeline; the screenshot must prove the whole composition.

- [ ] **Step 6: Run final diff and repository checks**

```powershell
git diff --check
git status --short
git diff --stat
```

Expected: no whitespace errors; only intended visualizer, test, package, server, and snapshot changes remain.

- [ ] **Step 7: Commit**

```powershell
git add openclaw-harness docs/assets/visualizer-snapshot.png
git commit -m "feat: complete living archive visualizer redesign"
```

---

## Final Acceptance Checklist

- [ ] The old visual design is absent rather than restyled.
- [ ] The page reads as one continuous illustrated scene.
- [ ] A first-time viewer can identify memories, relationships, recall, revision, and fading.
- [ ] Living moss and lichen green are both visible but serve distinct roles.
- [ ] Antique brass reads as aged material, not emitted light.
- [ ] The opening uses real data and never blocks interaction.
- [ ] Polling preserves opening state, focus, trace, zoom, and positions.
- [ ] Memory category remains understandable without color.
- [ ] Reduced motion retains every informational state.
- [ ] Empty, filtered-empty, degraded, and fatal-error states look intentional.
- [ ] The 62-memory, 405-relationship demo remains responsive.
- [ ] Keyboard, pointer, and touch exploration all work.
- [ ] The browser console remains clean.
- [ ] `npm run test:all` passes.
- [ ] `python -m pytest tests -q` passes.
- [ ] The final README snapshot shows the whole composition.
