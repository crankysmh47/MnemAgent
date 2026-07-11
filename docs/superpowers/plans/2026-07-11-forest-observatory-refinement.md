# Forest Observatory Refinement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refine the Living Archive with a guaranteed loader turn, true ground-up reveal, centered MnemTree, continuous water, memory labels, archive-specific storytelling, falling leaves, creamy/sage styling, larger logo, and dappled light.

**Architecture:** Keep deterministic data transformations in pure ES modules and DOM/SVG effects in focused render or motion controllers. Extend existing geometry rather than translating the rendered world, and preserve the nested transform boundary that protects memory placement.

**Tech Stack:** Vanilla ES modules, D3 SVG rendering, CSS animations, Node test runner, Playwright smoke tests.

## Global Constraints

- Keep the current forest theme, interaction model, focus-chain transparency, and vine behavior.
- The loader remains visible for at least 1,400ms and the scene is hidden until it exits.
- Initial reveal proceeds ground-to-canopy; polling does not replay it.
- Memory labels contain only a statement of at most 110 characters.
- Tree centering uses geometry, never a CSS translation on `#archiveWorld`.
- Show at most two falling leaves; disable them under reduced motion.
- Water extensions fade before the observation panel and remain subordinate to the tree.
- All commits use `crankysmh47 <annankhan741@gmail.com>`.

---

### Task 1: Loading gate and ground-up reveal

**Files:**
- Create: `openclaw-harness/src/public/scripts/motion/loading-gate.js`
- Modify: `openclaw-harness/src/public/scripts/main.js`
- Modify: `openclaw-harness/src/public/scripts/motion/choreographer.js`
- Modify: `openclaw-harness/src/public/scripts/motion/lifecycle-transitions.js`
- Modify: `openclaw-harness/src/public/styles/motion.css`
- Test: `openclaw-harness/test/loading-gate.test.mjs`
- Test: `openclaw-harness/test/motion.test.mjs`

**Interfaces:**
- Produces: `createLoadingGate({ minimumMs, now, wait })` with `ready()` and `release()`; opening phases `opening-ground`, `opening-roots`, `opening-trunk`, `opening-branches`, `opening-bloom`, `opening-connections`, and `opening-settle`.

- [ ] Write a failing test using an injected clock that proves `release()` waits until both `ready()` and 1,400ms, including error readiness.
- [ ] Run `node --test test/loading-gate.test.mjs test/motion.test.mjs`; expect missing-module and missing-phase failures.
- [ ] Implement the gate as a small promise coordinator with no DOM dependency.
- [ ] Update `main.js` so initial rendering remains under `data-loading="true"`, all initial response states call `ready()`, and only the gate release hides the loader and starts the opening.
- [ ] Split the opening timing into ground 420ms, roots 360ms, trunk 420ms, branches 520ms, bloom 1,200ms, connections 360ms, settle 480ms.
- [ ] Add CSS initial-hidden rules under `data-opening="true"`; animate the current scene groups in phase order and rotate the seed leaf once per 1.4 seconds.
- [ ] Run focused tests and require all to pass.

### Task 2: Centered geometry and continuous water

**Files:**
- Modify: `openclaw-harness/src/public/scripts/tree-geometry.js`
- Modify: `openclaw-harness/src/public/scripts/render/forest-scene.js`
- Modify: `openclaw-harness/src/public/styles/archive-stage.css`
- Test: `openclaw-harness/test/layout.test.mjs`
- Test: `openclaw-harness/test/render-contract.test.mjs`

**Interfaces:**
- Produces: shared tree center near `0.55 * width`; `.forest-water-wash` paths spanning both edges with low-opacity gradients.

- [ ] Add failing geometry assertions for the root near 55% width, finite paths, and bounded memory nodes at 1,000px and 390px widths.
- [ ] Add a failing render contract requiring two edge water washes and no `#archiveWorld` translation.
- [ ] Update the skeleton’s center constant and derived branch/root control points so every dependent path moves coherently.
- [ ] Extend `renderForestScene` with left and right water washes that meet the main pool and terminate outside the SVG viewport.
- [ ] Add SVG gradient-backed styling below groundcover with opacity lower than `.forest-water`.
- [ ] Run layout and contract tests and require all to pass.

### Task 3: Memory statement labels

**Files:**
- Create: `openclaw-harness/src/public/scripts/render/memory-label.js`
- Modify: `openclaw-harness/src/public/scripts/render/living-structure.js`
- Modify: `openclaw-harness/src/public/styles/archive-stage.css`
- Test: `openclaw-harness/test/memory-label.test.mjs`
- Test: `openclaw-harness/test/render-contract.test.mjs`

**Interfaces:**
- Produces: `shortMemoryStatement(memory, maxLength = 110)` and `memoryLabelPosition(node, bounds, size)`; one `g.memory-hover-label` in the annotations layer.

