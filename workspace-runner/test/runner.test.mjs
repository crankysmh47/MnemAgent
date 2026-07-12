import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { test } from 'node:test';

function invoke(request) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, ['runner.js'], {
      cwd: new URL('..', import.meta.url),
      stdio: ['pipe', 'pipe', 'pipe'],
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

test('CLI accepts one JSON request and returns one JSON response', async () => {
  const result = await invoke({ commandId: 'node-check', testNamePattern: 'test/fixture.js' });
  assert.equal(result.code, 0, result.stderr);
  const response = JSON.parse(result.stdout);
  assert.equal(response.ok, true);
  assert.equal(response.exitCode, 0);
});

test('CLI rejects malformed requests without executing a shell', async () => {
  const result = await invoke({ commandId: 'shell', command: 'echo unsafe' });
  assert.equal(result.code, 1);
  const response = JSON.parse(result.stdout);
  assert.equal(response.ok, false);
  assert.match(response.error, /not allowed/i);
});
