# Judge guide

**Track:** Track 1 — MemoryAgent

**Live URL:** [https://47-237-140-12.sslip.io/?user=demo-brain](https://47-237-140-12.sslip.io/?user=demo-brain)

**Time:** about five minutes
**Credentials:** only the private judge code supplied in Devpost

The landing page is populated and read-only. You can inspect the product before authenticating or using sponsored model capacity.

## Test the complete flow

1. Open the live URL. Confirm that the populated `demo-brain` tree appears.
2. Search for `backend framework`, select a leaf, and inspect its relationship chain in the Memory Lens.
3. Enter the private judge code from Devpost. This is not an API key. It creates a signed seven-day session and a random private memory namespace.
4. Send: `For MnemBench, keep every metric oriented so 1.0 means best behavior.`
5. Send: `What scoring convention should you follow for MnemBench?`
6. Confirm that the second reply recalls the convention. Each message uses a fresh OpenClaw conversation, so recall comes through MnemAgent rather than shared chat history.
7. Open the private MnemTree and locate the new repository-scoped memory.
8. Start the prepared [MnemBench issue #1](https://github.com/crankysmh47/MnemBench/issues/1) task.
9. Watch Activity for issue inspection, workspace creation, memory retrieval, test creation, the bounded source fix, and both Python test commands.
10. Open Memory to see the exact repository rule. Open Changes to inspect the patch and test output.
11. Optional: check the review box and choose **Open draft PR**. Publication remains disabled until the exact diff passes both checks and receives explicit approval.

The allowance is 30 chat turns, five coding runs, and five draft-PR approvals. Seven days changes elapsed access only; it does not add quota.

## Expected evidence

- **Persistence:** the rule survives a fresh OpenClaw conversation.
- **Scope:** the rule is stored under `repository/crankysmh47/MnemBench`, separate from core preferences.
- **Economy:** no more than six memories enter model context.
- **Agency:** the model reads a public issue, writes a regression test, fixes real code, runs tests, and explains the result.
- **Control:** the runner has no network or GitHub token, and publication requires a human decision.

The Activity view contains ordered server events. It is not a simulated terminal transcript.

## Pre-validated public result

The July 20 acceptance run solved issue #1 and produced [draft PR #2](https://github.com/crankysmh47/MnemBench/pull/2). It retrieved the MnemBench metric-orientation rule across fresh sessions, added three regression tests, changed one scoring expression, passed both fixed Python commands, and used only the repository owner's commit identity.

## Recovery

- **Empty tree:** reopen the URL with `?user=demo-brain`.
- **Judge code rejected:** five failures lock that source IP for 30 minutes.
- **Sponsored capacity reached:** inspect the populated tree, public issue, [validated draft PR #2](https://github.com/crankysmh47/MnemBench/pull/2), and benchmark records.
- **Spot interruption:** no PR opens. Durable quota state returns when the service restarts.
- **Test failure:** approval remains unavailable. The Changes view preserves the red output for inspection.

## Credential boundary

Judges do not paste GitHub or model keys into the browser. The hosted broker owns a repository-limited token, while the sponsored model budget stays server-side. General bring-your-own-key and arbitrary repository execution remain future capabilities, not hidden experimental paths.
