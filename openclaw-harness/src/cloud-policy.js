const DEMO_USER_ID = "demo-brain";

function canReadArchive(userId, judgeUserId, sessionUserId) {
  const candidate = String(userId || "").trim();
  return candidate === DEMO_USER_ID
    || Boolean(judgeUserId && candidate === judgeUserId)
    || Boolean(sessionUserId && candidate === sessionUserId);
}

function canMutateThroughHarness(method, cloudMode) {
  return !cloudMode || !["POST", "PUT", "PATCH", "DELETE"].includes(String(method).toUpperCase());
}

module.exports = { canReadArchive, canMutateThroughHarness };
