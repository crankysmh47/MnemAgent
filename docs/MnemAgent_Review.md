# MnemAgent — User Review

**Tester:** Asad
**Platform:** Windows (native PowerShell, not WSL)
**Model used:** Started on OpenRouter free bundle, later switched off it because it kept stalling
**Overall:** The memory layer *stores* facts, but it cannot reliably *recall* them across sessions. Setup on native Windows was rough. Details below.

---

## Short summary (read this first)

I got the system fully running and tested it as a normal user would. The good news: teaching the agent a fact works, and it stores it. The core problem: when I open a new session and ask for that fact back, the agent does **not** return it. Memory search is switched off because of an embedding/index mismatch, and when search fails the agent falls back to a pre-filled profile file that contains demo data ("FAST student") which I never told it. So it confidently gives a **wrong** answer about me.

In its current state I would not recommend it to another user yet. The idea is good and storage works, but recall — which is the whole point — is broken.

---

## 1. Overall first impression

**Setup time:** About 1.5 hours of actual configuration work to get everything running. (Spread across more wall-clock time because of debugging.)

**Where I got stuck:** Native Windows (PowerShell) was painful. The main blockers:

- The setup script tried to register the memory tools with an old command (`openclaw mcp add`) that my installed OpenClaw version no longer supports — it now uses `openclaw mcp set`. So registration silently did nothing and the `mnemos` server never got added. I had to register it by hand.
- The API key handling was confusing. Editing `.env` did not fix auth, because OpenClaw reads its key from its own credential store, not `.env`. I had to log in through OpenClaw directly.
- The OpenRouter login uses a browser OAuth flow that returns to `localhost:3000` — but port 3000 is already taken by the project's own visualizer container, so the login failed with "Cannot GET /openrouter-oauth/callback." I had to stop that container, log in, then restart it.
- The MCP memory calls timed out at first and I had to bump the timeout and re-register.

None of this is in the guide. A normal Windows user following the instructions would be stuck very early.

**Was it clear what to do after setup (dashboard vs :3000)?** Reasonably, yes. The guide is clear that `openclaw dashboard` is the chat and `:3000` is the memory map. That part was fine. The problem was getting *to* that point, not understanding it once there.

---

## 2. Memory vs a normal chatbot

Honestly, in its current state it does **not** feel like the agent knows me — and that's the most important takeaway.

I taught it clear facts (e.g. "I study at NUST"). It confirmed and stored them. But when I opened a **new session** and asked "Where do I study?", it did not recall NUST. Instead it either gave a wrong answer ("FAST") or lost the thread entirely and treated it like a location question, suggesting I "check a maps app."

So compared to a plain chatbot:

- **Better:** Within a single session it confirms facts naturally and doesn't dump raw JSON at you. When it genuinely doesn't know something, it admits it instead of making something up (mostly — see the trust section).
- **Worse:** The one thing it's supposed to do better than a normal chatbot — remember me across sessions — is exactly the thing that failed. A normal chatbot at least doesn't pretend to have a memory. This one promises memory and then gives a confidently wrong answer, which is worse than no memory at all.

---

## 3. Personal and stored-memory questions

**Asking about something I taught:** It failed to recall it in a new session. Storage worked (I could see the fact get stored, and a node sometimes appeared in the visualizer), but retrieval did not bring it back. The agent's own memory-search tool returned an error saying it was **disabled** ("index metadata is missing — memory search is paused because the index was built with different embedding settings").

**Asking something personal I never taught:** This part was good. It admitted it didn't know rather than inventing an answer. That's the right behavior.

**Does it blend facts in naturally or read like a database?** When it works inside a session, it blends naturally and sounds conversational — no robotic "database updated" tone, no JSON. So the presentation layer is fine. The problem is purely that the right facts don't come back.

**Important catch:** When recall failed, the agent read a pre-filled profile file (`USER.md`) that ships with demo content saying "FAST student." It then told me I study at FAST — something I never said, and which contradicts what I actually taught (NUST). So it didn't just fail to remember; it substituted demo data as if it were my real memory.

---

## 4. Tone and trust

