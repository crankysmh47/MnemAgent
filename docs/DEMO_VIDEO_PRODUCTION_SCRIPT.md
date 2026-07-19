# Three-minute demo production sheet

This document is a complete recording brief for a zero-context computer operator. The presenter supplies the narration. The operator controls Chrome and OBS Studio, follows the timeline, and produces one clean recording between 2:50 and 3:05.

## Deliverable

- Resolution: 1920 × 1080
- Frame rate: 30 fps
- Final format: MP4, H.264 video, AAC audio
- Target duration: 2:55
- Hard maximum: 3:05
- Presenter: live microphone narration
- Optional presenter camera: one short segment in the middle
- No background music
- No synthetic terminal output
- No private keys, access codes, cookies, environment files, browser profiles, or billing pages on screen

## Story

The video answers one question: does persistent memory change what an agent does?

The evidence appears in this order:

1. MnemTree shows what the agent remembers.
2. A fresh OpenClaw conversation recalls a repository rule from an earlier conversation.
3. MnemCode shows that rule affecting a tested coding task.
4. The architecture and benchmark evidence show how the system works and how it was measured.
5. Alibaba Cloud proof shows where the backend is running.

Do not present MnemAgent as a generic cloud IDE. MnemCode is one narrow, working agentic use case around the core memory MCP.

## URLs and files

Open these before recording, in this exact tab order:

1. **MnemTree:** `https://47-237-140-12.sslip.io/?user=demo-brain`
2. **Private MnemCode workspace:** the same site after judge login
3. **Validated draft PR:** `https://github.com/crankysmh47/WebPort/pull/15/files`
4. **Benchmarks:** `https://github.com/crankysmh47/MnemAgent/blob/MnemCode/docs/BENCHMARKS.md`
5. **Architecture image:** `https://github.com/crankysmh47/MnemAgent/blob/MnemCode/docs/assets/architecture.png`
6. **Alibaba proof image:** `https://github.com/crankysmh47/MnemAgent/blob/MnemCode/docs/assets/alibaba-ecs-workbench.png`

Keep Devpost, Alibaba Workbench, DeepSeek billing, `.env.cloud`, and all credential pages closed during recording.

## Pre-stage the live product before opening OBS

Complete this section off-camera. It prevents model or workspace latency from ruining the take.

1. Open tab 1 at the exact MnemTree URL above.
2. Wait for the leaf spinner to complete at least one rotation and for all 62 memories to appear.
3. Confirm the header says `62 memories`.
4. Confirm the right panel says `MnemCode · judge workspace` and `Watch memory become action.`
5. Do not leave a memory selected.
6. Open tab 2 and enter the private judge access code.
7. Never record the login step or expose the code.
8. In private chat, send this exact message:

   `Please remember this durable repository rule for WebPort: preserve backward compatibility and add a regression test before changing behavior.`

9. Wait until the response completes.
10. Start a fresh conversation using the product control.
11. Send this exact message:

    `What repository-specific rule did I ask you to remember for WebPort?`

12. Wait for the answer to recover both `preserve backward compatibility` and `add a regression test`.
13. Keep this completed conversation visible. Do not refresh tab 2.
14. If a completed issue #14 run is already visible in the workspace, keep it.
15. If no completed run is visible, run the prepared WebPort issue #14 scenario off-camera.
16. Wait until Activity shows completion, both tests pass, and Changes contains a non-empty diff.
17. Do not approve or publish another PR.
18. Leave the workspace on its Activity panel at the beginning of the completed run.
19. Open tabs 3 through 6 and wait for each to finish loading.
20. Set Chrome zoom to 100% on the product tabs.
21. Set GitHub zoom to 110% if the benchmark or architecture text is too small.
22. Close downloads, notifications, chat overlays, password prompts, and unrelated tabs.
23. Turn off browser bookmarks bar if it contains private names or links.
24. Turn on Do Not Disturb in Windows.

## OBS Studio setup

Create these scenes before recording.

### Scene 1: Product

- Source: Window Capture
- Window: Chrome containing the prepared demo tabs
- Capture method: Windows 10/11 capture
- Client area: on
- Cursor: on
- Crop browser chrome only if the URL bar contains no useful context; otherwise retain the URL bar so the public deployment is visible
- Fit the browser to the 1920 × 1080 canvas
- No decorative frame

### Scene 2: Presenter, optional

- Source 1: the same Chrome Window Capture, full canvas
- Source 2: webcam
- Webcam placement: bottom-right
- Webcam width: roughly 420 px
- Margin from right and bottom: 40 px
- Add a subtle 2 px warm-gray border
- Do not cover MnemCode controls or memory evidence
- If the webcam background is distracting, use a full-screen camera scene instead for the specified 12-second segment

### Audio

