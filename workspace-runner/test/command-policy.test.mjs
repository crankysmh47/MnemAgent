import test from 'node:test';
import assert from 'node:assert/strict';
import { validateCommand } from '../command-policy.js';

test('allows only fixed test and node-check commands', () => {
  assert.deepEqual(validateCommand({ commandId: 'test' }), { argv: ['npm', 'test'] });
  assert.deepEqual(validateCommand({ commandId: 'node-check', testNamePattern: 'src/config.js' }), { argv: ['node', '--check', 'src/config.js'] });
  assert.throws(() => validateCommand({ commandId: 'shell', testNamePattern: 'rm -rf /' }), /not allowed/);
});
