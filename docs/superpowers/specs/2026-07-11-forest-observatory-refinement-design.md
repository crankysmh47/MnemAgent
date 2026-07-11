# Forest Observatory Refinement Design

## Purpose

Refine the Living Archive into a cohesive forest observatory that feels warmer, more centered, more specific to the current agent, and more deliberately alive. The MnemTree remains the visual and narrative focus. New motion and decoration must clarify or complete the composition rather than compete with memory nodes.

## Experience goals

- A reload begins from a genuinely empty scene and reveals the archive from the ground upward.
- The existing leaf spinner remains recognizable for at least one complete rotation.
- The tree reads as centered within the visual stage instead of leaning too far left.
- Every memory can reveal a short statement without opening the detail panel.
- The observation panel feels connected to the forest and describes the actual archive rather than repeating generic copy.
- Ambient motion remains sparse, calm, and accessible.

## Visual direction

The palette becomes warmer and creamier. Bone white remains the foundation, but the stage shifts toward cream parchment rather than neutral grey. The observation panel receives a pale sage tint, moss-tinted dividers, and a restrained brass accent. Dappled light provides the final unifying atmospheric layer: two broad, extremely faint warm patches move slowly across the stage and just reach the inside edge of the panel.

The panel must remain readable and restrained. It must not become a separate illustration. A subtle botanical contour may cross only the first few pixels of its left edge to connect observation to the archive.

The water must not end as a visibly cut-off central shape. Its main pool remains shallow beneath the tree, while low-opacity reflection washes continue horizontally beyond the stage edges. These extensions fade before the observation-panel boundary, never sit above panel content, and remain lighter than the roots, trunk, grass bank, and memory forms.

## Opening sequence

### Loader hold

- The loading overlay begins visible before archive data is requested.
- The scene behind it is visually empty; pre-rendered SVG layers cannot show through.
- The leaf spinner completes at least one full 1.4-second rotation before the overlay may leave.
- If data takes longer than 1.4 seconds, the spinner continues naturally until data is ready.
- Empty, degraded, and error responses still dismiss the overlay after the minimum hold; they cannot leave the interface blocked.
- Reduced-motion mode uses a 1.4-second quiet opacity pulse instead of rotation.

### Ground-up reveal

After both the minimum loader hold and the initial data request finish, the overlay fades and the scene reveals in this order:

1. cream atmosphere and ground shadow;
2. water, grassy bank, and moss;
3. roots;
4. trunk;
5. branches;
6. memory forms, one at a time in ground-to-canopy order;
7. relationship tendrils;
8. hanging vines, annotations, observation panel, and timeline;
9. sparse ambient falling leaves.

Elements must begin hidden rather than appearing once and being reset for animation. The opening runs only for the initial page load and explicit replay control. Fifteen-second background refreshes update silently.

The sequence should take approximately 3.4 seconds after the loader exits. Memory staggering may overlap slightly at high memory counts, but each memory must retain a perceptible individual entrance. The animation may never alter `.memory-form` placement transforms; entrance and interaction transforms remain on nested elements.

## Tree centering

Center the MnemTree within the available archive stage, independent of the observation panel. Shift the tree skeleton, branch families, root system, water, and ground composition approximately 5–7% of stage width to the right from their current position, then validate the perceived center at desktop and mobile sizes.

This must be implemented through shared layout/scene geometry. Do not apply a CSS translation to `#archiveWorld`, because that would desynchronize navigation, hit testing, labels, and computed paths. The final root should sit near the midpoint of the visible stage, while asymmetric canopy growth may remain organic.

## Memory hover labels

Every rendered memory form receives a compact label on pointer hover and keyboard focus, regardless of whether its material shape is a leaf, pearl, mineral, scar, or husk.

- Content: one short, human-readable memory statement only.
- Exclude confidence, lifecycle, source IDs, timestamps, and instructions.
- Maximum visible length: 110 characters, with a semantic ellipsis when truncated.
- Placement: above or beside the memory, automatically flipped and clamped inside stage bounds.
- Appearance: cream label, moss border, subtle paper shadow, compact body typography.
- Behavior: appear after roughly 160ms, disappear softly, remain pointer-inert, and never cover the selected memory.
- Accessibility: the existing full `aria-label` remains authoritative; keyboard focus triggers the same visible short label.