- Mic/Aux: presenter's microphone
- Desktop audio: muted
- Sample rate: 48 kHz
- Mic peaks: between -12 dB and -6 dB
- Noise suppression: RNNoise, if available
- Compressor: optional, ratio 3:1
- Limiter: -2 dB
- Perform a ten-second test and listen back before the final take

### Recording

- Recording format: MKV
- Encoder: hardware H.264 if available; otherwise x264
- Quality: high quality, medium file size
- After recording: `File → Remux Recordings` and convert the MKV to MP4
- Do not record directly to MP4; an OBS crash can corrupt it

## Cursor rules

- Move deliberately, never in circles.
- Park the cursor in empty cream space while narration is the focus.
- Do not hover over leaves unless the script requests it.
- Do not open Archive controls.
- Do not drag the tree.
- Do not scroll the entire page while the cursor is over the MnemTree.
- Scroll only inside the panel currently being demonstrated.
- Use one click per action and wait for the state to settle.
- Never click `Open draft PR` or any publication control.

## Exact recording timeline

The presenter begins speaking immediately after OBS starts recording. Luna follows the action column. If the presenter is more than three seconds behind, Luna pauses cursor movement until the narration catches up.

### Shot 1 — the product in one frame

**Time:** 0:00–0:18  
**OBS scene:** Product  
**Browser tab:** 1, MnemTree  
**Starting frame:** Full populated tree, top header and MnemCode panel visible, page at the top

**Luna actions**

1. Start OBS recording.
2. Wait one second without moving the cursor.
3. Move the cursor slowly from the MnemAgent logo toward the center of the tree.
4. Stop in empty space to the left of the trunk.
5. Do not click anything.

**Presenter narration**

> Most agents are good for one conversation. Then the session ends, and the decisions that made them useful disappear. MnemAgent gives OpenClaw persistent memory, but it does not simply save every message.

**Required screen evidence**

- MnemAgent logo
- Populated living tree
- `62 memories`
- MnemCode panel

### Shot 2 — inspect a memory

**Time:** 0:18–0:43  
**OBS scene:** Product  
**Browser tab:** 1

**Luna actions**

1. Click the `Search memories` field.
2. Type `backend framework` at a natural speed.
3. Pause for one second after results settle.
4. Click the exact result or leaf labelled `backend framework FastAPI.`
5. Move the cursor into the Memory Lens below the tree.
6. Scroll only enough to expose the selected statement and its relationship context.
7. Pause for two seconds.

**Presenter narration**

> Each leaf is a durable belief. I can search the archive, select one, and inspect its scope, confidence, and relationships. The tree is the audit surface for what the agent currently believes.

**Required screen evidence**

- Search query visibly entered
- Matching memory selected
- Memory Lens populated
- Relationship chain visible

### Shot 3 — explain bounded memory

**Time:** 0:43–0:58  
**OBS scene:** Product  
**Browser tab:** 1

**Luna actions**

1. Clear the search field using Ctrl+A and Backspace.
2. Wait for the full tree to return.
3. Move the cursor to empty space and keep it still.

**Presenter narration**

> Storage is selective, contradictions replace only the matching scoped belief, and inactive memories decay. Retrieval is bounded too. No matter how large the archive becomes, at most six useful memories enter the model context for a turn.

### Shot 4 — cross-session recall

**Time:** 0:58–1:27  
**OBS scene:** Product  
**Browser tab:** 2, private MnemCode workspace

**Luna actions**

1. Switch to tab 2 with Ctrl+2 or by clicking its tab.
2. Ensure the private access code is nowhere on screen.
3. Show the completed first message that asked the agent to remember the WebPort rule.
4. Scroll inside the chat panel to the fresh-conversation recall question.
5. Stop with the answer containing both `backward compatibility` and `regression test` visible.
6. Point once to the recovered rule, then move the cursor away.

**Presenter narration**

> Before recording, I gave the agent a repository-specific rule for WebPort: preserve backward compatibility and add a regression test before changing behavior. Then I started a fresh OpenClaw conversation. There is no shared transcript here. The new session recovered the rule through MnemAgent's repository-scoped memory.

**Required screen evidence**

- Original durable-rule message
- Fresh-conversation recall question
- Correct recovered rule
- Sponsored model label

### Shot 5 — optional presenter camera

**Time:** 1:27–1:39  
**OBS scene:** Presenter  
**Browser tab:** 2 remains behind the camera

**Luna actions**

1. Switch to the Presenter scene exactly after the words `repository-scoped memory`.
2. Hold the scene without cursor movement.
3. Switch back to Product when the presenter finishes the sentence below.

**Presenter narration**

> This is the part I care about: memory should change the next action, not merely produce a convincing answer about the past.

**If the presenter does not want camera**

Stay on the recovered-rule screen and do not change any timing.

### Shot 6 — the coding agent acts on memory

