import assert from 'node:assert/strict';
import { test } from 'node:test';
import evidenceModule from '../src/judge-evidence.js';

const { createJudgeEvidenceStore, sanitizeEvidenceEvent } = evidenceModule;

test('evidence store captures workspace, tests, diff, memory, and rejects sensitive fields', () => {
  const store = createJudgeEvidenceStore();
  store.ingest('run_one', { type: 'workspace.created', detail: { workspaceId: 'ws_123', branch: 'mnemagent-judge/11/123' } });
  store.ingest('run_one', { type: 'memory.retrieved', detail: { scope: 'repository/crankysmh47/WebPort', value: 'Use user-safe errors.' } });
  store.ingest('run_one', { type: 'test.completed', detail: { commandId: 'test-unit', exitCode: 0, output: 'all pass' } });
  store.ingest('run_one', { type: 'diff.ready', detail: { diff: '--- a/src/x.cpp\n+++ b/src/x.cpp' } });
  const evidence = store.get('run_one');
  assert.equal(evidence.workspaceId, 'ws_123');
  assert.equal(evidence.tests[0].passed, true);
  assert.match(evidence.diff, /src\/x\.cpp/);
  assert.equal(evidence.memories[0].scope, 'repository/crankysmh47/WebPort');
  assert.throws(() => sanitizeEvidenceEvent({ type: 'test.completed', detail: { token: 'secret' } }), /sensitive/i);
});

test('evidence is ready only with a workspace, non-empty diff, and both required tests passing', () => {
  const store = createJudgeEvidenceStore();
  store.ingest('run_one', { type: 'workspace.created', detail: { workspaceId: 'ws_123' } });
  store.ingest('run_one', { type: 'diff.ready', detail: { diff: 'patch' } });
  assert.equal(store.get('run_one').readyForApproval, false);
  store.ingest('run_one', { type: 'test.completed', detail: { commandId: 'test-unit', exitCode: 0, output: 'pass' } });
  assert.equal(store.get('run_one').readyForApproval, false);
  store.ingest('run_one', { type: 'test.completed', detail: { commandId: 'numeric-command-test', exitCode: 0, output: 'pass' } });
  assert.equal(store.get('run_one').readyForApproval, true);
});

test('a later passing rerun supersedes an earlier red test for the same command', () => {
  const store = createJudgeEvidenceStore();
  store.ingest('run_one', { type: 'workspace.created', detail: { workspaceId: 'ws_123' } });
  store.ingest('run_one', { type: 'test.completed', detail: { commandId: 'test-unit', exitCode: 1, output: 'red' } });
  store.ingest('run_one', { type: 'test.completed', detail: { commandId: 'test-unit', exitCode: 0, output: 'green' } });
  store.ingest('run_one', { type: 'test.completed', detail: { commandId: 'numeric-command-test', exitCode: 0, output: 'green' } });
  store.ingest('run_one', { type: 'diff.ready', detail: { diff: 'patch' } });
  assert.equal(store.get('run_one').readyForApproval, true);
});
