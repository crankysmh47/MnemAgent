# Judge guide

Track: MemoryAgent. Allow five minutes for the main test and two minutes for optional inspection.

## Five-minute test

1. Open the submitted HTTPS URL. The public `demo-brain` tree should load without a login.
2. Search for `backend framework`, select a leaf, and inspect its relationship chain in the Memory Lens.
3. Enter the supplied judge code in the MnemCode panel. The code creates a one-hour signed session; it is not an API key.
4. Start prepared task 1. Watch Activity for issue, memory, workspace, patch, and test events.
5. Add this review: `Keep error messages user-safe and put detailed diagnostics only in server logs.` The agent stores it under the repository scope.
6. Start prepared task 2 in the fresh session offered by the UI. Open Memory and confirm that the review convention appears before the plan.
7. Open Changes, check the diff and passing test output, then approve the draft PR.

Expected result: a draft PR URL. The agent cannot push to `main`, edit GitHub Actions, install packages, run a generic shell, or open a PR before tests and human approval.

## What this proves

- Persistence: the correction survives a fresh OpenClaw session.
- Scope: repository guidance does not alter core preferences or another repository.
- Retrieval economy: no more than four repository and two core memories enter the model context.
- Forgetting: low-value memories decay and cross the prune threshold; contradictions replace only the matching scoped belief.
- Agency: the model reads an issue, chooses files, proposes a patch, runs tests, and stops at an approval boundary.
- Observability: the UI shows ordered server events rather than a simulated terminal transcript.

## Recovery

- Empty tree: use `?user=demo-brain`.
- Judge code rejected: wait for the organizer if the IP lockout was triggered after five attempts.
- Model budget reached: the UI switches to the recorded replay and labels it clearly.
- Spot interruption: the run becomes interrupted; no PR opens and the workspace is cleaned on restart.
- Test failure: inspect Changes, revise the agent instruction, and rerun the fixed test command.
