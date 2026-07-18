# Expanded Judge Session Allowance Design

## Goal

Give each authenticated judge enough room to teach the agent repository conventions, revisit them across fresh chat sessions, run several bounded coding tasks, and approve several independently evidenced draft pull requests.

## Decision

Each one-hour judge session receives 30 chat turns, 5 coding runs, and 5 draft-PR publication allowances. The server reserves $0.01 for each chat turn and $0.05 for each coding run, so the displayed per-session reserve is $0.55.

The existing controls do not change: one coding run may execute globally at a time; a draft PR still requires passing evidence, a non-empty diff, an explicit judge confirmation, an unused publication allowance, and a current diff-bound broker approval token. The global model token budget and maximum sponsored-session cap remain independent deployment controls.

## Implementation and verification

The session store remains the single authority for allowances. Its initial quota and release ceiling change to the new limits. Its unit tests will prove the full allowance can be consumed, the next request is rejected, and a failed in-flight operation restores only one allowance. The judge UI already renders the values returned by the API, so it requires no behavioral change.

README and judge-facing documentation will describe the expanded allowances and the $0.55 displayed reserve. No secrets, provider credentials, or GitHub permissions are exposed by this change.
