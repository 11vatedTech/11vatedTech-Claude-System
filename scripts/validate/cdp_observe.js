#!/usr/bin/env node
/**
 * cdp_observe.js — headless browser observation for runtime / visual QA.
 *
 * Launches Chrome headless, navigates to a URL, waits real wall-clock time
 * (so requestAnimationFrame, WebGL, network and animations genuinely run),
 * captures screenshots at intervals, and reports console errors + page state.
 *
 * Usage:
 *   node cdp_observe.js <url> <outdir> [seconds] [interval_seconds]
 *
 * Outputs:
 *   <outdir>/frame-<n>.png   screenshots
 *   <outdir>/console.json    console messages (errors/warnings)
 *   <outdir>/state.json      loading state + hero presence + perf timing
 */
const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");

const CHROME =
  process.env.CHROME_BIN ||
  "C:/Program Files/Google/Chrome/Application/chrome.exe";

const [url, outdir, seconds = "8", interval = "2"] = process.argv.slice(2);
if (!url || !outdir) {
  console.error("usage: node cdp_observe.js <url> <outdir> [seconds] [interval]");
  process.exit(1);
}

const totalMs = parseFloat(seconds) * 1000;
const stepMs = parseFloat(interval) * 1000;
const port = 9300 + Math.floor(Math.random() * 500);

fs.mkdirSync(outdir, { recursive: true });

const chrome = spawn(
  CHROME,
  [
    "--headless=new",
    "--no-sandbox",
    "--enable-unsafe-swiftshader",
    "--use-angle=swiftshader",
    "--window-size=1280,800",
    "--hide-scrollbars",
    `--remote-debugging-port=${port}`,
    "about:blank",
  ],
  { stdio: "ignore" }
);

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function getJson(url) {
  const res = await fetch(url);
  return res.json();
}

async function main() {
  // wait for the debugging endpoint
  let targets = null;
  for (let i = 0; i < 40; i++) {
    try {
      targets = await getJson(`http://127.0.0.1:${port}/json/list`);
      if (targets && targets.length) break;
    } catch (_) {}
    await sleep(250);
  }
  if (!targets || !targets.length) throw new Error("chrome did not start");

  const page = targets.find((t) => t.type === "page");
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });

  let msgId = 0;
  const pending = new Map();
  const consoleMsgs = [];

  ws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.id && pending.has(msg.id)) {
      pending.get(msg.id)(msg);
      pending.delete(msg.id);
    } else if (msg.method === "Runtime.consoleAPICalled") {
      const text = (msg.params.args || [])
        .map((a) => a.value ?? a.description ?? "")
        .join(" ");
      consoleMsgs.push({ type: msg.params.type, text });
    } else if (msg.method === "Runtime.exceptionThrown") {
      consoleMsgs.push({
        type: "exception",
        text: (msg.params.exceptionDetails?.exception?.description ||
          msg.params.exceptionDetails?.text || "exception"),
      });
    } else if (msg.method === "Log.entryAdded") {
      const e = msg.params.entry;
      if (e.level === "error" || e.level === "warning") {
        consoleMsgs.push({ type: `log:${e.level}`, text: e.text });
      }
    } else if (msg.method === "Network.loadingFailed") {
      failedRequests.push({
        requestId: msg.params.requestId,
        error: msg.params.errorText,
      });
    }
  };

  const failedRequests = [];

  const send = (method, params = {}) =>
    new Promise((res) => {
      const id = ++msgId;
      pending.set(id, res);
      ws.send(JSON.stringify({ id, method, params }));
    });

  await send("Runtime.enable");
  await send("Page.enable");
  await send("Log.enable");
  await send("Network.enable");
  await send("Emulation.setDeviceMetricsOverride", {
    width: 1280, height: 800, deviceScaleFactor: 1, mobile: false,
  });

  await send("Page.navigate", { url });
  await sleep(1500); // let the document + module start

  const frames = [];
  const shots = [];
  let elapsed = 1500;
  while (elapsed < totalMs) {
    const shot = await send("Page.captureScreenshot", { format: "png" });
    const name = `frame-${String(shots.length + 1).padStart(2, "0")}.png`;
    fs.writeFileSync(path.join(outdir, name), Buffer.from(shot.result.data, "base64"));
    shots.push(name);
    frames.push({ t_ms: elapsed, file: name });

    // page state probe
    const probe = await send("Runtime.evaluate", {
      expression: `JSON.stringify({
        loading: document.getElementById('loading') && document.getElementById('loading').textContent,
        loadingHidden: document.getElementById('loading') ? document.getElementById('loading').classList.contains('hidden') : null,
        status: document.getElementById('status') ? document.getElementById('status').textContent : null,
        canvas: !!document.querySelector('canvas'),
        canvasWH: document.querySelector('canvas') ? document.querySelector('canvas').width + 'x' + document.querySelector('canvas').height : null,
        title: document.title,
        foundryState: window.__emberveil && window.__emberveil.getState ? window.__emberveil.getState() : null
      })`,
      returnByValue: true,
    });
    frames[frames.length - 1].state = JSON.parse(probe.result?.result?.value || "{}");

    await sleep(stepMs);
    elapsed += stepMs;
  }

  const perf = await send("Runtime.evaluate", {
    expression: `JSON.stringify({
      timing: performance.timing ? { nav: performance.timing.navigationStart, load: performance.timing.loadEventEnd } : null,
      resources: performance.getEntriesByType('resource').map(r => ({ name: r.name.split('/').pop(), dur: Math.round(r.duration) }))
    })`,
    returnByValue: true,
  });

  fs.writeFileSync(
    path.join(outdir, "console.json"),
    JSON.stringify({ messages: consoleMsgs, failedRequests }, null, 2)
  );
  fs.writeFileSync(
    path.join(outdir, "state.json"),
    JSON.stringify({ url, frames, perf: JSON.parse(perf.result?.result?.value || "{}") }, null, 2)
  );

  console.log(JSON.stringify({
    frames: shots,
    consoleErrors: consoleMsgs.filter((m) => m.type === "error" || m.type === "exception").length,
    consoleWarnings: consoleMsgs.filter((m) => m.type === "warning").length,
    failedRequests: failedRequests.length,
    lastState: frames[frames.length - 1].state,
  }, null, 2));

  ws.close();
  chrome.kill();
  process.exit(0);
}

main().catch((e) => {
  console.error("CDP observe failed:", e.message);
  chrome.kill();
  process.exit(1);
});
