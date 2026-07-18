const REQUIRED_TESTS = ['numeric-command-test', 'test-unit'];

export function recordTestEvidence(store, workspaceId, commandId, exitCode) {
  const workspace = store.get(workspaceId) || new Map();
  workspace.set(String(commandId), Number(exitCode) === 0);
  store.set(workspaceId, workspace);
}

export function hasRequiredTestEvidence(store, workspaceId) {
  const workspace = store.get(workspaceId);
  return Boolean(workspace && REQUIRED_TESTS.every(commandId => workspace.get(commandId) === true));
}
