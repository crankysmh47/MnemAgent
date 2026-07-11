import test from 'node:test';
import assert from 'node:assert/strict';
import policy from '../src/cloud-policy.js';

test('cloud policy exposes only read-only demo and configured judge archives', () => {
  assert.equal(policy.canReadArchive('demo-brain', 'judge-1'), true);
  assert.equal(policy.canReadArchive('judge-1', 'judge-1'), true);
  assert.equal(policy.canReadArchive('someone-else', 'judge-1'), false);
  assert.equal(policy.canMutateThroughHarness('POST', true), false);
  assert.equal(policy.canMutateThroughHarness('POST', false), true);
});
