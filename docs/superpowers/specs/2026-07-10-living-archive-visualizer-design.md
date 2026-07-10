# Living Archive Visualizer Redesign

**Status:** Approved for implementation planning

**Date:** 2026-07-10

**Product:** MnemAgent

**Primary audience:** Hackathon judges and first-time viewers

**Secondary audience:** End users inspecting what their agent remembers

## 1. Objective

Replace the current MnemAgent visualizer with a completely new experience that makes persistent agent memory understandable and memorable at first sight. The redesign must communicate that memories are selectively formed, related, recalled, revised, strengthened, and allowed to fade.

The replacement is not constrained by the current visual design, layout, metaphors, component hierarchy, or interaction patterns. The existing backend API contracts may be reused where useful, but the current interface must not dictate the new one.

## 2. Non-negotiable experience principles

1. The page is one composed image, not a dashboard assembled from cards.
2. The living archive is always the visual protagonist.
3. Every visible element must support the memory lifecycle narrative.
4. The whole composition takes priority over isolated component polish.
5. Motion must indicate life or a meaningful memory event.
6. Organic materials dominate; cybernetic details provide structure and edge.
7. The interface must not use neon, hard sci-fi, generic tech decoration, or gratuitous particle effects.
8. Category and state must never rely on color alone.
9. The opening narrative must remain interactive and must never block the user.
10. Dense data, reduced motion, small screens, empty data, and API failures must still feel intentionally designed.

## 3. Central concept: The Living Archive

Memory is presented as a cultivated organism rather than a database, literal brain, or force-directed graph. Memories inhabit a softly branching structure made from roots, translucent membranes, seed capsules, engraved wires, and restrained brass joints.

The emotional blend is:

- Dominant: living intelligence
- Supporting: quiet wonder
- Finish: elegant spectacle

The visual result should resemble an animated natural-history plate crossed with a cybernetic reliquary. It should feel alive, observant, and gently uncanny without becoming threatening or mechanically cold.

## 4. Narrative: a memory becomes part of the organism

The interface tells five stages.

### 4.1 Arrival

A new memory enters as a pale seed near the edge of the archive. It pauses briefly to imply evaluation. An accepted memory warms and moves inward. Rejected or uncertain information remains faint and recedes without becoming a dramatic error.

### 4.2 Rooting

The seed searches for related memories using exploratory filaments. Candidate filaments extend and retract before the final connection takes hold. This explains semantic relationships in visual language before exposing technical graph terminology.

### 4.3 Becoming

The rooted seed opens into a category-specific form:

- Preference: folded leaf or petal
- Persona: smooth pearl-like seed
- System state: faceted mineral bud

Confidence and vitality are encoded through fullness, opacity, edge condition, movement, and color. Shape is the primary category cue.

### 4.4 Remembering

When recalled, a memory opens and sends a warm brass pulse through relevant branches. Connected forms respond with restrained motion and increased contrast. The sequence communicates that recall activates relationships rather than retrieving an isolated record.

### 4.5 Changing and fading

A contradiction closes the older form, creates a fine incision, and grafts the replacement to the same branch. The revision leaves a subtle brass scar. Neglected memories lose saturation, become papery, slow down, turn translucent, detach, and settle into the history timeline as husks.

Within the first ten seconds, a first-time viewer should understand that MnemAgent forms structured memories, relates them, recalls them selectively, revises them, and allows them to fade.

## 5. Whole-screen composition

The viewport is one continuous scene with one background, one lighting direction, one texture family, and one spacing rhythm.

### 5.1 Archive stage

The living structure occupies approximately 65–70% of the desktop viewport, centered slightly left. It receives the greatest contrast, detail, and motion. It must remain visible when a memory is focused; non-selected forms quiet down rather than disappearing or blurring into irrelevance.

### 5.2 Observation margin

The rightmost 30–35% is an editorial observation margin, not a conventional sidebar or card stack. Botanical annotation lines connect concise text to the archive. It contains:

- The current plain-language lifecycle heading
- Selected-memory statement and metadata
- Three vital signs: memory count, active relationship count, and recent recall count
- A compact material-and-shape legend
- Contextual actions only when relevant

### 5.3 Archive header

A thin header contains only:

- Simplified MnemAgent seal and wordmark
- Current user identity
- Live or paused status
- Compact archive menu

Filtering, export, replay, motion preferences, reset, and diagnostic controls belong inside the archive menu or appear contextually. They must not compete with the organism.

### 5.4 Sediment timeline

A shallow event timeline is attached to the bottom edge. Events settle chronologically as seeds, scars, petals, pulses, and husks. Hover or focus reveals the event text. Selection replays the event's visual effect when the source data supports it. The timeline replaces the existing terminal-style event feed.

