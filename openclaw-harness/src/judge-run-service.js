const { execFile } = require('node:child_process');
const { randomUUID } = require('node:crypto');
const { readFileSync } = require('node:fs');
const path = require('node:path');
const { promisify } = require('node:util');
const { createJudgeEventLog } = require('./judge-events');

const execFileAsync = promisify(execFile);

function parseOpenClawResponse(response) {
  const text = (response.payloads || response.result?.payloads || []).map(item => item?.text).filter(Boolean).join('\n')
    || response.output || response.text || 'The agent completed without a textual response.';
  const rawUsage = response.meta?.agentMeta?.usage || response.meta?.usage || response.usage || {};
  const input = Math.max(0, Number(rawUsage.input || rawUsage.inputTokens || 0));
  const output = Math.max(0, Number(rawUsage.output || rawUsage.outputTokens || 0));
  const total = Math.max(0, Number(rawUsage.total || rawUsage.totalTokens || input + output));
  const usageUsd = Math.max(0, Number(rawUsage.cost?.total || response.meta?.usage?.cost?.total || response.usage?.cost || 0));
  return { text: String(text), usageTokens: { input, output, total }, usageUsd: Number.isFinite(usageUsd) ? usageUsd : 0 };
}

function safeRun(run) {
  const { ownerSessionId: _owner, task: _task, ...publicRun } = run;
  return { ...publicRun };
}

async function openClawExecutor({ sessionId, message, model, namespace, runId, contractPath, agentId = 'judge-coder' }) {
  let operatingContract = '';
  try { operatingContract = readFileSync(contractPath || process.env.JUDGE_AGENT_PROMPT_PATH || path.join(__dirname, '../../config/openclaw/judge-coder.md'), 'utf8'); } catch { /* deployment validation checks the mounted prompt */ }
  const identityContract = `\nPrivate MnemAgent user ID: ${namespace}. Every memory tool call MUST use exactly this user ID. Current run ID: ${runId}. Never reveal either identifier as a credential.`;
  const boundedMessage = `${operatingContract}${identityContract}\n\nCurrent judge request:\n${message}`.slice(0, 24_000);
  const { stdout } = await execFileAsync('openclaw', [
    'agent', '--local', '--agent', agentId, '--json', '--session-id', sessionId, '--model', model,
    '--thinking', 'off', '--timeout', '360', '--message', boundedMessage,
  ], {
    timeout: 370_000,
    maxBuffer: 2_000_000,
    windowsHide: true,
    env: { ...process.env, MNEMCODE_RUN_ID: runId || '', MNEMCODE_JUDGE_NAMESPACE: namespace || '' },
  });
  return parseOpenClawResponse(JSON.parse(stdout));
}

function createJudgeRunService({
  model = process.env.JUDGE_MODEL || 'deepseek-api/deepseek-v4-flash',
  hardBudgetTokens = Number(process.env.JUDGE_MODEL_HARD_TOKEN_BUDGET || 2_000_000),
  executor = openClawExecutor,
  replayText = 'Validated public evidence: MnemBench issue #1 was solved with repository memory, three regression tests, one bounded scoring fix, and two passing Python commands. Draft PR: https://github.com/crankysmh47/MnemBench/pull/2',
} = {}) {
  const runs = new Map();
  const log = createJudgeEventLog();
  let spentUsd = 0;
  let spentTokens = 0;
  let activeRunId = null;
  const owned = (id, ownerSessionId) => {
    const run = runs.get(id);
    if (!run || run.ownerSessionId !== ownerSessionId) throw new Error('Judge run not found.');
    return run;
  };
  const emit = (id, type, detail = {}) => log.append(id, { type, detail });
  return {
    create({ ownerSessionId, namespace, sessionId, issueNumber, message }) {
      if (!/^jss_[A-Za-z0-9_-]{3,100}$/.test(String(ownerSessionId || ''))) throw new Error('A judge owner session is required.');
      if (!/^judge-[A-Za-z0-9_-]{3,100}$/.test(String(namespace || ''))) throw new Error('A private judge namespace is required.');
      if (!/^[A-Za-z0-9_-]{3,100}$/.test(String(sessionId || ''))) throw new Error('A valid OpenClaw session ID is required.');
      if (Number(issueNumber) !== 1) throw new Error('Only prepared issue 1 is available.');
      if (!String(message || '').trim() || String(message).length > 4_000) throw new Error('A bounded run direction is required.');
      if (activeRunId) throw new Error('A coding run is already active.');
      const id = `run_${randomUUID()}`;
      const mode = spentTokens >= hardBudgetTokens ? 'replay' : 'live';
      const run = { id, ownerSessionId, namespace, sessionId, issueNumber: 1, model, mode, status: 'running', createdAt: new Date().toISOString(), usageUsd: 0, usageTokens: { input: 0, output: 0, total: 0 } };
      runs.set(id, run);
      activeRunId = id;
      emit(id, 'run.started', { issueNumber: 1, mode });
      run.task = (async () => {
        try {
          emit(id, mode === 'live' ? 'model.started' : 'replay.started', { model });
          const result = mode === 'live'
            ? await executor({ sessionId, message: String(message), model, namespace, runId: id })
            : { text: replayText, usageUsd: 0 };
          run.usageUsd = Math.max(0, Number(result.usageUsd || 0));
          run.usageTokens = result.usageTokens || { input: 0, output: 0, total: 0 };
          spentUsd += run.usageUsd;
          spentTokens += Math.max(0, Number(run.usageTokens.total || 0));
          emit(id, 'assistant.message', { text: String(result.text || '').slice(0, 24_000) });
          run.status = 'completed';
          emit(id, 'run.completed', { usageUsd: run.usageUsd, usageTokens: run.usageTokens.total });
        } catch {
          run.status = 'failed';
          emit(id, 'run.failed', { message: 'The live coding run stopped. The validated replay remains available.' });
        } finally { if (activeRunId === id) activeRunId = null; }
        return safeRun(run);
      })();
      return safeRun(run);
    },
    get(id, ownerSessionId) { return safeRun(owned(id, ownerSessionId)); },
    events(id, ownerSessionId, afterId = null) { owned(id, ownerSessionId); return log.after(id, afterId); },
    wait(id) { const run = runs.get(id); if (!run) throw new Error('Judge run not found.'); return run.task; },
    appendEvidence(id, ownerSessionId, event) { owned(id, ownerSessionId); return emit(id, event.type, event.detail); },
    appendInternal(id, event) { if (!runs.has(id)) throw new Error('Judge run not found.'); return emit(id, event.type, event.detail); },
    budget() { return { spentUsd, spentTokens, hardBudgetTokens, locked: spentTokens >= hardBudgetTokens }; },
  };
}

module.exports = { createJudgeRunService, openClawExecutor, parseOpenClawResponse };
