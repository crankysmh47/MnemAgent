const SENSITIVE_KEY = /authorization|cookie|secret|token|password|api.?key|credential/i;
const ALLOWED_TYPES = new Set([
  'issue.inspected', 'workspace.created', 'file.read', 'patch.applied', 'source.changed',
  'test.completed', 'diff.ready', 'memory.retrieved', 'workspace.cleaned',
]);
const REQUIRED_TESTS = ['python-scoring-test', 'python-unit'];

function sanitizeEvidenceEvent(event) {
  if (!event || !ALLOWED_TYPES.has(event.type) || !event.detail || typeof event.detail !== 'object' || Array.isArray(event.detail)) throw new Error('Evidence event is invalid.');
  for (const key of Object.keys(event.detail)) if (SENSITIVE_KEY.test(key)) throw new Error('Sensitive evidence fields are forbidden.');
  const encoded = JSON.stringify(event.detail);
  if (encoded.length > 64_000) throw new Error('Evidence event is too large.');
  return { type: event.type, detail: JSON.parse(encoded), timestamp: event.timestamp || new Date().toISOString() };
}

function createJudgeEvidenceStore() {
  const runs = new Map();
  const entry = runId => {
    if (!runs.has(runId)) runs.set(runId, { workspaceId: null, branch: null, files: [], tests: [], memories: [], diff: '', pr: null });
    return runs.get(runId);
  };
  return {
    ingest(runId, rawEvent) {
      if (!/^run_[A-Za-z0-9-]+$/.test(String(runId || ''))) throw new Error('Evidence run ID is invalid.');
      const event = sanitizeEvidenceEvent(rawEvent);
      const value = entry(runId);
      if (event.type === 'workspace.created') {
        value.workspaceId = String(event.detail.workspaceId || '').slice(0, 100);
        value.branch = String(event.detail.branch || '').slice(0, 200);
      }
      if (event.type === 'file.read') value.files.push(String(event.detail.path || '').slice(0, 300));
      if (event.type === 'test.completed') value.tests.push({ commandId: String(event.detail.commandId || ''), passed: Number(event.detail.exitCode) === 0, exitCode: Number(event.detail.exitCode), output: String(event.detail.output || '').slice(0, 12_000) });
      if (event.type === 'diff.ready') value.diff = String(event.detail.diff || '').slice(0, 60_000);
      if (event.type === 'memory.retrieved') value.memories.push({ scope: String(event.detail.scope || '').slice(0, 300), entity: String(event.detail.entity || '').slice(0, 300), relation: String(event.detail.relation || '').slice(0, 200), value: String(event.detail.value || '').slice(0, 2_000), retrievedAt: event.timestamp });
      return event;
    },
    get(runId) {
      const value = entry(runId);
      const latestTests = new Map();
      for (const test of value.tests) latestTests.set(test.commandId, test);
      const latestTestResults = [...latestTests.values()];
      const requiredTestsPassed = REQUIRED_TESTS.every(commandId => latestTests.get(commandId)?.passed === true);
      return { ...value, files: [...new Set(value.files)], tests: value.tests.map(item => ({ ...item })), memories: value.memories.map(item => ({ ...item })), readyForApproval: Boolean(value.workspaceId && value.diff.trim() && requiredTestsPassed) };
    },
    setPr(runId, pr) { entry(runId).pr = { url: pr.url, number: pr.number, draft: true }; return this.get(runId); },
  };
}

module.exports = { createJudgeEvidenceStore, sanitizeEvidenceEvent };
