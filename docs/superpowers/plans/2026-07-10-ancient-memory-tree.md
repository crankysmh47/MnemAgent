# Ancient Memory Tree Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the radial archive cluster into one deterministic ancient memory tree and eliminate hover-induced SVG positioning failures.

**Architecture:** A focused tree-geometry module owns root, trunk, branch, and curve interpolation primitives. The existing layout assigns normalized memories to stable positions along category branches and returns botanical skeleton geometry; the renderer draws that geometry and separates permanent placement transforms from interaction transforms.

**Tech Stack:** Browser-native ES modules, D3 7 SVG rendering, CSS transforms and keyframes, Node test runner, Playwright browser smoke checks.

## Global Constraints

- Preserve the charcoal, parchment, brass, moss, lichen, clay, and mineral-blue palette.
- Use no neon or hard-tech visual treatment.
- Do not change the backend or API contracts.
- Keep memory buttons keyboard accessible and touch targets at least 44 pixels.
- Reduced-motion mode must remove sway, lift, traveling pulses, and growth transitions.
- The same dataset and viewport must produce deterministic layout output.

---

### Task 1: Tree Geometry Primitives

**Files:**
- Create: `openclaw-harness/src/public/scripts/tree-geometry.js`
- Modify: `openclaw-harness/test/layout.test.mjs`

**Interfaces:**
- Produces: `createTreeSkeleton({width, height}) -> {root, trunk, branches, crown}`
- Produces: `cubicPoint(curve, t) -> {x, y}`
- Produces: `curvePath(curve) -> string`

- [ ] **Step 1: Write the failing geometry tests**

```js
import { createTreeSkeleton, cubicPoint, curvePath } from '../src/public/scripts/tree-geometry.js';

test('tree skeleton is rooted and branches upward into three category families', () => {
  const tree = createTreeSkeleton({ width: 1000, height: 720 });
  assert.ok(tree.root.y > tree.crown.y);
  assert.deepEqual([...new Set(tree.branches.map(branch => branch.category))].sort(), ['persona','preference','system_state']);
  assert.ok(tree.branches.every(branch => branch.end.y < tree.root.y));
  assert.ok(tree.branches.every(branch => /^M[-+\d.e, ]+ C[-+\d.e, ]+$/.test(curvePath(branch))));
});

test('cubic interpolation keeps branch endpoints exact', () => {
  const curve = { start:{x:0,y:10}, control1:{x:3,y:5}, control2:{x:7,y:2}, end:{x:10,y:0} };
  assert.deepEqual(cubicPoint(curve, 0), curve.start);
  assert.deepEqual(cubicPoint(curve, 1), curve.end);
});
```

- [ ] **Step 2: Run tests and confirm RED**

Run: `node --test test/layout.test.mjs`

Expected: FAIL because `tree-geometry.js` does not exist.

- [ ] **Step 3: Implement deterministic tree primitives**

Create viewport-scaled roots, a tapered trunk centerline, and at least two asymmetric cubic branches per category. Implement the standard cubic Bézier equation:

```js
export function cubicPoint(curve, t) {
  const u = 1 - t;
  return {
    x: u*u*u*curve.start.x + 3*u*u*t*curve.control1.x + 3*u*t*t*curve.control2.x + t*t*t*curve.end.x,
    y: u*u*u*curve.start.y + 3*u*u*t*curve.control1.y + 3*u*t*t*curve.control2.y + t*t*t*curve.end.y,
  };
}
```

- [ ] **Step 4: Run tests and confirm GREEN**

Run: `node --test test/layout.test.mjs`

