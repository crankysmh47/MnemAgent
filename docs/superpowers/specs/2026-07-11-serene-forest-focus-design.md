# Serene forest focus design

## Goal

Turn the light archive into a restrained forest scene while keeping the
MnemTree visually dominant and making selected memory chains easier to read.

## Scene composition

- Remove the three trunk-climbing garden vines and their internal leaf marks.
- Add four hanging vine groups anchored to the top-left and top-right edges.
  Their lower ends stay outside the dense memory canopy.
- Replace the sparse bottom decoration with a continuous irregular grass bank,
  a few taller blades near the outer roots, and muted moss around the trunk.
- Add one shallow reflective water shape behind the grass. It uses mineral blue,
  bone white, and moss at low opacity, with two quiet ripple lines. It must read
  as atmosphere rather than a separate feature.

## Motion and interaction

- Hanging vines sway with slow, alternating CSS animations. Each vine has a
  wider transparent hover target; hover increases its movement slightly.
- Vines remain decorative and `aria-hidden`. They do not receive keyboard focus
  or trigger product actions.
- `prefers-reduced-motion: reduce` disables vine and water movement completely.
- No other environmental element intercepts pointer events.

## Memory-chain focus

- A relationship is active only when it directly touches the selected or traced
  memory. Connections merely touching a neighbor remain quiet.
- While a memory is selected, unrelated memory forms fade to 6 percent opacity
  and quiet tendrils fade to 3 percent.
- Roots, branches, groundcover, water, and hanging vines soften behind the
  selected chain. Selected and directly related memories remain fully opaque.
- Clearing selection restores the complete forest with no layout changes.

## Rendering boundaries

- Scene order is: hanging canopy, water, groundcover, roots, trunk, branches,
  tendrils, memories, effects, annotations.
- Environmental coordinates scale from the existing tree bounds and use stable
  data keys so repeated D3 renders never duplicate elements.
- The environment must not overlap the observation panel or timeline.

## Verification

- Add failing tests for the new layer order, hanging-vine classes, water and
  grass classes, reduced-motion rules, and direct-incidence relationship focus.
- Run the full Node suite and fixture visualizer check.
- Exercise a memory selection in Playwright and assert the stage enters focus
  mode without changing memory placement transforms.
- Capture and inspect the live `demo-brain` scene at 1440 by 1080, confirming 62
  memories, no console errors, and a readable selected chain.
