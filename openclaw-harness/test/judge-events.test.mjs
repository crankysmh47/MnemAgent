import test from 'node:test';
import assert from 'node:assert/strict';
import { createJudgeEventLog } from '../src/judge-events.js';

test('judge events are monotonic and resumable', () => {
  const log = createJudgeEventLog();
  const first = log.append('run-1', { type: 'plan.created', label: 'Plan formed' });
  const second = log.append('run-1', { type: 'tool.completed', label: 'Memory searched' });
  assert.equal(first.sequence, 1);
  assert.equal(second.sequence, 2);
  assert.deepEqual(log.after('run-1', first.id), [second]);
});
