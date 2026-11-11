// Synthetic mechanism probe. Dependencies and destination must be explicit and trusted.
const { createHash } = require('node:crypto');
const { execFileSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

function argumentsFrom(argv) {
  const required = ['playwright', 'chromium', 'ffmpeg', 'ffprobe', 'out'];
  const values = {};
  if (argv.length !== required.length * 2) throw new Error('provide all five --name absolute-path pairs');
  for (let i = 0; i < argv.length; i += 2) {
    const key = argv[i].replace(/^--/, '');
    if (argv[i] !== `--${key}` || !required.includes(key) || values[key] || !path.isAbsolute(argv[i + 1])) {
      throw new Error('invalid, duplicate, or non-absolute argument');
    }
    values[key] = argv[i + 1];
  }
  if (required.some(key => !values[key])) throw new Error('missing argument');
  return values;
}

const html = `<!doctype html><html><head>
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<style>html,body{margin:0;width:320px;height:240px;background:#193d32;overflow:hidden}
#box{position:absolute;left:20px;top:35px;width:60px;height:60px;background:#df8a4c}
#title{position:absolute;left:24px;top:150px;color:white;font:700 24px sans-serif}</style>
</head><body><div id="box"></div><div id="title">PAUSA FICTÍCIA</div></body></html>`;
const hash = data => createHash('sha256').update(data).digest('hex');

async function bounded(promise) {
  let timer;
  try {
    return await Promise.race([promise, new Promise((_, reject) => {
      timer = setTimeout(() => reject(new Error('browser operation timed out')), 10000);
    })]);
  } finally {
    clearTimeout(timer);
  }
}

async function run(args) {
  const { chromium } = require(args.playwright);
  fs.mkdirSync(args.out, { mode: 0o700 }); // Destination must not already exist.
  const work = fs.mkdtempSync(path.join(os.tmpdir(), 'motion-waapi-synthetic-'));
  let browser;
  try {
    // No API keys, user HOME, or proxy configuration enter the browser or ffmpeg.
    const cleanEnv = { PATH: '/usr/bin:/bin', HOME: work, TMPDIR: work, LANG: 'C.UTF-8' };
    browser = await chromium.launch({
      executablePath: args.chromium, headless: true, chromiumSandbox: true, env: cleanEnv, timeout: 15000,
    });
    const browserVersion = browser.version();
    const context = await browser.newContext({ viewport: { width: 320, height: 240 }, serviceWorkers: 'block' });
    let networkRequests = 0;
    await context.route('**/*', route => { networkRequests++; return route.abort(); });
    const page = await context.newPage();
    page.setDefaultTimeout(10000);
    await page.setContent(html, { waitUntil: 'load', timeout: 10000 });
    await bounded(page.evaluate(() => {
      const position = document.getElementById('box').animate(
        [{ transform: 'translateX(0px)' }, { transform: 'translateX(180px)' }],
        { duration: 1000, fill: 'both', easing: 'linear' });
      const opacity = document.getElementById('title').animate([{ opacity: 0 }, { opacity: 1 }],
        { duration: 1000, fill: 'both', easing: 'linear' });
      position.pause(); opacity.pause();
      window.syntheticAnimations = [position, opacity];
    }));
    const seek = async ms => bounded(page.evaluate(ms => {
      for (const animation of window.syntheticAnimations) animation.currentTime = ms;
      return { x: document.getElementById('box').getBoundingClientRect().x,
        opacity: Number(getComputedStyle(document.getElementById('title')).opacity) };
    }, ms));
    const states = [];
    const deadline = Date.now() + 120000;
    for (let index = 0; index <= 30; index++) {
      if (Date.now() > deadline) throw new Error('frame deadline exceeded');
      const ms = index * 1000 / 30;
      const state = await seek(ms);
      const frame = await page.screenshot({ type: 'png', animations: 'allow', caret: 'hide', timeout: 10000 });
      fs.writeFileSync(path.join(work, `frame-${String(index).padStart(3, '0')}.png`), frame, { mode: 0o600 });
      if ([0, 15, 30].includes(index)) {
        fs.writeFileSync(path.join(args.out, `frame-${String(index).padStart(3, '0')}.png`), frame, { mode: 0o600 });
        states.push({ ms, ...state, sha256: hash(frame) });
      }
    }
    const rewindState = await seek(0);
    const rewind = await page.screenshot({ type: 'png', animations: 'allow', caret: 'hide', timeout: 10000 });
    fs.writeFileSync(path.join(args.out, 'rewind.png'), rewind, { mode: 0o600 });
    if (states[0].sha256 !== hash(rewind)) throw new Error('rewind frame differs');
    if (JSON.stringify(states.map(s => Math.round(s.x))) !== JSON.stringify([20, 110, 200])) throw new Error('position mismatch');
    if (states[0].opacity !== 0 || states[1].opacity !== 0.5 || states[2].opacity !== 1) throw new Error('opacity mismatch');
    if (networkRequests !== 0) throw new Error('unexpected network request blocked');
    await browser.close(); browser = undefined;
    const video = path.join(args.out, 'synthetic.mp4');
    execFileSync(args.ffmpeg, ['-nostdin', '-v', 'error', '-protocol_whitelist', 'file,pipe', '-framerate', '30',
      '-i', path.join(work, 'frame-%03d.png'), '-frames:v', '31', '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
      '-movflags', '+faststart', video], { env: cleanEnv, timeout: 30000, stdio: 'pipe' });
    const info = JSON.parse(execFileSync(args.ffprobe, ['-v', 'error', '-protocol_whitelist', 'file,pipe', '-show_entries',
      'format=duration,size:stream=codec_name,codec_type,width,height,avg_frame_rate', '-of', 'json', video],
      { env: cleanEnv, timeout: 10000, stdio: 'pipe' }).toString());
    const report = { purpose: 'synthetic WAAPI mechanism probe; no model, paid call or customer media',
      browserVersion, browserSandbox: true, csp: "default-src 'none'", networkRequests, fps: 30, frames: 31,
      states, rewind: { ...rewindState, sha256: hash(rewind), equals_first: true },
      mp4: { sha256: hash(fs.readFileSync(video)), ...info } };
    fs.writeFileSync(path.join(args.out, 'report.json'), JSON.stringify(report, null, 2) + '\n', { mode: 0o600 });
    console.log(JSON.stringify(report));
  } finally {
    if (browser) await browser.close();
    fs.rmSync(work, { recursive: true, force: true });
  }
}

try {
  run(argumentsFrom(process.argv.slice(2))).catch(() => { console.error('Synthetic probe failed'); process.exitCode = 1; });
} catch {
  console.error('Usage: node motion_waapi_probe.cjs --playwright /absolute/module --chromium /absolute/browser --ffmpeg /absolute/ffmpeg --ffprobe /absolute/ffprobe --out /absolute/new-directory');
  process.exitCode = 1;
}