Expected: all layout tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add openclaw-harness/src/public/scripts/tree-geometry.js openclaw-harness/test/layout.test.mjs
git commit -m "feat: add deterministic memory tree geometry"
```

### Task 2: Branch-Aware Memory Layout

**Files:**
- Modify: `openclaw-harness/src/public/scripts/layout.js`
- Modify: `openclaw-harness/test/layout.test.mjs`

**Interfaces:**
- Consumes: `createTreeSkeleton`, `cubicPoint`
- Produces: existing `computeArchiveLayout(...)` plus `tree` geometry and node fields `branchId`, `branchT`, `angle`

- [ ] **Step 1: Write failing silhouette and assignment tests**

```js
test('memories grow along category branches instead of a radial cluster', () => {
  const layout = computeArchiveLayout(Array.from({length:62}, (_,i) => ({
    id:`tree-${i}`, category:['preference','persona','system_state'][i%3], vitality:.5 + (i%5)/10,
  })), [], {width:1000,height:720});
  assert.ok(layout.tree.root.y > layout.tree.crown.y);
  assert.ok(layout.nodes.every(node => node.branchId && Number.isFinite(node.branchT)));
  assert.ok(layout.nodes.every(node => node.y < layout.tree.root.y));
  assert.ok(Math.max(...layout.nodes.map(node => node.y)) - Math.min(...layout.nodes.map(node => node.y)) > 260);
});
```

- [ ] **Step 2: Run tests and confirm RED**

Run: `node --test test/layout.test.mjs`

Expected: FAIL because layout has no `tree`, `branchId`, or `branchT`.

- [ ] **Step 3: Assign memories to stable branch positions**

Sort memories by ID within each category, distribute them across that category's branches, derive `t` from rank with deterministic ID jitter, and offset perpendicular to the branch by no more than 18 pixels. Use vitality for visible radius, not radial distance. Route relationship paths between the resulting positions and return `{nodes, paths, groves, bounds, center, tree}`.

- [ ] **Step 4: Preserve bounds and permutation stability**

Clamp using each node radius. Keep category/branch assignment derived from stable IDs, never input array order. Re-run crowded, reversed-input, missing-ID, and finite-path assertions.

- [ ] **Step 5: Run tests and confirm GREEN**

Run: `node --test test/layout.test.mjs`

Expected: all layout tests PASS.

- [ ] **Step 6: Commit**

```powershell
git add openclaw-harness/src/public/scripts/layout.js openclaw-harness/test/layout.test.mjs
git commit -m "feat: grow memories along tree branches"
```

### Task 3: Botanical Renderer and Stable Hover Motion

**Files:**
- Modify: `openclaw-harness/src/public/scripts/render/living-structure.js`
- Modify: `openclaw-harness/src/public/scripts/render/memory-form.js`
- Modify: `openclaw-harness/src/public/styles/archive-stage.css`
- Modify: `openclaw-harness/src/public/styles/motion.css`
- Modify: `openclaw-harness/test/render-contract.test.mjs`
- Modify: `openclaw-harness/test/render-geometry.test.mjs`

**Interfaces:**
- Consumes: `layout.tree`, `layout.nodes`, `layout.paths`
- Produces: outer `.memory-form` placement group containing inner `.memory-interaction`
- Produces: SVG layers `.roots`, `.trunk`, `.branches`, `.tendrils`, `.memories`, `.effects`, `.annotations`

- [ ] **Step 1: Write failing structure tests**

```js
test('memory interaction motion is isolated from placement transforms', () => {
  assert.match(rendererSource, /class[^\n]+memory-interaction/);
  assert.match(stageCss, /\.memory-form:hover \.memory-interaction/);
  assert.doesNotMatch(stageCss, /\.memory-form:hover[^\{]*\{[^}]*transform:/s);
});

test('renderer exposes botanical structure layers', () => {
  for (const layer of ['roots','trunk','branches']) assert.match(rendererSource, new RegExp(`['\"]${layer}['\"]`));
});
```

- [ ] **Step 2: Run tests and confirm RED**

Run: `node --test test/render-contract.test.mjs test/render-geometry.test.mjs`

Expected: FAIL because the inner interaction group and botanical layers do not exist.

- [ ] **Step 3: Render data-driven roots, trunk, and branches**

Bind `layout.tree` paths to their dedicated layers. Use thicker, low-contrast brass/moss strokes for trunk and primary limbs, finer lichen strokes for branchlets, and preserve relationship veins above branches but below memories.

- [ ] **Step 4: Nest interaction geometry**

On enter, append `.memory-interaction` inside `.memory-form`; append body and focus ring to the inner group. Keep D3 `translate(x,y)` only on `.memory-form`. Apply category-specific rotation to the inner group through a CSS custom property or SVG transform that does not overwrite placement.

- [ ] **Step 5: Replace radial-node styling with botanical forms**

Leaves receive asymmetrical veins, persona forms become seed pods/fruit, and system state becomes mineral bark growth. At rest, memory forms use subtle category tone variation and brass edge highlights. Selected and related states strengthen the connected branch without introducing glow.

- [ ] **Step 6: Fix hover and lifecycle motion**

Use selectors shaped like:

```css
.memory-interaction { transition: transform 220ms var(--ease-organic), filter 220ms var(--ease-organic); }
.memory-form:hover .memory-interaction,
.memory-form:focus-visible .memory-interaction { transform: rotate(var(--memory-tilt)) translateY(-3px) scale(1.08); }
```

No hover/focus/selection rule may assign `transform` to `.memory-form`. Reduced-motion removes the transition and transform.

- [ ] **Step 7: Run tests and confirm GREEN**

Run: `node --test test/render-contract.test.mjs test/render-geometry.test.mjs`

Expected: all renderer tests PASS.

- [ ] **Step 8: Commit**

```powershell
git add openclaw-harness/src/public/scripts/render/living-structure.js openclaw-harness/src/public/scripts/render/memory-form.js openclaw-harness/src/public/styles/archive-stage.css openclaw-harness/src/public/styles/motion.css openclaw-harness/test/render-contract.test.mjs openclaw-harness/test/render-geometry.test.mjs
git commit -m "feat: render the archive as an ancient memory tree"
```

### Task 4: Integration, Responsive Tuning, and Live Verification

**Files:**
- Modify: `openclaw-harness/src/public/scripts/main.js`
- Modify: `openclaw-harness/src/public/styles/responsive.css`
- Modify: `openclaw-harness/scripts/check-visualizer.mjs`
- Modify: `openclaw-harness/test/main.test.mjs`

**Interfaces:**
- Consumes: completed tree layout and renderer
- Produces: stable desktop, tablet, mobile, selected, filtered, and reduced-motion experiences

- [ ] **Step 1: Extend the smoke assertions before production changes**

Require `.trunk path`, at least six `.branch` paths, 62 live `.memory-form` groups, matching `.memory-interaction` groups, at most 96 tendrils, meaningful labels, and no console errors. Add an assertion that the outer memory `transform` attribute is identical before and during hover.

- [ ] **Step 2: Run smoke test and confirm RED**

Run: `npm run test:visualizer`

Expected: FAIL because botanical layers and nested interaction groups are absent.

- [ ] **Step 3: Tune viewport composition**

Desktop uses a broad crown and visible root base. Tablet uses a taller, slightly narrower crown above the observation section. Mobile uses a tall tree with minimum 44-pixel interactive groups and the observation sheet above the timeline. Preserve the existing relationship cap and filters.

- [ ] **Step 4: Run the complete automated suite**

Run: `npm test && npm run test:visualizer`

Expected: all unit tests PASS, visualizer report has no console errors, and the old graph implementation remains absent.

- [ ] **Step 5: Verify the live 62-memory archive in the in-app browser**

At `http://127.0.0.1:3100/?user=demo-brain`, verify the tree silhouette, hover position stability, selected relationship path, filter restoration, readable observation detail, desktop composition, mobile composition, and reduced-motion state. Reload after each source edit before evaluating.

- [ ] **Step 6: Commit**

```powershell
git add openclaw-harness/src/public/scripts/main.js openclaw-harness/src/public/styles/responsive.css openclaw-harness/scripts/check-visualizer.mjs openclaw-harness/test/main.test.mjs
git commit -m "test: verify ancient memory tree experience"
```
