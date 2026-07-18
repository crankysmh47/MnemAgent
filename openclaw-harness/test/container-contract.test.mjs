import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

const dockerfile = fs.readFileSync(new URL('../Dockerfile', import.meta.url), 'utf8');

test('harness image satisfies the pinned OpenClaw Node runtime requirement', () => {
  assert.match(dockerfile, /^FROM node:22(?:\.|-)/m);
  assert.match(dockerfile, /openclaw@2026\.6\.5/);
});