### 5.5 Visual hierarchy

The fixed priority is:

1. Living structure and active lifecycle motion
2. Selected or changing memory
3. Plain-language narrative annotation
4. Supporting vital signs
5. Controls and technical detail

No implementation task may invert this priority.

## 6. Visual language

### 6.1 Palette

| Token | Hex | Role |
|---|---:|---|
| Midnight charcoal | `#151714` | Primary background and deepest ink |
| Warm parchment | `#EEE8DA` | Annotation surfaces and primary light text |
| Bone white | `#F6F1E7` | Strongest highlights and readable foreground |
| Antique brass | `#B68A4A` | Active relationships, recall, joints, and primary action |
| Living moss | `#69765A` | Mature preference forms and established growth |
| Lichen green | `#94A67C` | New growth, recently rooted memories, and healthy connection accents |
| Clay rose | `#A86758` | Persona forms, revision seams, and emotional warmth |
| Mineral blue | `#637985` | System-state forms and constructed elements |
| Weathered taupe | `#8B8171` | Dormant and fading states |

Gold must read as a material, not emitted light. Recall may briefly lift antique brass toward bone white, but no effect may create a neon halo, bloom cloud, or LED-like glow.

### 6.2 Materials

The material vocabulary is smoked glass, uncoated paper, bark, translucent tissue, aged brass, pearl, dried leaves, and mineral facets. Texture must remain subtle enough to preserve legibility and rendering performance.

### 6.3 Shape language

- Memories combine seeds, petals, pearls, and mineral buds.
- Relationships combine roots, veins, and engraved wires.
- Cybernetic structure uses incomplete rings, hinges, clamps, sutures, and revision scars.
- Separators resemble engraved rules or botanical annotation lines.
- Corners use irregular organic curves instead of repeated rounded rectangles.
- Mechanical components move less than organic components.

### 6.4 Typography

- Display and narrative: Cormorant Garamond
- Interface and body: Manrope
- Technical identifiers and timestamps: IBM Plex Mono

Display typography is reserved for headings and lifecycle prose. Interface copy must remain highly legible. Uppercase is limited to short specimen labels. Font loading must use a system fallback stack and may not hide content while web fonts load.

### 6.5 Logo integration

The existing logo is a source of thematic cues, not a miniature illustration to paste into the header. Create a simplified monochrome brass seal derived from its head, circuit, and organic-mechanical motifs. Do not reproduce the ornate border throughout the interface.

## 7. Motion language

Motion exists because the archive is alive or because a memory event occurred.

### 7.1 Ambient motion

- The full structure breathes by 1–2% over a 7–9 second cycle.
- Tendrils carry occasional low-contrast pressure waves.
- Memory forms drift by one or two pixels at offset phases.
- Brass components remain nearly still.
- Background grain moves imperceptibly.
- Ambient work pauses when the page is hidden.

### 7.2 Opening choreography

The opening lasts approximately 8–10 seconds and never blocks interaction:

1. `0–2s`: darkness lifts into material texture and the brass skeleton resolves.
2. `2–5s`: membranes and living branches grow into place.
3. `5–8s`: one real memory roots and activates related forms.
4. `8–10s`: annotations and vital signs settle into view.

The opening runs once per page load. Polling or resizing must not replay it.

### 7.3 Lifecycle transitions

- New memory: arrive, pause, move inward, root, open.
- New relationship: exploratory filaments search, retract, and attach.
- Recall: form opens, brass pulse travels, related forms answer.
- Strengthening: form becomes fuller, steadier, and more saturated.
- Contradiction: old form closes, incision appears, replacement grafts, seam settles into brass.
- Decay: form dries, slows, fades, and becomes translucent.
- Pruning: husk detaches and settles into the sediment timeline.

### 7.4 Edgy fallback language

When complex organic deformation would be brittle or slow, the design must deliberately switch to sharp brass linework, silhouettes, incision marks, mechanical ticks, and material dissolves. This is a supported visual mode, not a degraded accident. It preserves completeness without introducing neon or hard-tech styling.

### 7.5 Reduced motion

When `prefers-reduced-motion: reduce` is active or the user disables motion:

- Breathing, drifting, traveling pulses, and growth paths stop.
- Lifecycle states use short dissolves, contrast changes, line-weight changes, and static scars.
- Information, selection, filtering, event replay results, and focus relationships remain available.

## 8. Interaction model

### 8.1 Memory exploration

