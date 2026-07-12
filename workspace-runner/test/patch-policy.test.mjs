import test from 'node:test';
import assert from 'node:assert/strict';
import { validatePatch } from '../patch-policy.js';

const valid = '--- a/src/config.js\n+++ b/src/config.js\n@@\n-old\n+new\n';

test('accepts bounded source patches and rejects protected paths', () => {
  assert.deepEqual(validatePatch(valid), { files: ['src/config.js'], changedLines: 2 });
  assert.throws(() => validatePatch(valid.replace('+++ b/src/config.js', '+++ b/.env')), /not allowed/);
  assert.throws(() => validatePatch(valid.replace('+++ b/src/config.js', '+++ b/../escape.js')), /not allowed/);
  const cppPatch = '--- a/src/core/fs_path.cpp\n+++ b/src/core/fs_path.cpp\n@@\n-old\n+new\n';
  assert.deepEqual(validatePatch(cppPatch).files, ['src/core/fs_path.cpp']);
});
