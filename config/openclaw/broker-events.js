const clip = (value, max) => String(value ?? '').slice(0, max);

export function projectBrokerEvent(name, args, result) {
  if (name === 'list_issues') return { type: 'issue.inspected', detail: { count: Array.isArray(result?.issues) ? result.issues.length : 0 } };
  if (name === 'create_workspace') return { type: 'workspace.created', detail: { workspaceId: clip(result?.id, 100), branch: clip(result?.branch, 200) } };
  if (name === 'read_workspace_file') return { type: 'file.read', detail: { path: clip(args?.path, 300) } };
  if (name === 'apply_workspace_patch') return { type: 'patch.applied', detail: { files: Number(result?.files || 0), changedLines: Number(result?.changedLines || 0) } };
  if (name === 'replace_workspace_text') return { type: 'source.changed', detail: { path: clip(args?.path, 300), changedLines: Number(result?.changedLines || 0) } };
  if (name === 'run_workspace_tests') return { type: 'test.completed', detail: { commandId: clip(args?.commandId, 80), exitCode: Number(result?.exitCode ?? 1), output: clip(result?.output, 12_000) } };
  if (name === 'show_workspace_diff') return { type: 'diff.ready', detail: { diff: clip(result?.diff, 60_000) } };
  if (name === 'cleanup_workspace') return { type: 'workspace.cleaned', detail: { workspaceId: clip(args?.workspaceId, 100) } };
  return null;
}