**Is it honest when it doesn't remember?** Mixed. For a fact I never taught, yes — it honestly said it didn't know. But for a fact I *did* teach, it didn't say "I couldn't find that in memory." Instead it gave the wrong answer (FAST) with confidence, and separately blamed a fake technical cause ("the memory index is out of sync, you need an OpenAI API key, run `openclaw memory index --force`"). That advice is wrong and would send a user down a useless path. (It turned out this exact wrong advice is built into the memory tool's own error message, so the agent is just relaying it.)

**Did it ever claim to remember something I never said?** Yes — the "FAST student" answer. This is the most serious trust problem. For a memory product, confidently stating a wrong personal fact is a deal-breaker.

**Any raw JSON / tool-name leakage?** No. In normal replies it stayed clean and conversational. The internals were only visible when I deliberately expanded the tool-activity panel, which is fine.

---

## 5. Corrections and the `/memory` command

**Not tested.** I did not run the correction test (teach Python → correct to Rust) or the `/memory` / `/memory stats` commands.

The reason: both of these depend on memory search working, and memory search was disabled the whole time (the index error above). A correction would fail at the recall step, and `/memory` likely hits the same disabled-search wall. So I marked these as **blocked by the search bug** rather than test something I already knew couldn't succeed.

---

## 6. Latency and friction

This was a real problem, and I have evidence for it.

On the default free model, the agent regularly **stalled for 2–6 minutes** with no reply. The gateway logs showed sessions hanging and then being force-aborted by a "stuck session recovery" — one run sat for 378 seconds before the system killed it, and a session write-lock blew past its own 300-second limit. So the "no reply" wasn't my imagination; the free model genuinely hangs and the gateway has to abort it.

After I switched off the free model, short replies came back fast and storage worked smoothly. So the latency is mostly the free-tier model, not the app itself — but since the free model is the **default** the project ships with, a new tester will hit these stalls immediately.

**Would I use it daily in current form?** No. Between the broken recall and the free-model stalls, it's not usable day-to-day yet.

---

## 7. Visualizer value

The visualizer loaded fine and the demo graph worked. For my own user, I **sometimes** saw a node appear after I taught a fact, which was satisfying and did help me trust that storage was happening.

But it was also misleading at times: it often showed 0 memories even after I'd taught facts, because the user id in the visualizer didn't always match the id the agent stored under. So I'd be looking at an empty graph while facts existed under a different id. Helpful when it matched; confusing when it didn't.

Overall: a nice idea and useful for confirming storage, but the user-id mismatch made it unreliable as a source of truth.

---

## 8. Deal-breakers before cloud deploy

**What would stop me recommending this to another user right now:** Cross-session recall doesn't work, and worse, the agent gives confidently wrong personal facts (the "FAST" demo data) when recall fails. For a memory product, that's the core promise broken plus a trust failure on top.

**Top 3 fixes I'd prioritize:**

1. **Fix memory search / the embedding-index mismatch.** Right now `memory_search` returns "disabled — index metadata is missing," so stored facts can never be retrieved. Nothing else matters until this works. Stored is not the same as recallable.

2. **Remove or stop relying on the seeded `USER.md` demo profile ("FAST student").** When search fails, the agent reads this file and presents demo data as the user's real memory, contradicting what they actually taught. This should never override real user input.

3. **Fix the misleading error advice and stop shipping the stalling free model as the default.** The "run `openclaw memory index --force` / add an OpenAI key" advice is wrong and useless for this setup, and the default free model hangs for minutes. Both make a first-time user think they did something wrong when they didn't.

**Bonus (setup fixes for Windows):** Update the registration command from `mcp add` to `mcp set`, document the `localhost:3000` OAuth port clash with the visualizer, and clarify that the API key goes through `openclaw` auth, not just `.env`.

---

## Coverage note (what I did and didn't test)

**Tested:** setup/install (native Windows), first reply, teaching/storing a fact, cross-session recall, "never-taught" question, latency/stalls, visualizer, failure behavior (bad key, timeouts), trust/honesty.

**Not tested (blocked by the disabled search bug):** the correction flow (Python → Rust), the `/memory` and `/memory stats` commands, multi-day persistence, and the optional channel tests (Telegram/Discord/WhatsApp).

I stopped at this point because the central feature (recall) was confirmed broken with clear evidence, and the remaining tests all depend on it working. Happy to continue once search is fixed.
