const { randomUUID } = require('node:crypto');

function createJudgeEventLog() {
  const runs = new Map();
  return {
    append(runId, event) {
      const entries = runs.get(runId) || [];
      const entry = { id: `evt_${randomUUID()}`, runId, sequence: entries.length + 1, timestamp: new Date().toISOString(), ...event };
      entries.push(entry);
      runs.set(runId, entries);
      return entry;
    },
    after(runId, eventId = null) {
      const entries = runs.get(runId) || [];
      if (!eventId) return [...entries];
      const index = entries.findIndex(entry => entry.id === eventId);
      return index < 0 ? [...entries] : entries.slice(index + 1);
    },
  };
}

module.exports = { createJudgeEventLog };
