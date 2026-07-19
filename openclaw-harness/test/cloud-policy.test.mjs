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

test('cloud policy exposes a signed session archive only to its owning judge', () => {
  assert.equal(policy.canReadArchive('judge-a1b2', '', 'judge-a1b2'), true);
  assert.equal(policy.canReadArchive('judge-other', '', 'judge-a1b2'), false);
});

test('signed judge archive defaults to the prepared repository scope plus core memory', () => {
  assert.equal(
    policy.archiveQueryString({}, { privateJudge: true, repository: 'crankysmh47/WebPort' }),
    'scope_type=repository&scope_id=crankysmh47%2FWebPort&include_core=true',
  );
  assert.equal(policy.archiveQueryString({ q: 'green' }, { privateJudge: false }), 'q=green');
});
