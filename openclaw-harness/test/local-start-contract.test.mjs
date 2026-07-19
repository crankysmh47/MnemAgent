import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

const script = fs.readFileSync(new URL('../../scripts/start-demo.ps1', import.meta.url), 'utf8');
const cloudVerify = fs.readFileSync(new URL('../../scripts/verify-cloud.sh', import.meta.url), 'utf8');

test('local demo start hydrates the broker token from the GitHub CLI keyring', () => {
  assert.match(script, /gh auth token/);
  assert.match(script, /\$env:JUDGE_GITHUB_TOKEN\s*=/);
  assert.match(script, /GitHub CLI authentication is required/);
  assert.doesNotMatch(script, /JUDGE_GITHUB_TOKEN.*(?:Set-Content|Out-File|Add-Content)/);
});

test('cloud verification enforces the published 30 / 5 / 5 judge allowance', () => {
  assert.match(cloudVerify, /chatTurnsRemaining[^\n]+== 30/);
  assert.match(cloudVerify, /codingRunsRemaining[^\n]+== 5/);
  assert.match(cloudVerify, /publicationsRemaining[^\n]+== 5/);
  assert.match(cloudVerify, /python3 -/);
  assert.doesNotMatch(cloudVerify, /node -e/);
});