- Hover: the form turns subtly toward the pointer and neighboring branches tense.
- Click or keyboard activation: focus the memory while keeping the whole archive visible.
- Related memories rise in contrast and the relationship path becomes legible.
- Double-click or explicit Trace action: enter trace mode and follow related memories through the archive.
- Escape: exit trace or focus mode in one step.

### 8.2 Navigation

- Wheel zoom operates only while the pointer is over the archive stage.
- Drag pans the archive.
- Individual memories cannot be manually rearranged.
- A menu action restores the canonical seeded view.
- Focused memories remain reachable and labeled after zoom or resize.

### 8.3 Timeline

- Hover and keyboard focus reveal timestamp, event type, and plain-language event text.
- Selection replays a supported lifecycle effect without mutating backend state.
- The most recent meaningful event is emphasized; repeated low-value events remain quieter.

### 8.4 Filters and controls

Filters use shape samples plus text and live inside the archive menu. Changing filters quiets excluded memories and relationships rather than abruptly deleting them from the scene. A filtered-empty state explains that memories exist but are hidden.

## 9. Information model

The frontend normalizes the current graph, metrics, and event APIs into a single archive state.

### 9.1 Memory state

Each normalized memory contains:

- Stable string ID
- Plain-language statement
- Source, relation, and target fields
- Normalized category: `preference`, `persona`, or `system_state`
- Confidence and vitality values clamped to `0..1`
- Recall and influence counts
- Derived lifecycle state: `new`, `rooted`, `vivid`, `stable`, `fading`, or `dormant`
- Visual shape type
- Stable layout seed
- Selection, trace, and filter visibility flags

### 9.2 Relationship state

Each relationship contains stable source and target IDs, normalized kind, clamped weight, layout path, and active or quiet display state. Backend-provided edges are authoritative. Frontend inference is allowed only as an explicit fallback when edges are missing.

### 9.3 Event state

Each event contains a deterministic identity, timestamp, normalized lifecycle type, affected memory identity when available, display statement, replay capability, and sediment glyph type.

### 9.4 View state

The store tracks:

- Loading, ready, empty, filtered-empty, degraded, or error status
- Current user ID
- Selected and traced memory IDs
- Active filters
- Zoom transform
- Motion preference
- Opening and lifecycle narrative phase
- Last processed event identity
- Polling and document visibility status

## 10. Technical architecture

The visualizer remains a lightweight static browser application served by the existing Express harness. It uses semantic HTML, CSS, SVG, native ES modules, and the existing vendored D3 package. Chart.js is removed. No frontend framework or build pipeline is introduced.

### 10.1 Target file organization

```text
openclaw-harness/src/public/
├── index.html
├── favicon.svg
├── assets/
│   ├── mnemagent-seal.svg
│   ├── paper-grain.svg
│   └── material-samples.svg
├── styles/
│   ├── tokens.css
│   ├── base.css
│   ├── archive-stage.css
│   ├── observation-margin.css
│   ├── sediment-timeline.css
│   ├── motion.css
│   └── responsive.css
└── scripts/
    ├── main.js
    ├── api.js
    ├── archive-store.js
    ├── memory-model.js
    ├── narrative.js
    ├── layout.js
    ├── render/
    │   ├── living-structure.js
    │   ├── memory-form.js
    │   ├── tendril.js
    │   ├── annotations.js
    │   └── timeline.js
    ├── motion/
    │   ├── choreographer.js
    │   ├── lifecycle-transitions.js
    │   └── ambient-motion.js
    └── interactions/
        ├── archive-navigation.js
        ├── memory-focus.js
        └── archive-menu.js
```

Every file has one responsibility. Renderers do not fetch. API modules do not know visual details. Layout functions do not manipulate the DOM. Motion modules do not own application state.

### 10.2 Data flow

```text
Existing graph, metrics, and event APIs
  → API validation and fallback
  → memory/event normalization
  → unified archive store
  → narrative event selection
  → stable organic layout
  → SVG and HTML renderers
  → lifecycle choreography
```

### 10.3 Update behavior

- Graph, metrics, and events load concurrently at startup.
- Structural graph changes trigger a lifecycle transition.
- Metric-only changes update annotations without rebuilding the archive.
- Existing positions remain stable between polls.
- Events are deduplicated by deterministic identity.
- In an event burst, one meaningful event receives full choreography and the remainder settle quietly into the timeline.
- Polling must not reset zoom, selection, trace mode, opening state, or stable positions.
- Resize recomputes bounds and paths without replaying lifecycle events.

### 10.4 Rendering

- SVG renders the living structure, paths, forms, material filters, and stage annotations.
- HTML renders the observation margin, menu, accessible status, and detailed text.
- CSS handles material surfaces, ambient transforms, responsive composition, and reduced motion.
- A deterministic seeded layout keeps each user's archive recognizable across refreshes.
- Dense archives group distant memories into groves while retaining aggregate category and vitality cues.