- [ ] Write failing tests for statement fallback, semantic truncation, top/bottom flipping, and horizontal clamping.
- [ ] Implement the two pure helpers.
- [ ] Bind pointer-enter/leave and focus/blur on memory forms to render or clear a single label without changing `.memory-form` transforms.
- [ ] Render a rounded cream label with moss border, paper shadow, `pointer-events:none`, and a 160ms reveal.
- [ ] Run label and contract tests and require all to pass.

### Task 4: Agent-specific storyteller

**Files:**
- Modify: `openclaw-harness/src/public/scripts/narrative.js`
- Modify: `openclaw-harness/src/public/scripts/main.js`
- Modify: `openclaw-harness/src/public/scripts/render/annotations.js`
- Test: `openclaw-harness/test/narrative.test.mjs`

**Interfaces:**
- Produces: `archiveStory({ memories, relationships, events, selectedMemory, hoveredMemory })` returning `{ eyebrow, title, body, guidance }` with priority selection > hover > event > overview.

- [ ] Write failing tests for all four priority paths and deterministic repeated output.
- [ ] Implement category counts, average vitality, direct relationship counts, and stable copy variation selection from archive IDs.
- [ ] Track hovered memory ID locally in `main.js` without making graph layout depend on it.
- [ ] Render `guidance` as a secondary sentence and preserve selected-memory details beneath it.
- [ ] Run narrative and observation tests and require all to pass.

### Task 5: Restrained ambient leaves

**Files:**
- Create: `openclaw-harness/src/public/scripts/motion/falling-leaves.js`
- Modify: `openclaw-harness/src/public/scripts/main.js`
- Modify: `openclaw-harness/src/public/styles/motion.css`
- Test: `openclaw-harness/test/falling-leaves.test.mjs`

**Interfaces:**
- Produces: `createFallingLeaves({ root, reducedMotion, random, schedule })` with `start()`, `stop()`, `setVisible()`, and `destroy()`.

- [ ] Write failing fake-scheduler tests proving 7–12 second delays, a two-leaf cap, cleanup, visibility pause, and reduced-motion suppression.
- [ ] Implement the controller with injected scheduling and deterministic random input.
- [ ] Add transient `path.falling-leaf` nodes to the effects layer and remove them on animation end or fallback timeout.
- [ ] Start only after `OPENING_FINISHED`; connect document visibility, motion preference, and destroy lifecycle.
- [ ] Add gentle drift/rotation/fade keyframes with pointer and accessibility suppression.
- [ ] Run controller tests and require all to pass.

### Task 6: Cream, sage, light, panel, and logo polish

**Files:**
- Modify: `openclaw-harness/src/public/index.html`
- Modify: `openclaw-harness/src/public/styles/base.css`
- Modify: `openclaw-harness/src/public/styles/archive-stage.css`
- Modify: `openclaw-harness/src/public/styles/observation-margin.css`
- Modify: `openclaw-harness/src/public/styles/responsive.css`
- Modify: `openclaw-harness/src/public/styles/motion.css`
- Test: `openclaw-harness/test/render-contract.test.mjs`

**Interfaces:**
- Produces: two `.dappled-light` layers behind the SVG, 46px desktop logo/34px mobile logo, creamy stage, sage observation panel, and botanical panel-edge contour.

- [ ] Add failing static-contract assertions for light layers, palette selectors, logo sizes, panel tint, and reduced-motion light behavior.
- [ ] Add two decorative light elements inside the stage before the loader and SVG.
- [ ] Warm the stage background, tint the panel sage, recolor dividers, and add a subtle left-edge contour with a pseudo-element.
- [ ] Increase logo and minimally adjust header height while preserving mobile controls.
- [ ] Animate dappled light slower than vines and freeze it under reduced motion.
- [ ] Run contract tests and require all to pass.

### Task 7: Full visual and regression verification

**Files:**
- Modify: `openclaw-harness/scripts/check-visualizer.mjs`
- Update: `docs/assets/visualizer-snapshot.png` only if the final settled scene materially differs from the README image.

**Interfaces:**
- Consumes: the completed dashboard.
- Produces: browser evidence for loading, opening, centering, labels, narrative, water, ambient cleanup, responsive layout, and reduced motion.

- [ ] Extend the Playwright smoke test to measure loader visibility before 1,400ms, confirm ordered phases, hover a memory label, validate centered root geometry, inspect story copy, verify falling-leaf cap/cleanup, and check reduced motion.
- [ ] Run `npm run test:all`; require zero failures and zero console errors.
- [ ] Refresh `http://127.0.0.1:3100/?user=demo-brain`, inspect opening and settled screenshots, and interact with memories and vines.
- [ ] Run `git diff --check`, verify only intended files changed, commit with the configured user author, and push `main` to `origin`.
