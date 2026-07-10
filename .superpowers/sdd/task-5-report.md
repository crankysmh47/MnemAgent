# Task 5 report

Implemented deterministic normalized-coordinate archive layout in `layout.js`, including seeded hashing/randomness, category groves, 32-pass collision relaxation, viewport bounds, cubic relationship tendrils, and >80-memory grove collapsing.

Verification:
- `node --test test/layout.test.mjs` — 3 passed.
- `npm.cmd test` — 23 passed.

Fix evidence:
- Selected memories are excluded from the >80-memory collapse set even when low vitality.
- Memories without IDs receive deterministic content-derived IDs, so input permutation preserves node identity and positions.
- Collapsed groves expose aggregate centroid, representative, member IDs, and count while retaining visible members.

Verification after fixes:
- `node --test test/layout.test.mjs` — 5 passed, including selected low-vitality preservation, permutation-stable generated IDs, and grove aggregate/member metadata.
- `npm.cmd test` — 25 passed.

Concerns: layout intentionally uses normalized memory fields (`id`, `category`, `vitality`/`node_weight`) and emits compact grove metadata; UI rendering remains out of scope.
