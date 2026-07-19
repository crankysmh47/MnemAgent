# Judge guide

**Track:** Track 1 — MemoryAgent

**Live URL:** [https://47-237-140-12.sslip.io/?user=demo-brain](https://47-237-140-12.sslip.io/?user=demo-brain)

**Time:** about five minutes

The landing page is populated and read-only, so the core memory design is visible before login or model spend.

## Five-minute test

1. Open the live URL. Confirm that the populated `demo-brain` tree appears.
2. Search for `backend framework`, select a leaf, and inspect its relationship chain in the Memory Lens.
3. Enter the judge code supplied privately through Devpost. This code is not an API key. It creates a signed seven-day session and a random private namespace.
4. Send: `For WebPort, keep error messages user-safe and put detailed diagnostics only in server logs.`
5. Send: `What error-message convention should you follow for WebPort?` This is a different OpenClaw session. The response should recall the convention, and the MnemTree should show the new memory.
6. Start the prepared WebPort issue #14 task. Watch Activity for issue inspection, workspace creation, memory retrieval, source changes, diff generation, and tests.
7. Open Memory to see the repository-scoped guidance. Open Changes to inspect the exact patch and test output.
8. If you want to exercise publication, check the review box and select **Open draft PR**. Nothing can publish before the run passes and this approval is submitted.

The allowance is 30 chat turns, five coding runs, and five draft-PR approvals. Seven days changes elapsed access only; it does not add model or publication quota.

## Expected result

The agent should demonstrate all four layers of the product:

- **Persistence:** the correction survives a fresh OpenClaw session.
- **Scope:** repository guidance remains separate from core preferences and other repositories.
- **Economy:** at most six relevant memories enter the model context.
- **Agency:** the model reads the issue, chooses bounded files, writes a patch, runs tests, and stops at a human approval boundary.

The workbench shows ordered server evidence, not a simulated terminal transcript.

## Pre-validated path

The reference run fixed [WebPort issue #14](https://github.com/crankysmh47/WebPort/issues/14) and produced [draft PR #15](https://github.com/crankysmh47/WebPort/pull/15). It retrieved repository memory, wrote the regression test first, changed only the source and test files, passed the focused and full unit commands, and used the repository owner's commit identity.

## Recovery

- **Empty tree:** reopen the URL with `?user=demo-brain`.
- **Judge code rejected:** five failures lock that source IP for 30 minutes.
- **Sponsored capacity reached:** use the public tree and validated PR; both require no live model call.
- **Spot interruption:** no PR opens. The seven-day allowance is stored in a Docker volume and returns after the service is restored.
- **Test failure:** the approval control remains unavailable; inspect the pre-validated PR instead.

## What is intentionally unavailable

Judges do not provide GitHub or model keys to the browser. The hosted broker owns a repository-limited token, and the sponsored model budget is server-side. General bring-your-own-key and arbitrary repository execution are future product capabilities, not hidden experimental paths in this submission.
