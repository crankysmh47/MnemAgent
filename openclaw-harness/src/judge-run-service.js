const { execFile } = require('node:child_process');
const { randomUUID } = require('node:crypto');
const { readFileSync } = require('node:fs');
const { promisify } = require('node:util');
const { createJudgeEventLog } = require('./judge-events');

const execFileAsync = promisify(execFile);

async function openClawExecutor({ sessionId, message, model }) {
  let operatingContract = '';
  try { operatingContract = readFileSync(process.env.JUDGE_AGENT_PROMPT_PATH || require('node:path').join(__dirname, '../../config/openclaw/judge-coder.md'), 'utf8'); } catch { /* deployment validation checks the mounted prompt */ }
  const boundedMessage = `${operatingContract}\n\nCurrent judge request:\n${message}`.slice(0, 24_000);
  const { stdout } = await execFileAsync('openclaw', [
    'agent', '--local', '--agent', 'judge-coder', '--json', '--session-id', sessionId, '--model', model,
    '--thinking', 'off', '--timeout', '600', '--message', boundedMessage,
  ], { timeout: 620_000, maxBuffer: 2_000_000, windowsHide: true });
  const response = JSON.parse(stdout);
  const text = response.result?.payloads?.map(item => item.text).filter(Boolean).join('\n')
    || response.output || response.text || 'The agent completed without a textual response.';
  const usageUsd = Number(response.meta?.usage?.cost?.total || response.usage?.cost || 0);
  return { text, usageUsd: Number.isFinite(usageUsd) ? usageUsd : 0 };
}

function createJudgeRunService({
  model = process.env.JUDGE_MODEL || 'deepseek-api/deepseek-v4-flash',
  hardBudgetUsd = Number(process.env.JUDGE_MODEL_HARD_BUDGET_USD || 4.5),
  executor = openClawExecutor,
  replayText = 'Replay mode is active. The recorded agent run remains available without additional model spend.',
} = {}) {
  const runs = new Map();
  const log = createJudgeEventLog();
  let spentUsd = 0;
  let active = false;
  const emit = (id, type, detail = {}) => log.append(id, { type, detail });
  return {
    async create({ sessionId, issueNumber, message }) {
      if (active) throw new Error('A judge run is already active.');
      if (!/^[A-Za-z0-9_-]{3,100}$/.test(String(sessionId || ''))) throw new Error('A valid judge session ID is required.');
      if (!String(message || '').trim() || String(message).length > 12_000) throw new Error('A bounded run message is required.');
      const id = `run_${randomUUID()}`;
      const mode = spentUsd >= hardBudgetUsd ? 'replay' : 'live';
      const run = { id, sessionId, issueNumber: Number(issueNumber || 0), model, mode, status: 'running', createdAt: new Date().toISOString(), usageUsd: 0 };
      runs.set(id, run);
      emit(id, 'run.started', { issueNumber: run.issueNumber, mode });
      active = true;
      try {
        emit(id, mode === 'live' ? 'model.started' : 'replay.started', { model });
        const result = mode === 'live' ? await executor({ sessionId, message: String(message), model }) : { text: replayText, usageUsd: 0 };
        run.usageUsd = Math.max(0, Number(result.usageUsd || 0));
        spentUsd += run.usageUsd;
        emit(id, 'assistant.message', { text: String(result.text || '') });
        run.status = 'completed';
        emit(id, 'run.completed', { usageUsd: run.usageUsd, totalUsageUsd: spentUsd });
      } catch (error) {
        run.status = 'failed';
        emit(id, 'run.failed', { message: 'The coding agent could not complete this run.' });
        throw error;
      } finally { active = false; }
      return { ...run };
    },
    get(id) { const run = runs.get(id); return run ? { ...run } : null; },
    events(id, afterId = null) { return log.after(id, afterId); },
    budget() { return { spentUsd, hardBudgetUsd, locked: spentUsd >= hardBudgetUsd }; },
  };
}

module.exports = { createJudgeRunService, openClawExecutor };
