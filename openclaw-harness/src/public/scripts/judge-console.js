import { judgeApi } from './judge-api.js';

export function reduceJudgeState(state, event) {
  if (event.id && state.events.some(existing => existing.id === event.id)) return state;
  const events = [...state.events, event].sort((a, b) => a.sequence - b.sequence);
  const next = { ...state, events };
  if (event.type === 'run.started') next.status = 'running';
  if (event.type === 'assistant.message') next.message = event.detail?.text || '';
  if (event.type === 'run.completed') next.status = 'completed';
  if (event.type === 'run.failed') next.status = 'failed';
  return next;
}

function addActivity(list, event) {
  const item = document.createElement('li');
  const label = document.createElement('strong');
  label.textContent = event.type.replaceAll('.', ' ');
  const detail = document.createElement('span');
  detail.textContent = event.detail?.text || event.detail?.message || '';
  item.append(label, detail);
  list.append(item);
}

export async function createJudgeConsole({ root, api = judgeApi } = {}) {
  if (!root) return null;
  const accessForm = root.querySelector('[data-judge-access]');
  const runForm = root.querySelector('[data-judge-run]');
  const scenarioSelect = root.querySelector('[data-scenario]');
  const activity = root.querySelector('[data-activity]');
  const status = root.querySelector('[data-judge-status]');
  const model = root.querySelector('[data-model]');
  let sessionId = `judge-${crypto.randomUUID()}`;
  const scenarios = await api.scenarios();
  model.textContent = scenarios.model;
  for (const scenario of scenarios.scenarios) {
    const option = document.createElement('option');
    option.value = scenario.issueNumber;
    option.textContent = `#${scenario.issueNumber} · ${scenario.title}`;
    scenarioSelect.append(option);
  }
  accessForm.addEventListener('submit', async event => {
    event.preventDefault();
    status.textContent = 'Opening the judge workspace…';
    try {
      await api.login(new FormData(accessForm).get('accessCode'));
      accessForm.hidden = true;
      runForm.hidden = false;
      status.textContent = 'Workspace ready. Choose a prepared task.';
    } catch (error) { status.textContent = error.message; }
  });
  runForm.addEventListener('submit', async event => {
    event.preventDefault();
    runForm.querySelector('button').disabled = true;
    activity.replaceChildren();
    status.textContent = 'The agent is reading issue and memory context…';
    try {
      const run = await api.start({ sessionId, issueNumber: Number(scenarioSelect.value), message: new FormData(runForm).get('message') });
      const snapshot = await api.run(run.id);
      snapshot.events.forEach(eventItem => addActivity(activity, eventItem));
      status.textContent = snapshot.status === 'completed' ? 'Run complete. Review the evidence before approving a draft PR.' : 'Run stopped.';
      sessionId = `judge-${crypto.randomUUID()}`;
    } catch (error) { status.textContent = error.message; }
    finally { runForm.querySelector('button').disabled = false; }
  });
  return { sessionId };
}

if (typeof document !== 'undefined') {
  createJudgeConsole({ root: document.querySelector('#agentWorkbench') }).catch(() => {});
}
