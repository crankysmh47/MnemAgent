const { randomUUID } = require('node:crypto');
const { openClawExecutor } = require('./judge-run-service');

function publicTurn(turn) {
  const { ownerSessionId: _owner, task: _task, ...value } = turn;
  return { ...value };
}

function createJudgeChatService({ model = process.env.JUDGE_MODEL || 'deepseek-api/deepseek-v4-flash', executor = openClawExecutor } = {}) {
  const turns = new Map();
  const owned = (id, ownerSessionId) => {
    const turn = turns.get(id);
    if (!turn || turn.ownerSessionId !== ownerSessionId) throw new Error('Judge chat turn not found.');
    return turn;
  };
  return {
    create({ ownerSessionId, namespace, message }) {
      if (!/^jss_[A-Za-z0-9_-]{3,100}$/.test(String(ownerSessionId || '')) || !/^judge-[A-Za-z0-9_-]{3,100}$/.test(String(namespace || ''))) throw new Error('A private judge session is required.');
      if (!String(message || '').trim() || String(message).length > 2_000) throw new Error('A bounded chat message is required.');
      const id = `chat_${randomUUID()}`;
      const sessionId = `judge-chat-${randomUUID()}`;
      const turn = { id, ownerSessionId, namespace, sessionId, model, status: 'running', message: String(message), createdAt: new Date().toISOString(), response: '' };
      turns.set(id, turn);
      const contractMessage = `This is a conversational memory turn for private user ${namespace}. Reply naturally and search existing memories before answering. Call memory_store only when the user's current message introduces or corrects a durable preference, decision, correction, or repository rule. A question that merely asks you to recall must never write another memory. If the message is about WebPort or a WebPort convention, use scope_type repository and scope_id crankysmh47/WebPort. Use core/core only for preferences that apply across repositories. Do not use repository workspace tools. User message: ${message}`;
      turn.task = (async () => {
        try {
          const result = await executor({ sessionId, message: contractMessage, model, namespace, runId: id, agentId: 'judge-chat', contractPath: process.env.JUDGE_CHAT_PROMPT_PATH || require('node:path').join(__dirname, '../../config/openclaw/judge-chat.md') });
          turn.response = String(result.text || '').slice(0, 12_000);
          turn.usageUsd = Math.max(0, Number(result.usageUsd || 0));
          turn.usageTokens = result.usageTokens || { input: 0, output: 0, total: 0 };
          turn.status = 'completed';
        } catch {
          turn.status = 'failed';
          turn.response = 'The live chat turn stopped. Your existing memories are unchanged.';
        }
        return publicTurn(turn);
      })();
      return publicTurn(turn);
    },
    get(id, ownerSessionId) { return publicTurn(owned(id, ownerSessionId)); },
    wait(id) { const turn = turns.get(id); if (!turn) throw new Error('Judge chat turn not found.'); return turn.task; },
  };
}

module.exports = { createJudgeChatService };
