import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

const dockerfile = fs.readFileSync(new URL('../Dockerfile', import.meta.url), 'utf8');
const compose = fs.readFileSync(new URL('../../docker-compose.yml', import.meta.url), 'utf8');
const server = fs.readFileSync(new URL('../src/index.js', import.meta.url), 'utf8');

test('broker image includes the shared patch policy required at startup', () => {
  assert.match(compose, /workspace-broker:[\s\S]*?build:[\s\S]*?context:\s*\./);
  assert.match(dockerfile, /COPY workspace-runner\/patch-policy\.js \/workspace-runner\/patch-policy\.js/);
  assert.match(server, /listen\(config\.port,\s*['"]0\.0\.0\.0['"]/);
  assert.match(compose, /127\.0\.0\.1:8010:8010/);
});
