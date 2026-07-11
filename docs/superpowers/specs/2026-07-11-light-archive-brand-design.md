# Light archive brand design

## Goal

Use `docs/assets/logo.jpg` as the MnemAgent brand image, make the living
archive feel like an illuminated herbarium rather than a dark console, and add
a direct GitHub path without changing the archive interactions.

## Header

- The brand link uses `logo.jpg` as a compact square thumbnail and retains the
  `MnemAgent` wordmark so the product remains identifiable at small sizes.
- The thumbnail is cropped with `object-fit: cover`, uses a restrained rounded
  frame, and has descriptive alternative text.
- The visible connection-status output is removed. Existing loading and error
  feedback stays available through the screen-reader live region in the stage.
- A labelled GitHub icon link opens `https://github.com/crankysmh47/MnemAgent`
  in a new tab with `rel="noopener noreferrer"`. It sits immediately before
  the Archive controls button and has a visible keyboard focus state.

## Light archive palette

- Page and stage: bone white and warm parchment.
- Observation panel and timeline: slightly deeper parchment to preserve the
  existing layout hierarchy.
- Text: dark charcoal for readable contrast.
- Tree: moss, lichen, brass, clay, and mineral-blue memory forms retain their
  current semantic colors, with stronger outlines where the light surface needs
  them.
- Controls and modal: parchment surfaces with charcoal text; no bright white
  glare and no neon treatment.

## Documentation imagery

- The README logo uses `docs/assets/logo.jpg` with MnemAgent-specific alt text.
- The visualizer snapshot is regenerated from `?user=demo-brain` after the
  light theme is applied.
- README copy identifies the screenshot as the live demo-brain archive.

## Verification

- Extend the visualizer browser check to require the official logo asset, one
  labelled GitHub repository link, and no visible live-state output in the
  header.
- Run the visualizer harness against the live `demo-brain` URL to create the
  README snapshot, asserting no console errors.
- Confirm the README contains the new logo and snapshot paths, then run the
  existing Node test suite and visualizer check.
