# Ancient Memory Tree Visualizer Design

## Purpose

Replace the current radial memory cluster with a single, unmistakable ancient plant. The visualizer must help first-time viewers understand that memories accumulate, strengthen, connect, and fade inside one living intelligence. It must retain the existing charcoal, parchment, brass, moss, lichen, clay, and mineral-blue palette and avoid neon or hard-tech styling.

## Composition

The archive stage contains one asymmetrical tree occupying most of the available canvas. A visible root flare anchors it near the bottom center. A tapered trunk rises into three overlapping branch families and a broad, uneven canopy. Empty space around the crown keeps the silhouette legible at a glance.

Memory categories occupy consistent botanical roles:

- Preferences are lichen and moss leaves along outer branchlets.
- Persona memories are clay-colored fruit or rounded seed pods nearer the warm central canopy.
- System-state memories are mineral-blue growths attached to structural limbs.

High-vitality memories sit closer to strong limbs and appear fuller. New memories sit near branch tips. Fading and dormant memories become smaller, drier, and quieter without disappearing. The layout remains deterministic for the same data and keeps every form inside the viewport.

## Layout Architecture

The layout module will return four coordinated structures:

1. A root and trunk skeleton derived from the current viewport.
2. Category-specific branch paths attached to the trunk.
3. Memory nodes assigned to stable positions along those paths using their IDs, category, and vitality.
4. Relationship paths routed as fine internal veins between memory positions.

The canopy expands vertically and horizontally as memory count increases. Collision resolution may adjust a memory locally but must preserve its assigned branch and never collapse the tree into a circular packing pattern. Responsive layouts retain the same tree semantics with a narrower crown and taller trunk.

## Rendering

The renderer will create separate SVG layers for roots, trunk, branches, relationship veins, memory-position groups, interactive memory shapes, effects, and annotations. Root and branch geometry is data-driven from the layout instead of using one fixed decorative path.

Each memory uses two nested groups:

- The outer group owns its permanent layout translation.
- The inner group owns hover, focus, selection, and lifecycle motion.

This separation is mandatory. Interaction CSS must never set `transform` on the outer positioning group, preventing hover animations from overriding or corrupting SVG placement.

## Interaction and Narrative

At rest, the tree breathes almost imperceptibly and its canopy sways as one organism. Motion remains soft and coordinated rather than giving every node an independent pulse.

Hover gently lifts, tilts, and brightens only the inner memory shape. Selection quiets unrelated memories, strengthens the selected branch, and illuminates the complete relationship path through the tree. Double-click trace continues to expose the wider connected neighborhood.

Lifecycle events become botanical actions:

- New belief: a bud opens at a branch tip.
- Recall: sap-like light travels from root to memory.
- Influence: a vein warms between related memories.
- Revision: a scar closes and a new shoot grafts onto the branch.
- Decay: a form curls inward and loses saturation.
- Pruning: a husk falls and the branch settles.

Reduced-motion mode removes sway, lift, traveling pulses, and growth transitions while preserving opacity, stroke, and selection-state changes.

## Data Flow

Existing normalized memory and relationship data remains the source of truth. The main controller passes visible memories and the capped contextual relationship set into the tree layout. The layout returns all drawable geometry. The renderer consumes that geometry without recomputing placement. Filters and selection trigger deterministic re-layout and re-render through the existing store subscription.

No backend or API changes are required.

## Failure and Empty States

An empty archive shows the root flare and one dormant central bud with the existing explanatory copy. Partial API failure keeps the last usable tree visible and reports degraded status. Missing relationships produce a valid tree with no veins. Unknown categories continue to normalize to system state.

## Accessibility

Memory forms remain keyboard-focusable buttons with meaningful labels. Focus uses both a high-contrast outline and a branch highlight. The companion list remains available to assistive technology. Touch targets remain at least 44 pixels even when their visible botanical form is smaller.

## Verification

Automated tests will prove:

- The layout forms a rooted, branching, non-radial silhouette.
- Every memory remains bounded and assigned to a category branch.
- Layout output is deterministic and permutation-stable.
- Root, trunk, and branch paths contain finite SVG geometry.
- Hover transforms apply only to the inner interaction group.
- Selection preserves the outer translation and highlights related paths.
- Dense live data remains readable and relationship rendering stays capped.
- Reduced-motion behavior removes continuous and interaction animation.

The final browser check will use the live 62-memory demo, verify hover and selection visually, exercise filters, inspect desktop and mobile compositions, and confirm there are no browser errors.
