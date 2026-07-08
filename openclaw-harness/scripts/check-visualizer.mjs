import { chromium } from "playwright";

const url = process.argv[2] || "http://127.0.0.1:3000/?user=demo-brain";

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
const consoleLogs = [];
const consoleErrors = [];
page.on("console", (msg) => {
  const line = `[${msg.type()}] ${msg.text()}`;
  consoleLogs.push(line);
  if (msg.type() === "error") consoleErrors.push(line);
});
page.on("pageerror", (err) => consoleErrors.push(`[pageerror] ${err.message}`));

await page.goto(url, { waitUntil: "networkidle", timeout: 30000 });
await page.waitForTimeout(4000);

const report = await page.evaluate(() => {
  const svg = document.querySelector("#graphSvg");
  const nodes = document.querySelectorAll("g.node");
  const detail = document.getElementById("nodeDetail")?.textContent || "";
  const live = document.getElementById("liveLabel")?.textContent || "";
  const beliefs = document.getElementById("mBeliefs")?.textContent || "";
  return {
    title: document.title,
    hasStamp: document.body.innerHTML.includes("v2026-07-08"),
    d3Loaded: typeof window.d3 !== "undefined",
    svgWidth: svg?.getAttribute("width"),
    svgHeight: svg?.getAttribute("height"),
    nodeCount: nodes.length,
    nodeDetail: detail,
    liveLabel: live,
    mBeliefs: beliefs,
    bodyBg: getComputedStyle(document.body).backgroundColor,
  };
});

console.log(JSON.stringify({ url, report, consoleErrors, consoleLogs: consoleLogs.slice(-8) }, null, 2));
await browser.close();
process.exit(report.nodeCount > 0 ? 0 : 1);
