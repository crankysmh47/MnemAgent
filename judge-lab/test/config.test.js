import test from 'node:test';
import assert from 'node:assert/strict';
import { loadConfig, parsePositiveInteger } from '../src/config.js';

test('uses safe defaults', () => {
  assert.deepEqual(loadConfig({}), { timeoutMs: 2_000, maxBodyBytes: 16_384 });
});

test('parses positive integer values', () => {
  assert.equal(parsePositiveInteger('12', 1), 12);
  assert.throws(() => parsePositiveInteger('1.5', 1), /positive integer/);
  assert.throws(() => parsePositiveInteger('0', 1), /positive integer/);
});
