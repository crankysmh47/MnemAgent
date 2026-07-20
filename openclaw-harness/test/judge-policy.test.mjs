import test from 'node:test';
import assert from 'node:assert/strict';
import policy from '../src/judge-policy.js';
const { validateJudgeRun, canOpenDraftPr } = policy;

test('judge runs allow only prepared issues and bounded messages', () => {
  assert.deepEqual(validateJudgeRun({ issueNumber: 1, message: 'Fix the contradiction dimension.' }), { issueNumber: 1, message: 'Fix the contradiction dimension.' });
  assert.throws(() => validateJudgeRun({ issueNumber: 99, message: 'x' }), /prepared issue/);
  assert.throws(() => validateJudgeRun({ issueNumber: 1, message: 'x'.repeat(2001) }), /2,000/);
});

test('draft PR opens only after a passing approved diff', () => {
  assert.equal(canOpenDraftPr({ testsPassed: true, approval: { valid: true }, diffHash: 'abc' }), true);
  assert.equal(canOpenDraftPr({ testsPassed: false, approval: { valid: true }, diffHash: 'abc' }), false);
});
