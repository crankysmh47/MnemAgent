import test from 'node:test';
import assert from 'node:assert/strict';
import { validateCommand } from '../command-policy.js';

test('allows the fixed MnemBench Python checks', () => {
  assert.deepEqual(validateCommand({ commandId: 'python-scoring-test' }), { argv: ['python', '-m', 'pytest', '-q', 'tests/test_scoring.py'] });
  assert.deepEqual(validateCommand({ commandId: 'python-unit' }), { argv: ['python', '-m', 'pytest', '-q'] });
  assert.throws(() => validateCommand({ commandId: 'test-unit' }), /not allowed/);
  assert.throws(() => validateCommand({ commandId: 'shell', testNamePattern: 'rm -rf /' }), /not allowed/);
});
