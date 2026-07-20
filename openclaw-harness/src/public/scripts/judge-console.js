import { judgeApi } from './judge-api.js';

const TERMINAL = new Set(['completed', 'failed']);
const activityKey = namespace => `mnemagent:judge-activity:${namespace}`;

function saveActivity(namespace, runId, state) {
  if (!namespace || typeof localStorage === 'undefined') return;
  localStorage.setItem(activityKey(namespace), JSON.stringify({ runId, state }));
}

function loadActivity(namespace) {
  if (!namespace || typeof localStorage === 'undefined') return null;
  try { return JSON.parse(localStorage.getItem(activityKey(namespace)) || 'null'); } catch { return null; }
}

export function reduceJudgeState(state, event, snapshot = {}) {
  const duplicate = event.id && state.events.some(existing => existing.id === event.id);
  const events = duplicate ? state.events : [...state.events, event].sort((a, b) => Number(a.sequence || 0) - Number(b.sequence || 0));
  const next = {
    ...state,
    events,
    quota: snapshot.quota ?? state.quota,
    evidence: snapshot.evidence ?? state.evidence,
  };
  if (event.type === 'run.started') next.status = 'running';
  if (event.type === 'assistant.message') next.message = event.detail?.text || '';
  if (event.type === 'run.completed') next.status = 'completed';
  if (event.type === 'run.failed') next.status = 'failed';
  return next;
}

export async function restoreJudgeSession(api) {
  try {
    const session = await api.session();
    return session?.authenticated ? session : null;
  } catch {
    return null;
  }
}

function setText(node, value) { if (node) node.textContent = value == null ? '' : String(value); }

function addActivity(list, event) {
  const item = document.createElement('li');
  const label = document.createElement('strong');
  label.textContent = String(event.type || 'event').replaceAll('.', ' ');
  const detail = document.createElement('span');
  detail.textContent = event.detail?.text || event.detail?.message || event.detail?.path || event.detail?.commandId || '';
  item.append(label, detail);
  list.append(item);
}

function addChat(log, role, message) {
  log.querySelector('.chat-empty')?.remove();
  const item = document.createElement('article');
  item.className = `chat-message chat-message-${role}`;
  const label = document.createElement('strong');
  label.textContent = role === 'user' ? 'You' : 'Memory agent';
  const body = document.createElement('p');
  body.textContent = message;
  item.append(label, body);
  log.append(item);
  log.scrollTop = log.scrollHeight;
}

function renderQuota(node, quota) {
  if (!node || !quota) return;
  node.hidden = false;
  node.replaceChildren();
  const entries = [
    ['Chat', quota.chatTurnsRemaining],
    ['Code run', quota.codingRunsRemaining],
    ['Draft PR', quota.publicationsRemaining],
    ['Session', '7 days'],
  ];
  for (const [label, value] of entries) {
    const item = document.createElement('span');
    const strong = document.createElement('strong');
    strong.textContent = String(value);
    item.append(strong, document.createTextNode(label));
    node.append(item);
  }
}

function renderEvidence(root, evidence = {}) {
  const memories = root.querySelector('[data-memory-evidence]');
  const tests = root.querySelector('[data-test-evidence]');
  const diff = root.querySelector('[data-diff]');
  memories.replaceChildren();
  tests.replaceChildren();
  for (const memory of evidence.memories || []) {
    const item = document.createElement('li');
    const scope = document.createElement('strong');
    scope.textContent = memory.scope || 'repository memory';
    const value = document.createElement('span');
    value.textContent = memory.value || '';
    item.append(scope, value);
    memories.append(item);
  }
  for (const test of evidence.tests || []) {
    const item = document.createElement('li');
    item.className = test.passed ? 'passed' : 'failed';
    item.textContent = `${test.passed ? 'Passed' : 'Failed'} · ${test.commandId || 'test command'}`;
    tests.append(item);
  }
  setText(diff, evidence.diff || '');
  root.querySelector('[data-memory-empty]').hidden = Boolean(memories.children.length);
  root.querySelector('[data-changes-empty]').hidden = Boolean(tests.children.length || evidence.diff);
  const approval = root.querySelector('[data-approve-pr]');
  approval.hidden = !evidence.readyForApproval || Boolean(evidence.pr);
  const prLink = root.querySelector('[data-pr-link]');
  if (evidence.pr?.url) {
    prLink.href = evidence.pr.url;
    prLink.hidden = false;
  }
}

async function poll(read, id, onSnapshot, timeoutMs = 370_000) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    const snapshot = await read(id);
    onSnapshot(snapshot);
    if (TERMINAL.has(snapshot.status)) return snapshot;
    await new Promise(resolve => window.setTimeout(resolve, 900));
  }
  throw new Error('The run is still active. Its evidence remains available in this workspace.');
}

async function showPrivateTree(namespace) {
  const switchTree = () => window.mnemArchive?.changeUser(namespace);
  if (window.mnemArchive) await switchTree();
  else window.addEventListener('mnemagent:archive-ready', switchTree, { once: true });
  const url = new URL(window.location.href);
  url.searchParams.set('user', namespace);
  window.history.replaceState({}, '', url);
}

