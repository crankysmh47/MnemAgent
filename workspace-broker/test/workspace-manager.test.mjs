import assert from 'node:assert/strict';
import { mkdtemp, rm, writeFile, mkdir } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { test } from 'node:test';
import { createWorkspaceManager } from '../src/workspace-manager.js';

test('manager enforces repository allowlist and one active workspace', async () => {
  const root = await mkdtemp(path.join(os.tmpdir(), 'mnemcode-'));
  const fixture = path.join(root, 'fixture');
  await mkdir(fixture);
  await writeFile(path.join(fixture, 'README.md'), 'fixture');
  const manager = createWorkspaceManager({ root: path.join(root, 'runs'), allowedRepository: 'crankysmh47/WebPort', clone: async (_repo, target) => { await mkdir(target, { recursive: true }); await writeFile(path.join(target, 'README.md'), 'fixture'); } });
  await assert.rejects(manager.create({ repository: 'other/repo', issueNumber: 1 }), /allowlist/i);
  const session = await manager.create({ repository: 'crankysmh47/WebPort', issueNumber: 1 });
  assert.match(session.branch, /^mnemagent-judge\/1\//);
  await assert.rejects(manager.create({ repository: 'crankysmh47/WebPort', issueNumber: 2 }), /active workspace/i);
  await manager.cleanup(session.id);
  await rm(root, { recursive: true, force: true });
});
