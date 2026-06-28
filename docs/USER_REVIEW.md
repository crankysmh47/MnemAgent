# MnemAgent — User Review & Testing Guide

## What you are testing

You are not testing a standalone chatbot. You are testing **OpenClaw with a persistent memory layer (MnemOS)** attached.

| Piece | What it is | How you use it |
|-------|------------|----------------|
| **OpenClaw frontend** | Chat UI / CLI | `openclaw dashboard` or `openclaw agent` |
| **OpenClaw gateway** | Agent runtime on port **18789** | Started automatically during setup |
| **MnemOS memory API** | Brain / SQLite + vectors on port **8000** | Must be running (“awake”) for memory to work |
| **MCP bridge** | 7 memory tools OpenClaw calls | Registered as server `mnemos` |
| **Memory visualizer** (optional but recommended) | Live graph at port **3000** | Watch memories appear as you chat |

**Normal OpenClaw agent:** each session starts fresh; it only knows what is in the current conversation.

**MnemAgent:** the agent is instructed to call `memory_search` before answering personal/history questions, `memory_store` when you teach it facts, and `memory_dump` when you ask what it remembers. Those facts persist across sessions and can be seen in the visualizer.

---

## Prerequisites (local review — not needed after cloud deploy)

| Tool | Version | Check |
|------|---------|-------|
| **Git** | any recent | `git --version` |
| **Docker Desktop** | Engine 24+ | `docker info` |
| **Node.js** | 20+ | `node --version` |
| **Python** | 3.11+ | `python --version` (setup script uses it; Docker runs the memory server) |

**Platform notes**

- **Linux / macOS:** follow the bash path below.
- **Windows:** **WSL 2 + Ubuntu is strongly recommended** (`bash scripts/setup.sh`). Native PowerShell works but is a second-class path (see Windows section).