**Time:** 1:39–2:14  
**OBS scene:** Product  
**Browser tab:** 2

**Luna actions**

1. Switch to the completed issue #14 run.
2. Click the `Activity` tab.
3. Scroll slowly through issue inspection, workspace preparation, source edit, and test events.
4. Pause when both test commands show success.
5. Click the `Memory` tab.
6. Pause on the repository-scoped rule for two seconds.
7. Click the `Changes` tab.
8. Position the panel so the regression test and implementation diff are both represented.
9. Do not scroll faster than the presenter can describe the evidence.

**Presenter narration**

> MnemCode turns that memory into action. For the prepared WebPort issue, OpenClaw inspects bounded files, retrieves scoped memory, writes a regression test, makes the smallest source change, and runs fixed tests in a no-network runner. Activity, memory, and the exact diff are separate, auditable evidence.

**Required screen evidence**

- Activity events
- Passing tests
- Repository-scoped memory
- Non-empty source and test diff

### Shot 7 — human approval boundary

**Time:** 2:14–2:27  
**OBS scene:** Product  
**Browser tab:** 2, then 3

**Luna actions**

1. Scroll to the review/publication control.
2. Point at the disabled or unselected approval control.
3. Do not select it.
4. Switch to tab 3 showing WebPort draft PR #15 Files changed.
5. Pause with the source file and regression test visible.

**Presenter narration**

> Publication is a separate human decision. A run cannot open a pull request until its tests pass and the reviewer approves that exact diff. This is the pre-validated draft PR produced by the same workflow.

### Shot 8 — benchmark evidence

**Time:** 2:27–2:40  
**OBS scene:** Product  
**Browser tab:** 4, benchmarks

**Luna actions**

1. Switch to tab 4.
2. Scroll beforehand or during the first second so the best-result table is centered.
3. Keep `66.7 vs 23.7` and `76.9% vs 38.5%` visible.
4. If possible, also show the live Qwen project-continuity row `91.7 vs 8.3`.
5. Do not scroll through raw logs.

**Presenter narration**

> MnemBench v2 measures the same lifecycle across sessions. The latest stable Postgres run scored 66.7 against a 23.7 stateless baseline. In a separate live Qwen run, project continuity scored 91.7 against 8.3. The repository includes the weaker and tied scenarios too.

### Shot 9 — architecture and cloud proof

**Time:** 2:40–2:54  
**OBS scene:** Product  
**Browser tabs:** 5, then 6

**Luna actions**

1. Switch to tab 5 showing the architecture image.
2. Hold for seven seconds.
3. Point briefly to Qwen Cloud, OpenClaw, MnemAgent MCP, and Postgres in that order.
4. Switch to tab 6 showing the Alibaba ECS screenshot.
5. Hold with `MnemAgentServer`, `Running`, Singapore, and the spot-instance billing line visible.

**Presenter narration**

> The core is provider-neutral: OpenClaw calls MnemAgent through MCP, and Postgres with pgvector stores the graph. Qwen Cloud is the primary integration and evaluation path. The public sponsored demo uses DeepSeek so judges need no key. The backend is running on this Alibaba ECS spot instance in Singapore.

### Shot 10 — closing frame

**Time:** 2:54–3:00  
**OBS scene:** Product  
**Browser tab:** 1

**Luna actions**

1. Switch back to tab 1.
2. Show the complete tree and MnemCode panel.
3. Park the cursor beside the trunk.
4. Stop OBS recording one second after narration ends.

**Presenter narration**

> MnemTree shows the memory. MnemBench measures it. MnemCode proves that remembered experience changes what the agent does.

## Full narration without production notes

Use this section for rehearsal or a teleprompter.

> Most agents are good for one conversation. Then the session ends, and the decisions that made them useful disappear. MnemAgent gives OpenClaw persistent memory, but it does not simply save every message.
>
> Each leaf is a durable belief. I can search the archive, select one, and inspect its scope, confidence, and relationships. The tree is the audit surface for what the agent currently believes.
>
> Storage is selective, contradictions replace only the matching scoped belief, and inactive memories decay. Retrieval is bounded too. No matter how large the archive becomes, at most six useful memories enter the model context for a turn.
>
> Before recording, I gave the agent a repository-specific rule for WebPort: preserve backward compatibility and add a regression test before changing behavior. Then I started a fresh OpenClaw conversation. There is no shared transcript here. The new session recovered the rule through MnemAgent's repository-scoped memory.
>
> This is the part I care about: memory should change the next action, not merely produce a convincing answer about the past.
>
> MnemCode turns that memory into action. For the prepared WebPort issue, OpenClaw inspects bounded files, retrieves scoped memory, writes a regression test, makes the smallest source change, and runs fixed tests in a no-network runner. Activity, memory, and the exact diff are separate, auditable evidence.
>
> Publication is a separate human decision. A run cannot open a pull request until its tests pass and the reviewer approves that exact diff. This is the pre-validated draft PR produced by the same workflow.
>
> MnemBench v2 measures the same lifecycle across sessions. The latest stable Postgres run scored 66.7 against a 23.7 stateless baseline. In a separate live Qwen run, project continuity scored 91.7 against 8.3. The repository includes the weaker and tied scenarios too.
>
> The core is provider-neutral: OpenClaw calls MnemAgent through MCP, and Postgres with pgvector stores the graph. Qwen Cloud is the primary integration and evaluation path. The public sponsored demo uses DeepSeek so judges need no key. The backend is running on this Alibaba ECS spot instance in Singapore.
>
> MnemTree shows the memory. MnemBench measures it. MnemCode proves that remembered experience changes what the agent does.

