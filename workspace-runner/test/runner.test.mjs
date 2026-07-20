import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdtemp, mkdir, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { test } from 'node:test';

function invoke(request, workspaceRoot) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, ['runner.js'], {
      cwd: new URL('..', import.meta.url),
      stdio: ['pipe', 'pipe', 'pipe'],
      env: { ...process.env, WORKSPACE_ROOT: workspaceRoot || '' },
    });
    let stdout = '';
    let stderr = '';
    child.stdout.on('data', (chunk) => { stdout += chunk; });
    child.stderr.on('data', (chunk) => { stderr += chunk; });
    child.once('error', reject);
    child.once('close', (code) => resolve({ code, stdout, stderr }));
    child.stdin.end(`${JSON.stringify(request)}\n`);
  });
}

test('CLI accepts the fixed Python request and returns one JSON response', async () => {
  const root = await mkdtemp(path.join(os.tmpdir(), 'mnemcode-runner-'));
  await mkdir(path.join(root, 'tests'));
  await writeFile(path.join(root, 'tests', 'test_scoring.py'), 'def test_fixture():\n    assert True\n');
  const result = await invoke({ commandId: 'python-scoring-test' }, root);
  const response = JSON.parse(result.stdout);
  assert.equal(typeof response.exitCode, 'number');
  assert.doesNotMatch(response.output, /not allowed/i);
  await rm(root, { recursive: true, force: true });
});

test('CLI rejects malformed requests without executing a shell', async () => {
  const result = await invoke({ commandId: 'shell', command: 'echo unsafe' });
  assert.equal(result.code, 1);
  const response = JSON.parse(result.stdout);
  assert.equal(response.ok, false);
  assert.match(response.error, /not allowed/i);
});