You also need a **free trial LLM API key** from [DashScope](https://dashscope.aliyuncs.com) (default in the project).

---

## First-time setup (exact steps)

### Path A — Linux / macOS / WSL (recommended)

**1. Clone the repo**

```bash
git clone https://github.com/crankysmh47/MnemAgent.git
cd MnemAgent
```

**2. Configure API key**

```bash
cp config/env.template .env
```

Edit `.env` and set:

```
QWEN_API_KEY=sk-your-real-dashscope-key-here
```

Leave the DashScope defaults unless instructed otherwise.

**3. One-command setup** (first run: **2–5 minutes** while Docker builds)

```bash
bash scripts/setup.sh
```

This automatically:

- Creates Python `.venv` and installs deps
- Builds and starts Docker: memory (`:8000`), MCP (`:8001`), visualizer (`:3000`)
- Seeds a demo memory graph (`demo-brain`) for the visualizer
- Installs OpenClaw globally (`npm install -g openclaw`)
- Onboards OpenClaw with your API key
- Registers the **7 MnemOS MCP tools**
- Copies agent instructions into `~/.openclaw/workspace/`
- Starts the OpenClaw gateway on `:18789`
- Verifies MCP probe

**4. Confirm everything is healthy**

```bash
curl -s http://localhost:8000/health    # {"status":"ok",...}
curl -s http://localhost:8001/health    # {"status":"ok",...}
openclaw gateway health
openclaw mcp probe mnemos               # should report 7 tools
```

**5. Open the chat frontend**

```bash
openclaw dashboard
```

This opens the OpenClaw web UI in your browser. Chat with agent `main`.

Alternative: terminal chat

```bash
openclaw agent --agent main --message "Hello"
# or
openclaw tui
```

**6. (Recommended) Open the memory visualizer in a second tab**

```
http://localhost:3000?user=demo-brain
```

Use your own user id later (see below) once you start storing personal memories.

---

### Path B — Windows PowerShell (if not using WSL)

**1–2.** Same clone + `.env` as above.

**3. Start the memory stack**

```powershell
docker compose up -d --build
```

Wait until `http://localhost:8000/health` returns `"status":"ok"`.

**4. Install OpenClaw + register memory**

```powershell
npm install -g openclaw@latest
.\scripts\setup-openclaw.ps1
```

**5. Daily launcher (after first setup)**

```powershell
.\scripts\launch.ps1
```

---

## Daily startup (after first setup)

Memory must be “awake” before chatting.

**Linux / macOS / WSL:**

```bash
bash scripts/dev.sh
```

**Windows PowerShell:**

```powershell
.\scripts\launch.ps1
```

Then:

```bash
openclaw dashboard
```

Quick sanity check:

```bash
openclaw gateway health
openclaw mcp probe mnemos
```

---

## How to talk to the agent (the actual user flow)

1. **Start Docker + gateway** (`dev.sh` or `launch.ps1`).
2. **Open OpenClaw dashboard** (`openclaw dashboard`).
3. **Chat normally** — teach facts in plain language, ask recall questions, use `/memory` when you want a dump.
4. **Optionally watch the graph** at `http://localhost:3000/visualizer?user=<your-user-id>`.

### Your personal user id

Setup creates a stable id at:

- Linux/macOS/WSL: `~/.openclaw/mnemos-user-id.txt`
- Windows: `%USERPROFILE%\.openclaw\mnemos-user-id.txt`

Paste that into the visualizer **User** field to see *your* memories (not just `demo-brain`).

### Built-in commands to try

| You type | Expected agent behavior |
|----------|-------------------------|
| “I prefer Python for backend APIs.” | Calls `memory_store`, confirms naturally |
| “What language should I use for APIs?” (new session) | Calls `memory_search`, answers from memory |
| “Actually I prefer Go now.” | Stores correction; old fact overwritten |
| `/memory` | Calls `memory_dump`, summarizes stored beliefs |
| `/memory stats` | Calls `memory_stats`, shows UCB optimization info |

### Automated proof scripts (optional)

If something feels broken, run:

```powershell
.\scripts\prove-openclaw.ps1   # end-to-end OpenClaw → MCP → memory
.\scripts\prove-memory.ps1     # memory API + harness chat
.\scripts\submission-test.ps1  # full project smoke suite
```

---

## What is different from a normal OpenClaw agent?

Ask the tester to compare against a **plain OpenClaw install with no MnemOS MCP**. MnemAgent should feel different in these ways:

| Dimension | Normal OpenClaw | MnemAgent (MnemOS) |
|-----------|-----------------|---------------------|
| **Cross-session recall** | Forgets after session ends | Remembers taught facts in new sessions |
| **Tool use** | General tools only | Uses 7 `memory_*` MCP tools behind the scenes |
| **Answer grounding** | Generic LLM knowledge | Searches stored beliefs before answering personal questions |
| **Corrections** | Only in chat context | Overwrites contradictions in the memory graph |
| **Noise filtering** | N/A | Tentative “maybe…” facts often **not** stored (conviction gate) |
| **Transparency** | Opaque | `/memory`, visualizer, live graph updates |
| **Response style** | May leak JSON / internals | Instructed **not** to leak raw memory JSON |
| **Identity** | Per-session | `memory_resolve_user` binds you to a stable `user_id` |

---

## Test checklist (do not skip sections)

### A. Setup & infrastructure

- [ ] Clone + `.env` with valid API key completes without errors
- [ ] `docker compose up` brings up all three services (`8000`, `8001`, `3000`)
- [ ] First setup finishes in reasonable time (< 10 min on a normal machine)
- [ ] `openclaw mcp probe mnemos` reports **7 tools**
- [ ] `openclaw dashboard` loads and accepts messages
- [ ] **Daily restart:** stop Docker, run `dev.sh`/`launch.ps1`, confirm chat still works
- [ ] If gateway was down, does restarting fix it? (`openclaw gateway restart --force`)

### B. First-run UX

- [ ] Is it clear what to do after setup? (dashboard vs visualizer)
- [ ] Are error messages understandable if Docker is not running?
- [ ] Does the agent respond at all on first message (API key valid)?
- [ ] Free-model latency: note if responses feel slow or time out (> 2 min)

### C. Memory storage (teaching)

Test each in a **fresh session** where possible.

- [ ] **Firm preference:** “I always use Python for backend work.” → stored, natural confirmation
- [ ] **Persona fact:** “I'm a FAST student.” → stored under persona
- [ ] **Project fact:** “Our project codename is Atlas.” → retrievable later
- [ ] **Tentative / weak fact:** “Maybe we could try Vue for the dashboard someday.” → should **not** become a strong stored preference (salience gate)
- [ ] **Sensitive data:** give a fake password/API key → agent should **refuse** to store it
- [ ] Visualizer: new nodes appear within ~5–10 s after storing (refresh if paused)

### D. Memory recall (the core value)

Use **new sessions** (close/reopen dashboard or new `--session-id` in CLI).

- [ ] Ask about a taught preference → answer references **your** fact, not generic advice
- [ ] Ask “What university am I from?” after teaching FAST → mentions FAST
- [ ] Ask something **never taught** → agent admits uncertainty or asks; does not invent a stored memory
- [ ] Ask a **personal question unrelated to memory** (e.g. “What's the capital of France?”) → answers normally, no forced memory search noise
- [ ] **No JSON leak:** responses must not contain raw `{"entity":...}` blobs

### E. Corrections & forgetting behavior

- [ ] Teach “I prefer Python” → then “Actually I prefer Rust now” → recall should say **Rust**
- [ ] Old value should not dominate in `/memory` dump
- [ ] Contradiction feels natural in conversation (not “database updated” robotic tone)

### F. Commands & transparency

- [ ] `/memory` returns a readable summary of stored beliefs
- [ ] `/memory stats` returns optimization/UCB info (or a sensible explanation)
- [ ] “What do you remember about me?” works without the slash command
- [ ] Visualizer **User** field: switching user ids shows different graphs

### G. Cross-session & persistence

- [ ] Teach facts → **fully quit** dashboard/browser → restart stack → recall still works
- [ ] Same facts visible in visualizer after restart
- [ ] Second day: run `dev.sh` only → memory from day 1 still there

### H. OpenClaw frontend UX

- [ ] Dashboard: message input, scrolling, multi-turn conversation
- [ ] Responses feel conversational (per SOUL.md: concise, honest about memory limits)
- [ ] Long messages / follow-ups don't break the thread
- [ ] Tool-call delays: note if user waits noticeably while memory searches run
- [ ] CLI parity: `openclaw agent --agent main --message "..."` behaves like dashboard

### I. Visualizer UX (port 3000)

- [ ] `http://localhost:3000?user=demo-brain` loads pre-seeded demo graph
- [ ] Live stream / refresh shows new events when you chat
- [ ] Click a node → conviction, utility, recall history visible
- [ ] Category filters (preference / persona / system) work
- [ ] Export button produces usable output
- [ ] Page usable on your screen size (no broken layout)

### J. Failure modes (important for review)

- [ ] **Memory down:** stop Docker → send chat message → note error quality (graceful vs cryptic)
- [ ] **Bad API key:** note error message clarity
- [ ] Gateway running but MCP broken → what does the user see?

### K. Optional channel scripts (only if enabled)

Skip unless the team configured tokens in `.env`:

- Telegram / Discord / WhatsApp scripts in `scripts/add-*.ps1`
- Cross-channel: same `user_id` should share memory

---

## Feedback questions for the tester (please answer in prose)

Copy these into your review form:

### 1. Overall first impression

- How long did setup take? Where did you get stuck?
- Was it obvious that **OpenClaw dashboard** is the chat UI and **:3000** is the memory map?

### 2. Memory vs normal chatbot

- After teaching 3–4 personal facts and opening a **new session**, does it feel like the agent **knows you**?
- Compared to ChatGPT / a plain OpenClaw agent, what felt **better**? What felt **worse**?

### 3. Personal & stored-memory questions

- When you ask about something **you already taught**, how confident and specific is the answer?
- When you ask something **personal but never stored** (favorite color, birthday), does it hallucinate or ask?
- Does it **blend** stored facts into answers naturally, or does it feel like reading a database aloud?

### 4. Tone & trust

- Does the agent feel honest when it **doesn't** remember something?
- Any moments where it claimed to remember something you never said?
- Any raw JSON, tool names, or “memory_store was called” leakage?

### 5. Corrections

- When you corrected a fact, did the new answer feel seamless?
- Did `/memory` reflect the correction?

### 6. Latency & friction

- How long between sending a message and getting a reply?
- Is the wait acceptable given memory search + free model?
- Would you use this daily in current form?

### 7. Visualizer value

- Did watching the graph change how you understood what the agent “remembers”?
- Was it helpful or distracting during chat?

### 8. Deal-breakers before cloud deploy

- What would stop you from recommending this to another user?
- Top 3 UX fixes you'd prioritize.

---

## Quick reference card

```
FIRST TIME:
  git clone … && cd MnemAgent
  cp config/env.template .env   # add QWEN_API_KEY
  bash scripts/setup.sh         # WSL/Linux/macOS
  # OR: docker compose up -d && .\scripts\setup-openclaw.ps1  # Windows

EVERY SESSION:
  bash scripts/dev.sh           # or .\scripts\launch.ps1
  openclaw dashboard            # CHAT HERE
  http://localhost:3000/visualizer?user=<your-id>   # WATCH MEMORY

VERIFY:
  openclaw gateway health
  openclaw mcp probe mnemos     # 7 tools
  curl http://localhost:8000/health

PROVE IT WORKS:
  .\scripts\prove-openclaw.ps1
```

---

## Note on cloud deployment (for context)

For this review, testers **do** need Docker locally so the memory layer runs on their machine. After cloud deploy, the expected flow simplifies to:

1. Open a hosted URL (or `openclaw dashboard` pointed at a hosted gateway)
2. Chat — no clone, no Docker, no Python venv

The **behavior under test stays the same**; only the infrastructure moves off the laptop.

---

## Related documentation

| Doc | Contents |
|-----|----------|
| [SETUP.md](SETUP.md) | Full setup, troubleshooting, architecture |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Waking/dreaming, schema, data flow |
| [README.md](../README.md) | Project overview and quick start |
