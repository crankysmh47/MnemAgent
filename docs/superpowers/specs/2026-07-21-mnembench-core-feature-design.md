# MnemBench core-feature documentation design

## Objective

Make MnemBench an immediately visible core feature of MnemAgent, explain its evolution without conflating v1 and v2, remove the final obsolete repository wording, and preserve direct links to measured evidence.

## Product model

The repository will present four connected surfaces:

- **MnemAgent** is the persistent memory engine and MCP interface.
- **MnemTree** makes stored memories, relationships, scopes, and lifecycle changes observable.
- **MnemBench** measures whether memory improves agent behavior across sessions and lifecycle events.
- **MnemCode** demonstrates one bounded agentic use case in which recalled repository knowledge changes a coding decision.

MnemBench and MnemCode remain optional proof surfaces. Neither is required to use MnemAgent with an ordinary OpenClaw installation.

## Canonical MnemBench document

Create `docs/MNEMBENCH.md` as the single narrative authority for the benchmark. It will cover:

1. The memory-agent evaluation problem MnemBench addresses.
2. The evolution from the compact public v1 repository to the expanded v2 suite.
3. The exact location and status of each version:
   - v1 is the public `crankysmh47/MnemBench` repository.
   - v2 currently lives in MnemAgent's `eval/` directory and is not a separate public repository.
4. The dimensions added in v2, including cross-session continuity, scoped recall, contradiction handling, revision, and forgetting.
5. How MnemBench relates to MnemTree and MnemCode.
6. Links to the stable results record, reproduction commands, public issue, and public draft PR.
7. Honest limitations: scenario-level variance, the difference between Postgres smoke evidence and live-provider evidence, and no claim that every scenario improves equally.
8. Future direction, framed as planned work rather than existing functionality.

Numerical results will remain canonical in `docs/BENCHMARKS.md` and `docs/evidence/MNEMBENCH_V2_RESULTS.md`; the new document will link to them instead of duplicating unstable tables.

## Navigation changes

Update the root `README.md` so the four-part product model appears near the first judge-facing evidence links. Promote the MnemBench document alongside architecture, deployment proof, judge instructions, and measured results.

Update `docs/README.md` so `MNEMBENCH.md` appears before the detailed benchmark-results document. The navigation should let a judge understand the product role first, then inspect the measurements.

Replace the final legacy-repository reference in `docs/DEMO_VIDEO_PRODUCTION_SCRIPT.md` with a positive check that the visible interface uses the current MnemBench task and terminology.

## Evidence discipline

- Do not rename historical GitHub artifacts or manufacture a MnemBench v2 repository.
- Do not present the sponsored DeepSeek judge run as Qwen evidence.
- Do not generalize aggregate improvements to every scenario.
- Keep dates, scores, public issue links, and PR links tied to their existing evidence documents.
- Describe future standalone packaging as future work.

## Verification

After editing:

1. Search the repository for the retired repository name; the result must be empty in tracked product and documentation files.
2. Check every new relative Markdown link resolves to an existing file.
3. Run the repository's focused documentation and harness checks that do not require paid model calls.
4. Review the final diff for accidental changes to benchmark evidence or credentials.
5. Commit the pending judge activity-persistence fix and documentation changes intentionally, preserving the user's commit identity configuration, then push the `MnemCode` branch.
