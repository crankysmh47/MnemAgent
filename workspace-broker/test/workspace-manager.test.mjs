import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { mkdtemp, rm, writeFile, mkdir } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { test } from 'node:test';
import { buildRunnerArgs, createWorkspaceManager } from '../src/workspace-manager.js';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);

test('runner mounts the shared workspace volume at the selected workspace', () => {
  const args = buildRunnerArgs({
    workspaceVolume: 'mnemagent-judge-workspaces',
    workspaceId: 'ws_example',
    runnerImage: 'runner:test',
  });
  assert.ok(args.includes('type=volume,source=mnemagent-judge-workspaces,target=/workspaces'));
  assert.ok(args.includes('WORKSPACE_ROOT=/workspaces/ws_example'));
  assert.ok(!args.some(value => value.includes('/workspaces/ws_example:/workspace')));
  assert.equal(args.at(-1), 'runner:test');
});

test('manager enforces repository allowlist and one active workspace', async () => {
  const root = await mkdtemp(path.join(os.tmpdir(), 'mnemcode-'));
  const fixture = path.join(root, 'fixture');
  await mkdir(fixture);
  await writeFile(path.join(fixture, 'README.md'), 'fixture');
  const manager = createWorkspaceManager({ root: path.join(root, 'runs'), allowedRepository: 'crankysmh47/WebPort', clone: async (_repo, target) => { await mkdir(path.join(target, 'src'), { recursive: true }); await writeFile(path.join(target, 'README.md'), 'fixture'); await writeFile(path.join(target, 'src/config.js'), 'export const value = 1;\n'); await execFileAsync('git', ['init'], { cwd: target }); await execFileAsync('git', ['config', 'user.name', 'fixture'], { cwd: target }); await execFileAsync('git', ['config', 'user.email', 'fixture@example.test'], { cwd: target }); await execFileAsync('git', ['add', '.'], { cwd: target }); await execFileAsync('git', ['commit', '-m', 'fixture'], { cwd: target }); } });
  await assert.rejects(manager.create({ repository: 'other/repo', issueNumber: 1 }), /allowlist/i);
  const session = await manager.create({ repository: 'crankysmh47/WebPort', issueNumber: 1 });
  assert.match(session.branch, /^mnemagent-judge\/1\//);
  assert.equal(await manager.readFile(session.id, 'README.md'), 'fixture');
  await assert.rejects(manager.readFile(session.id, '../secret'), /path/i);
  await manager.applyPatch(session.id, '--- a/src/config.js\n+++ b/src/config.js\n@@ -1 +1 @@\n-export const value = 1;\n+export const value = 2;\n');
  assert.match(await manager.diff(session.id), /value = 2/);
  await manager.applyPatch(session.id, '--- /dev/null\n+++ b/tests/new-test.js\n@@ -0,0 +1 @@\n+export const first = true;\n');
  await manager.applyPatch(session.id, '--- a/tests/new-test.js\n+++ b/tests/new-test.js\n@@ -1 +1 @@\n-export const first = true;\n+export const first = false;\n');
  assert.match(await manager.diff(session.id), /first = false/);
  await manager.replaceText(session.id, { path: 'src/config.js', oldText: 'export const value = 2;', newText: 'export const value = 3;' });
  assert.match(await manager.diff(session.id), /value = 3/);
  await assert.rejects(manager.replaceText(session.id, { path: 'src/config.js', oldText: 'missing', newText: 'unsafe' }), /exactly once/i);
  assert.ok((await manager.listFiles(session.id)).includes('src/config.js'));
  await assert.rejects(manager.create({ repository: 'crankysmh47/WebPort', issueNumber: 2 }), /active workspace/i);
  await manager.cleanup(session.id);
  await rm(root, { recursive: true, force: true });
});
