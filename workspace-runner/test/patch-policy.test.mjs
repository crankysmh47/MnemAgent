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
  const pythonPatch = '--- a/mnembench/scoring.py\n+++ b/mnembench/scoring.py\n@@\n-old\n+new\n--- /dev/null\n+++ b/tests/test_scoring.py\n@@\n+test\n';
  assert.deepEqual(validatePatch(pythonPatch).files, ['mnembench/scoring.py', 'tests/test_scoring.py']);
});
