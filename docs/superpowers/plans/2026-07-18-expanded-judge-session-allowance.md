# Expanded Judge Session Allowance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Increase each judge session to 30 chat turns, 5 coding runs, and 5 draft-PR publication allowances.

**Architecture:** `openclaw-harness/src/judge-session-store.js` remains the sole quota authority. It initializes the higher allowance and restores against the corresponding higher reserve ceiling; the API and existing browser quota renderer continue to consume its returned snapshot. Documentation reflects the same values.

**Tech Stack:** Node.js CommonJS, Node built-in test runner, Markdown.

## Global Constraints

- Keep judge sessions at one hour and permit only one global coding run at a time.
- Keep chat reserve at `$0.01` and coding reserve at `$0.05`.
- Keep draft PR approval gates unchanged: passing evidence, non-empty diff, explicit confirmation, unused publication allowance, and current diff-bound approval token.
- Keep the global model token budget and sponsored-session cap as independent deployment controls.

---

### Task 1: Raise and enforce session allowances

**Files:**
- Modify: `openclaw-harness/test/judge-session-store.test.mjs:7-29`
- Modify: `openclaw-harness/src/judge-session-store.js:1-74`

**Interfaces:**
- Consumes: `createJudgeSessionStore({ now, ttlMs, maxSessions })`.
- Produces: the unchanged `create`, `reserve`, `release`, `settle`, and `consumePublication` API with quota snapshots of `{ chatTurnsRemaining, codingRunsRemaining, publicationsRemaining, reservedUsdRemaining }`.

- [ ] **Step 1: Write the failing test**

Replace the initial allowance assertion and consumption loops with:

```js
assert.deepEqual(session.quota, { chatTurnsRemaining: 30, codingRunsRemaining: 5, publicationsRemaining: 5, reservedUsdRemaining: 0.55 });
for (let i = 0; i < 30; i += 1) store.reserve('jss_owner', 'chat');
assert.throws(() => store.reserve('jss_owner', 'chat'), /allowance/i);
for (let i = 0; i < 5; i += 1) store.reserve('jss_owner', 'coding');
assert.throws(() => store.reserve('jss_owner', 'coding'), /allowance/i);
for (let i = 0; i < 5; i += 1) store.consumePublication('jss_owner');
assert.throws(() => store.consumePublication('jss_owner'), /allowance/i);
assert.deepEqual(store.get('jss_owner').quota, { chatTurnsRemaining: 0, codingRunsRemaining: 0, publicationsRemaining: 0, reservedUsdRemaining: 0 });
```

Also change the release assertion to `assert.equal(store.get('jss_owner').quota.chatTurnsRemaining, 30);`.

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test openclaw-harness/test/judge-session-store.test.mjs`

Expected: FAIL because the store still creates a quota of 3 chats, 1 coding run, 1 publication, and `$0.10`.

- [ ] **Step 3: Write minimal implementation**

In `openclaw-harness/src/judge-session-store.js`, add these constants beneath the existing reserve constants:

```js
const CHAT_TURN_LIMIT = 30;
const CODING_RUN_LIMIT = 5;
const PUBLICATION_LIMIT = 5;
const SESSION_RESERVE_USD = 0.55;
```

Replace the initial quota with:

```js
quota: {
  chatTurnsRemaining: CHAT_TURN_LIMIT,
  codingRunsRemaining: CODING_RUN_LIMIT,
  publicationsRemaining: PUBLICATION_LIMIT,
  reservedUsdRemaining: SESSION_RESERVE_USD,
},
```

Replace the hard-coded release ceiling with:

```js
entry.quota.reservedUsdRemaining = Number(Math.min(SESSION_RESERVE_USD, entry.quota.reservedUsdRemaining + cost).toFixed(2));
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test openclaw-harness/test/judge-session-store.test.mjs`

Expected: all three session-store tests PASS.

- [ ] **Step 5: Commit**

```bash
git add openclaw-harness/src/judge-session-store.js openclaw-harness/test/judge-session-store.test.mjs
git commit -m "feat: expand judge session allowance"
```

### Task 2: Align judge-facing copy

**Files:**
- Modify: `README.md:61`
- Modify: `docs/MNEMCODE_DEMO.md:55`
- Modify: `docs/superpowers/specs/2026-07-18-sponsored-judge-experience-design.md:15-18,94,99`

**Interfaces:**
- Consumes: the server-defined 30/5/5 allowance and `$0.55` reserve from Task 1.
- Produces: consistent judge documentation; no runtime behavior.

- [ ] **Step 1: Update copy**

Replace the README sentence with:

```markdown
2. Enter the private judge access code. This creates a random one-hour memory namespace with 30 chat turns, 5 coding runs, and 5 draft-PR approvals.
```

Replace the MnemCode demo allowance bullet with:

```markdown
- 30 chat turns, 5 coding runs, and 5 draft publications per judge session
```

In the sponsored-experience design, replace the three-turn/one-run/one-publication allowance and `$0.10` reserve with 30/5/5 and `$0.55`; update the acceptance criteria to require 30 chat turns to be available.

- [ ] **Step 2: Verify documentation**

Run: `rg -n "three chat|one sponsored coding|one draft-PR|\$0\.10|3 chat turns|1 coding run" README.md docs/MNEMCODE_DEMO.md docs/superpowers/specs/2026-07-18-sponsored-judge-experience-design.md`

Expected: no stale allowance claims.

- [ ] **Step 3: Run focused verification**

Run: `node --test openclaw-harness/test/judge-session-store.test.mjs`

Expected: all three session-store tests PASS.

- [ ] **Step 4: Commit**

```bash
git add README.md docs/MNEMCODE_DEMO.md
git add -f docs/superpowers/specs/2026-07-18-sponsored-judge-experience-design.md docs/superpowers/plans/2026-07-18-expanded-judge-session-allowance.md
git commit -m "docs: describe expanded judge allowance"
```
