const DEMO_USER_ID = "demo-brain";

function canReadArchive(userId, judgeUserId) {
  const candidate = String(userId || "").trim();
  return candidate === DEMO_USER_ID || Boolean(judgeUserId && candidate === judgeUserId);
}

function canMutateThroughHarness(method, cloudMode) {
  return !cloudMode || !["POST", "PUT", "PATCH", "DELETE"].includes(String(method).toUpperCase());
}

module.exports = { canReadArchive, canMutateThroughHarness };