## 11. Responsive behavior

### Desktop, `>= 1100px`

Use the 65–70% archive stage and 30–35% observation margin composition. The sediment timeline remains attached to the bottom.

### Tablet, `700–1099px`

The archive occupies the upper two-thirds. The observation margin becomes a lower editorial band. The timeline remains compact at the bottom. Selection scrolls its annotation into view without moving the archive offscreen.

### Mobile, `< 700px`

The archive fills the initial viewport beneath the thin header. The observation margin becomes an accessible pull-up sheet. The sediment timeline remains a shallow horizontal strip. Touch targets are at least 44 by 44 CSS pixels. Pinch zoom and one-finger panning must not trap page scrolling outside the archive.

## 12. Accessibility

- The archive has an accessible summary describing memory count and current state.
- Every memory is keyboard reachable through an ordered companion list or SVG focus target.
- Shape, text, and line treatment reinforce all color encodings.
- Focus indicators use bone-white and brass outlines with sufficient contrast.
- Live updates use a polite status region and announce only meaningful changes.
- The opening sequence never delays access to controls or memory details.
- Tooltips are also available through focus and do not contain exclusive information.
- All menu controls expose names, states, and expanded relationships.
- Reduced motion retains every informational state.

## 13. Loading, empty, degraded, and error states

### Loading

Show the dormant structural skeleton resolving quietly. Do not use a generic spinner or fake data.

### Empty archive

Show a root crown with one waiting seed and the message that the archive is ready for its first memory. Offer a copyable next action appropriate to the configured user. Do not auto-seed users other than the explicit demo user.

### Filtered empty

Keep the dormant organism visible and explain that existing memories are quieted by the current filters. Provide one Clear filters action.

### Degraded data

If one API fails, render the available data. Mark unavailable annotations with restrained disconnected-joint imagery and plain text. Continue polling the failed source with bounded retry intervals.

### Fatal error

Show a disconnected brass joint, concise error text, and a Retry action. Technical details remain inside the archive menu and never replace the primary message.

## 14. Performance constraints

- First meaningful archive skeleton should render without waiting for web fonts.
- Use transforms and opacity for recurring motion wherever possible.
- Pause ambient work in background tabs.
- Avoid per-frame DOM creation, layout reads, and SVG filter mutation.
- Cap simultaneous traveling pulses and exploratory filaments.
- Reduce decoration before reducing information as archive density rises.
- Use one shared SVG definition set for gradients, textures, masks, and filters.
- Preserve stable object identity so metric polling does not recreate the full SVG tree.
- The visualizer must remain usable with at least the existing 62-memory, 405-relationship demo dataset.

## 15. Validation strategy

### Unit tests

Test pure modules for:

- Category normalization
- Confidence and lifecycle derivation
- Event identity and deduplication
- Backend edge normalization and inference fallback
- Deterministic seeded layout
- Dense-grove grouping
- Store transitions that preserve selection and zoom
- Narrative selection during event bursts

### Browser checks

Verify:

- Initial load with demo data
- Opening sequence does not block interaction
- New, recalled, contradicted, decayed, and pruned event presentation
- Focus and trace behavior
- Filtered-empty state
- API partial failure and recovery
- Reduced-motion behavior
- Keyboard navigation and Escape handling
- Desktop, tablet, and mobile layouts
- Stable layout across refresh and polling
- No console or page errors

### Visual regression targets

Capture stable screenshots for:

- Default demo archive
- Selected preference memory
- Trace mode
- Contradiction graft
- Empty archive
- Degraded metrics
- Reduced motion
- Mobile observation sheet

### Acceptance narrative

A first-time viewer shown the page for ten seconds should be able to answer:

1. What does MnemAgent remember?
2. How are memories related?
3. What happens when a memory is recalled, revised, or forgotten?

## 16. Explicit exclusions

- Reusing the current page composition or card dashboard
- Literal brain silhouettes
- Terminal-style event feeds
- Chart.js charts
- Manual node rearrangement
- Neon glow, holographic grids, scanning beams, or generic cyberpunk effects
- Unrelated background particles
- A second chat interface
- Backend mutations from timeline replay
- A frontend framework migration
- A new build pipeline
- Decorative illustrations that compete with the live archive

## 17. Definition of design success

The redesign succeeds when it feels like one complete living portrait, immediately demonstrates the MnemAgent memory lifecycle, remains understandable without documentation, responds beautifully to real data, and preserves its narrative hierarchy in reduced-motion, dense-data, empty, degraded, and small-screen states.