## Luna master instruction

Give Luna the entire text below together with this document.

```text
You are the screen-recording operator for a three-minute hackathon demo. You have no authority to change source code, cloud settings, GitHub content, Devpost fields, credentials, quotas, or the product's data beyond the two explicitly provided private chat messages and the prepared coding run.

Read docs/DEMO_VIDEO_PRODUCTION_SCRIPT.md completely before touching OBS or Chrome. Follow its pre-stage checklist, OBS settings, tab order, cursor rules, exact shot timeline, and recovery rules. The human presenter supplies all narration. Do not speak.

Never reveal or record the judge access code. Never open .env files, cloud billing, API-key pages, password managers, browser profiles, or terminal history. Never click Open draft PR, approve publication, submit Devpost, merge a pull request, or alter cloud resources.

Before the final take, perform one silent rehearsal without recording. Confirm that the populated tree, completed cross-session recall, completed issue #14 evidence, PR #15, benchmark table, architecture image, and Alibaba proof are all loaded. Confirm microphone levels with the presenter.

Record in OBS as MKV at 1920x1080 and 30 fps. Follow the timestamps as a target, but prioritize matching the presenter's spoken transitions. When the take ends, stop recording, verify the file plays, remux it to MP4, and report the absolute MKV and MP4 paths plus their durations. Do not upload the video anywhere unless the user separately asks you to.
```

## Recovery rules during recording

### If the tree is empty

1. Stop the take.
2. Reopen `https://47-237-140-12.sslip.io/?user=demo-brain`.
3. Wait for 62 memories.
4. Restart from shot 1.

### If search does not return the expected leaf

1. Clear the query.
2. Search `FastAPI` instead.
3. Select the result stating that FastAPI is the backend framework.
4. Continue without mentioning the change.

### If chat or coding output is still running

1. Stop the take.
2. Wait off-camera for completion.
3. Do not narrate a spinner or uncertain result.
4. Restart the take with the completed state pre-staged.

### If the live coding run fails

1. Do not approve anything.
2. Use the completed Activity evidence if it remains available.
3. Otherwise show PR #15 and state only that it is the pre-validated run.
4. Do not claim the failed attempt passed.

### If the spot server is unavailable

1. Do not record a broken live page.
2. Wait for the owner to restore the deployment.
3. If time is critical, record the populated README screenshot, PR #15, benchmark table, architecture image, and Alibaba proof as a transparent evidence-only cut.

### If narration timing slips

- Less than three seconds: Luna pauses cursor movement.
- Three to eight seconds: shorten the hold on the next static evidence shot.
- More than eight seconds: stop and restart the take.
- Never speed-scroll to catch up.

### If the presenter misspeaks

- A small natural correction is acceptable.
- A wrong score, provider, deployment claim, or security claim requires a restart.
- Never call the public DeepSeek run a Qwen run.

## Final quality check

Before giving the MP4 to the user, Luna verifies all of the following:

- Duration is between 2:50 and 3:05.
- Resolution is 1920 × 1080.
- Audio is present in both channels and never clips.
- No access code or credential appears in any frame.
- The opening frame shows the populated MnemTree.
- Search and memory selection are visibly demonstrated.
- Cross-session recall shows both parts of the WebPort rule.
- Activity, Memory, Changes, passing tests, and a real diff are shown.
- No publication action occurs.
- PR #15 is described as pre-validated evidence.
- Benchmark numbers match the narration.
- Qwen and DeepSeek paths are distinguished.
- Alibaba ECS proof shows the running instance.
- The last frame returns to the complete product.
- The MP4 plays from beginning to end after remuxing.

## Suggested filenames

- OBS source: `mnemagent-demo-2026-07-20.mkv`
- Final upload: `mnemagent-qwen-cloud-demo.mp4`
- Optional rehearsal: `mnemagent-demo-rehearsal.mkv`

Keep the rehearsal and final file separate so the wrong take cannot be uploaded accidentally.