export async function createJudgeConsole({ root, api = judgeApi } = {}) {
  if (!root) return null;
  const accessForm = root.querySelector('[data-judge-access]');
  const shell = root.querySelector('[data-judge-shell]');
  const chatForm = root.querySelector('[data-judge-chat]');
  const runForm = root.querySelector('[data-judge-run]');
  const activity = root.querySelector('[data-activity]');
  const chatLog = root.querySelector('[data-chat-log]');
  const status = root.querySelector('[data-judge-status]');
  const model = root.querySelector('[data-model]');
  const quotaNode = root.querySelector('[data-sponsored-quota]');
  let runId = null;
  let namespace = null;
  let state = { status: 'idle', events: [], quota: null, evidence: null };

  async function activateSession(session, { restored = false } = {}) {
    namespace = session.namespace;
    accessForm.hidden = true;
    shell.hidden = false;
    renderQuota(quotaNode, session.quota);
    if (restored) {
      chatLog.replaceChildren();
      for (const turn of session.chatHistory || []) {
        if (turn.message) addChat(chatLog, 'user', turn.message);
        if (turn.response) addChat(chatLog, 'assistant', turn.response);
      }
      if (session.latestRun) {
        runId = session.latestRun.id;
        state = { status: session.latestRun.status, events: [], quota: session.quota, evidence: session.latestRun.evidence };
        for (const eventItem of session.latestRun.events || []) state = reduceJudgeState(state, eventItem, session.latestRun);
        activity.replaceChildren();
        state.events.forEach(eventItem => addActivity(activity, eventItem));
        renderEvidence(root, session.latestRun.evidence);
      } else {
        const saved = loadActivity(session.namespace);
        if (saved?.state) {
          runId = saved.runId || null;
          state = saved.state;
          activity.replaceChildren();
          for (const eventItem of state.events || []) addActivity(activity, eventItem);
          renderEvidence(root, state.evidence || {});
        }
      }
    }
    setText(status, restored ? 'Private workspace restored. Your memory and conversation are ready.' : 'Private workspace ready. Teach the agent a preference first.');
    await showPrivateTree(session.namespace);
  }

  const scenarios = await api.scenarios();
  setText(model, scenarios.model || 'DeepSeek V4 Flash');

  for (const tab of root.querySelectorAll('[data-tab]')) tab.addEventListener('click', () => {
    for (const candidate of root.querySelectorAll('[data-tab]')) candidate.setAttribute('aria-selected', String(candidate === tab));
    for (const panel of root.querySelectorAll('[data-panel]')) panel.hidden = panel.dataset.panel !== tab.dataset.tab;
  });

  const restoredSession = await restoreJudgeSession(api);
  if (restoredSession) await activateSession(restoredSession, { restored: true });

  accessForm.addEventListener('submit', async event => {
    event.preventDefault();
    const button = accessForm.querySelector('button');
    button.disabled = true;
    try {
      const session = await api.login(new FormData(accessForm).get('accessCode'));
      await activateSession(session);
    } catch (error) { setText(status, error.message); button.disabled = false; }
  });

  chatForm.addEventListener('submit', async event => {
    event.preventDefault();
    const button = chatForm.querySelector('button');
    const message = String(new FormData(chatForm).get('message') || '').trim();
    if (!message) return;
    button.disabled = true;
    addChat(chatLog, 'user', message);
    chatForm.reset();
    setText(status, 'A fresh agent session is recalling your private memory…');
    try {
      const created = await api.chat({ message });
      const snapshot = await poll(api.chatTurn, created.id, current => renderQuota(quotaNode, current.quota));
      if (snapshot.status === 'failed') throw new Error(snapshot.error || 'The chat turn failed.');
      addChat(chatLog, 'assistant', snapshot.response || snapshot.message || 'Memory updated.');
      renderQuota(quotaNode, snapshot.quota);
      setText(status, 'Reply complete. The tree is refreshing with any durable memories.');
      await window.mnemArchive?.refresh(true);
    } catch (error) { setText(status, error.message); }
    finally { button.disabled = false; }
  });

  runForm.addEventListener('submit', async event => {
    event.preventDefault();
    const button = root.querySelector('[data-run-coding]');
    button.disabled = true;
    activity.replaceChildren();
    state = { status: 'running', events: [], quota: state.quota, evidence: null };
    setText(status, 'The agent is recalling conventions and opening an isolated workspace…');
    try {
      const created = await api.start({ issueNumber: 1, message: String(new FormData(runForm).get('message') || '') });
      runId = created.id;
      const snapshot = await poll(api.run, runId, current => {
        for (const eventItem of current.events || []) state = reduceJudgeState(state, eventItem, current);
        activity.replaceChildren();
        state.events.forEach(eventItem => addActivity(activity, eventItem));
        renderQuota(quotaNode, current.quota);
        renderEvidence(root, current.evidence);
        saveActivity(namespace, runId, state);
      });
      if (snapshot.status === 'failed') throw new Error(snapshot.error || 'The coding run failed.');
      setText(status, snapshot.evidence?.readyForApproval ? 'Run complete. Review Memory and Changes, then approve the draft PR.' : 'Run complete. Evidence is available for review.');
    } catch (error) { setText(status, error.message); }
    finally { button.disabled = false; }
  });

  root.querySelector('[data-approve-pr]').addEventListener('submit', async event => {
    event.preventDefault();
    const form = event.currentTarget;
    const button = form.querySelector('button');
    button.disabled = true;
    try {
      const snapshot = await api.approve(runId, { confirmed: form.elements.confirmed.checked });
      renderQuota(quotaNode, snapshot.quota);
      renderEvidence(root, snapshot.evidence);
      state = { ...state, evidence: snapshot.evidence, quota: snapshot.quota };
      saveActivity(namespace, runId, state);
      setText(status, 'Draft PR opened. Publication remained gated until your explicit approval.');
    } catch (error) { setText(status, error.message); button.disabled = false; }
  });

  return { getState: () => ({ ...state }), getRunId: () => runId };
}

if (typeof document !== 'undefined') createJudgeConsole({ root: document.querySelector('#agentWorkbench') }).catch(() => {});
