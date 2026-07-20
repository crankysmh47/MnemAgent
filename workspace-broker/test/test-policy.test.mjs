import assert from 'node:assert/strict';
import { test } from 'node:test';
import { hasRequiredTestEvidence, recordTestEvidence } from '../src/test-policy.js';

test('publication requires both prepared scenario tests to pass most recently', () => {
  const evidence = new Map();
  recordTestEvidence(evidence, 'ws_one', 'python-unit', 0);
  assert.equal(hasRequiredTestEvidence(evidence, 'ws_one'), false);
  recordTestEvidence(evidence, 'ws_one', 'python-scoring-test', 0);
  assert.equal(hasRequiredTestEvidence(evidence, 'ws_one'), true);
  recordTestEvidence(evidence, 'ws_one', 'python-unit', 1);
  assert.equal(hasRequiredTestEvidence(evidence, 'ws_one'), false);
});
