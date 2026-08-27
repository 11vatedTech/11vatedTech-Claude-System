import { chromium } from 'playwright-core';
import { mkdir, writeFile } from 'node:fs/promises';
import { join } from 'node:path';

const url = process.argv[2] || 'http://127.0.0.1:5175/';
const out = process.argv[3] || 'artifacts/frontend/wave-a-pumkit-before';
await mkdir(out, { recursive: true });
const browser = await chromium.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true });
const viewports = [
  ['desktop-wide', 1440, 900], ['desktop-laptop', 1280, 800], ['desktop-narrow', 1024, 768],
  ['mobile', 375, 812], ['mobile-narrow', 320, 700], ['tablet', 768, 1024]
];
const states = ['default', 'liquid', 'behavior-alert', 'field-mode'];
const evidence = { schema_version: 1, kind: 'wave-a-pumkit-before-evidence', url, read_only: true, captures: [], console_errors: [], network_failures: [] };
for (const [name, width, height] of viewports) for (const state of states) {
  const context = await browser.newContext({ viewport: { width, height } });
  const page = await context.newPage();
  page.on('console', msg => { if (msg.type() === 'error') evidence.console_errors.push({ viewport: name, state, text: msg.text() }); });
  page.on('response', r => { if (r.status() >= 400) evidence.network_failures.push({ viewport: name, state, url: r.url(), status: r.status() }); });
  await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
  if (state === 'liquid') await page.locator('.liquid-trigger').evaluate(el => el.click());
  if (state === 'behavior-alert') await page.locator('[data-state="alert"]').evaluate(el => el.click());
  if (state === 'field-mode') await page.locator('.field-toggle').evaluate(el => el.click());
  await page.waitForTimeout(500);
  const screenshot = `${name}__${state}.png`;
  await page.screenshot({ path: join(out, screenshot), fullPage: true });
  const observation = await page.evaluate(() => {
    const rect = selector => { const el = document.querySelector(selector); if (!el) return null; const r = el.getBoundingClientRect(); const s = getComputedStyle(el); return { selector, x:r.x, y:r.y, width:r.width, height:r.height, display:s.display, position:s.position, zIndex:s.zIndex, overflow:s.overflow, color:s.color, backgroundColor:s.backgroundColor, fontSize:s.fontSize, lineHeight:s.lineHeight }; };
    const focusables = [...document.querySelectorAll('a,button,[tabindex]')].map((el, i) => ({ i, tag: el.tagName, text: (el.innerText || el.getAttribute('aria-label') || '').trim().slice(0,120), ariaPressed: el.getAttribute('aria-pressed'), href: el.getAttribute('href'), tabIndex: el.tabIndex }));
    const overflow = [...document.querySelectorAll('body,main,section,.topbar,nav')].map(el => ({ selector: `${el.tagName}.${el.className}`, scrollWidth: el.scrollWidth, clientWidth: el.clientWidth, overflowX: getComputedStyle(el).overflowX, clipped: el.scrollWidth > el.clientWidth + 1 }));
    return { title: document.title, viewport: { width: innerWidth, height: innerHeight }, landmarkCounts: { main: document.querySelectorAll('main').length, nav: document.querySelectorAll('nav').length, header: document.querySelectorAll('header').length }, hero: rect('.hero-character'), heroImage: rect('.hero-character img'), topbar: rect('.topbar'), nav: rect('nav'), fieldToggle: rect('.field-toggle'), focusables, overflow, liquidState: document.querySelector('.scene-liquid')?.dataset.liquidState || null, behaviorState: document.querySelector('[data-behavior-stage]')?.dataset.state || null, fieldMode: document.body.classList.contains('field-mode') };
  });
  evidence.captures.push({ viewport: name, width, height, state, screenshot, observation });
  await context.close();
}
await browser.close();
evidence.summary = { captures: evidence.captures.length, screenshots: evidence.captures.length, console_errors: evidence.console_errors.length, network_failures: evidence.network_failures.length, clipped_entries: evidence.captures.reduce((n, c) => n + c.observation.overflow.filter(x => x.clipped).length, 0) };
await writeFile(join(out, 'pumkit-before-evidence.json'), JSON.stringify(evidence, null, 2));
console.log(JSON.stringify(evidence.summary, null, 2));
