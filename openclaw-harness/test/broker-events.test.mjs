import assert from 'node:assert/strict';
import { test } from 'node:test';
import { projectBrokerEvent } from '../../config/openclaw/broker-events.js';

test('broker events expose bounded evidence without source or patch payloads', () => {
  assert.deepEqual(projectBrokerEvent('create_workspace', { repository: 'crankysmh47/WebPort', issueNumber: 11 }, { id: 'ws_1', branch: 'judge/1' }), { type: 'workspace.created', detail: { workspaceId: 'ws_1', branch: 'judge/1' } });
  assert.deepEqual(projectBrokerEvent('read_workspace_file', { workspaceId: 'ws_1', path: 'src/core/commands.cpp' }, { content: 'secret source' }), { type: 'file.read', detail: { path: 'src/core/commands.cpp' } });
  assert.deepEqual(projectBrokerEvent('run_workspace_tests', { commandId: 'test-unit' }, { exitCode: 0, output: 'pass' }), { type: 'test.completed', detail: { commandId: 'test-unit', exitCode: 0, output: 'pass' } });
  assert.deepEqual(projectBrokerEvent('show_workspace_diff', {}, { diff: 'patch' }), { type: 'diff.ready', detail: { diff: 'patch' } });
});