Only one memory label may be visible at a time.

## Observation panel

### Visual integration

- Use a pale sage-cream background distinct from, but related to, the stage.
- Replace neutral dividers with low-contrast moss dividers.
- Add one subtle botanical edge contour and allow dappled light to reach only the panel’s inner edge.
- Preserve the existing reading hierarchy and contrast.

### Agent-specific storyteller

Narrative copy is deterministic and derived from current archive state. It uses the following priority:

1. selected or traced memory;
2. hovered memory;
3. meaningful recent lifecycle event;
4. archive overview.

The archive overview describes actual dominant categories, memory vitality, relationship density, and recent activity. Selection copy explains the memory and its direct connections. Hover copy offers one brief interpretation without replacing the detailed selected-memory section. Event copy states what changed and why that change matters. First-time guidance appears as a secondary sentence rather than the headline.

Copy variations must be chosen deterministically from archive data so text does not flicker during re-renders. Generic defaults remain only for empty or unavailable data.

## Ambient falling leaves

- Start only after the opening sequence finishes.
- Emit one leaf every 7–12 seconds using a deterministic pseudo-random schedule.
- Show no more than two falling leaves at once.
- Originate within the upper canopy, drift diagonally, rotate gently, and fade before reaching the timeline or controls.
- Use the existing moss, lichen, clay, and brass-adjacent palette.
- Set `pointer-events: none` and `aria-hidden: true`.
- Pause when the document is hidden and disable completely under reduced motion or the archive motion toggle.
- Do not create persistent DOM growth; remove each leaf after its animation ends.

## Logo and header

Increase the desktop logo from 38px to 46px and adjust the header height only as much as needed to preserve vertical breathing room. Retain the circular crop, border, and current brand wordmark. Use approximately 34px on mobile. The logo must become easier to notice without becoming a competing focal point.

## Completion element: dappled light

Use two soft, blurred, low-opacity light patches as the finishing atmospheric element. Their movement should be slower than vine motion, with no sharp edges or bright highlights. They must sit behind all interactive SVG content and never reduce label or panel contrast. Reduced-motion mode displays them statically.

## State and component boundaries

- Loading readiness coordinates minimum hold time and initial data completion in `main.js` through a small, testable gate.
- Opening phase timing remains owned by the motion choreographer.
- Tree centering remains owned by tree/layout geometry and forest-scene geometry.
- Memory labels are rendered by the living-structure renderer in a dedicated SVG annotation layer.
- Storyteller copy remains a pure narrative function fed by archive state, hover state, and selection state.
- Falling leaves are owned by a small ambient controller with explicit `start`, `stop`, and `destroy` methods.
- Palette and panel integration remain CSS responsibilities.

## Error handling

- Loader gating always resolves for ready, degraded, empty, and error states.
- A failed narrative derivation falls back to the archive overview without affecting graph rendering.
- Missing or malformed memory statements produce a short “Memory details unavailable” label.
- Ambient leaf creation failures stop that decorative controller without affecting the archive.

## Accessibility and performance

- Respect both `prefers-reduced-motion` and the existing motion toggle.
- Do not announce decorative motion.
- Tooltips cannot trap focus or intercept pointer input.
- Use transforms and opacity for ambient animation.
- Cap transient leaves at two and reuse existing SVG/CSS primitives.
- Keep all existing keyboard navigation and focus semantics.

## Verification

Automated tests must prove:

- the loader cannot dismiss before 1.4 seconds and cannot become stuck after failure;
- the opening sequence uses current scene layers and reveals individual memories;
- tree geometry shifts right while remaining bounded at desktop and mobile sizes;
- hover labels clamp to stage bounds, contain only the short statement, and preserve placement transforms;
- storyteller copy varies deterministically with archive, hover, selection, and event state;
- falling leaves obey count, lifecycle, visibility, and reduced-motion limits;
- the larger logo and sage panel visual contract are present;
- existing focus-chain transparency and vine interaction behavior remain intact.

Live verification must cover a full reload, loader visibility, ground-up opening, memory hover/focus label, tree centering, selected-memory narrative, falling leaf cleanup, mobile layout, reduced motion, and browser console errors.
