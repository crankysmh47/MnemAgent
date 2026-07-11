# Rooted garden design

## Goal

Give the light-theme living archive a grounded, botanical setting without
competing with the memory forms or changing archive behavior.

## Render layers

- Add a `groundcover` SVG group before roots, trunk, branches, tendrils, and
  memories. It contains grass tufts, moss patches, and small seed heads beneath
  the existing root system.
- Add a `vines` SVG group after branches but before tendrils and memories. It
  contains three low-opacity curling vine paths plus a restrained set of leaf
  marks.
- Every environmental element is `aria-hidden`, has no pointer events, and is
  keyed by a stable string so D3 updates do not duplicate it.

## Composition

- Groundcover stays in the bottom 24 percent of the tree viewBox, centered on
  the root base and extending outward along the two outer roots.
- Vines use the existing moss, lichen, and brass palette. They climb the trunk
  and only occupy quiet canopy pockets rather than crossing memory nodes.
- The details are static. Existing ambient animation and reduced-motion rules
  remain unchanged.

## Verification

- Extend the render contract test to require both environmental layer names and
  the decorative class names in the renderer and stage stylesheet.
- Run the fixture check to verify the memory count, hit targets, hover behavior,
  and reduced-motion behavior remain intact.
- Capture the live `demo-brain` page and visually inspect that the tree remains
  the focal point and no decoration sits above memory forms.
