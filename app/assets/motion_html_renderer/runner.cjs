'use strict';

// Trusted container entry point. Model JavaScript executes only inside Chromium.
// stdout is a bounded binary result protocol; stderr contains stable error codes.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { spawnSync } = require('node:child_process');
const { buildAudioArgs, parseAudioMetrics } = require('./audio.cjs');
// Preserve absolute asset URLs used by qualified compositions; still one fixed, routed origin.
const ORIGIN = 'https://motion-fixture.invalid';
const MAX_INPUT = 256 * 1024 * 1024;
const MAX_VIDEO = 128 * 1024 * 1024;
const MAX_EVIDENCE = 32 * 1024 * 1024;
const hash = data => crypto.createHash('sha256').update(data).digest('hex');

class RenderFault extends Error {
  constructor(code) { super(code); this.code = code; }
}
const fail = code => { throw new RenderFault(code); };
function read(file, maximum, digest) {
  const stat = fs.lstatSync(file);
  if (!stat.isFile() || stat.size > maximum) fail('MOTION_RENDER_INPUT_LIMIT');
  const data = fs.readFileSync(file);
  if (digest !== undefined && hash(data) !== digest) fail('MOTION_RENDER_INPUT_CHANGED');
  return data;
}
function command(binary, args, timeout = 30000) {
  const result = spawnSync(binary, args, {
    env: { PATH: '/usr/bin:/bin', HOME: '/tmp/home', TMPDIR: '/tmp', LANG: 'C.UTF-8' },
    timeout, killSignal: 'SIGKILL', maxBuffer: 2 * 1024 * 1024, stdio: ['ignore', 'pipe', 'pipe'],
  });
  if (result.error || result.status !== 0) fail('MOTION_RENDER_MEDIA_FAILED');
  return result.stdout;
}
function audioMetrics(file) {
  const result = spawnSync('/usr/bin/ffmpeg', ['-hide_banner', '-nostdin', '-v', 'info',
    '-protocol_whitelist', 'file,pipe', '-i', file, '-map', '0:a:0',
    '-af', 'ebur128=peak=sample', '-f', 'null', '-'], {
    env: { PATH: '/usr/bin:/bin', HOME: '/tmp/home', TMPDIR: '/tmp', LANG: 'C.UTF-8' },
    timeout: 30000, killSignal: 'SIGKILL', maxBuffer: 2 * 1024 * 1024, stdio: ['ignore', 'pipe', 'pipe'],
  });
  if (result.error || result.status !== 0) fail('MOTION_RENDER_AUDIO_INVALID');
  try { return parseAudioMetrics(result.stderr.toString('utf8')); }
  catch (_) { fail('MOTION_RENDER_AUDIO_INVALID'); }
}
async function deadline(promise, ms = 10000) {
  let timer;
  try {
    return await Promise.race([promise, new Promise((_, reject) => {
      timer = setTimeout(() => reject(new RenderFault('MOTION_RENDER_BROWSER_TIMEOUT')), ms);
    })]);
  } finally { clearTimeout(timer); }
}
function status(file) {
  return Object.fromEntries(fs.readFileSync(file, 'utf8').split('\n').filter(line => line.includes(':'))
    .map(line => { const colon = line.indexOf(':'); return [line.slice(0, colon), line.slice(colon + 1).trim()]; }));
}
function isolation() {
  const own = status('/proc/self/status');
  if (process.getuid() !== 65532 || own.CapEff !== '0000000000000000' || own.NoNewPrivs !== '1' || own.Seccomp !== '2' ||
      !Number.isSafeInteger(Number(own.Seccomp_filters)) || Number(own.Seccomp_filters) < 1) {
    fail('MOTION_RENDER_OS_ISOLATION_FAILED');
  }
  return Number(own.Seccomp_filters);
}
function browserSandbox(ownFilters) {
  for (const pid of fs.readdirSync('/proc').filter(value => /^\d+$/.test(value))) {
    let args, child;
    try {
      // Chromium rewrites argv as a single process-title string on Linux.
      args = fs.readFileSync(`/proc/${pid}/cmdline`, 'utf8').split(/[\0\s]+/);
      if (!args.includes('--type=renderer')) continue;
      child = status(`/proc/${pid}/status`);
    } catch (error) {
      if (error.code === 'ENOENT' || error.code === 'ESRCH') continue;
      throw error;
    }
    if (args.includes('--no-sandbox') || child.Seccomp !== '2' || child.NoNewPrivs !== '1' ||
        !Number.isSafeInteger(Number(child.Seccomp_filters)) ||
        Number(child.Seccomp_filters) <= ownFilters) fail('MOTION_RENDER_BROWSER_SANDBOX_FAILED');
    return Number(child.Seccomp_filters);
  }
  fail('MOTION_RENDER_BROWSER_SANDBOX_UNPROVEN');
}
function range(header, size) {
  const match = /^bytes=(\d+)-(\d*)$/.exec(header);
  if (!match) return null;
  const first = Number(match[1]), last = match[2] ? Math.min(Number(match[2]), size - 1) : size - 1;
  return Number.isSafeInteger(first) && Number.isSafeInteger(last) && first <= last && first < size ? { first, last } : null;
}
async function controls(context) {
  await context.addInitScript(() => {
    for (const key of ['RTCPeerConnection', 'webkitRTCPeerConnection', 'RTCIceCandidate', 'RTCSessionDescription', 'WebTransport']) {
      Object.defineProperty(window, key, { value: undefined, writable: false, configurable: false });
    }
    Object.defineProperty(window, 'open', { value: () => null, writable: false, configurable: false });
  });
  await context.routeWebSocket('**/*', socket => socket.close({ code: 1008, reason: 'blocked' }));
}
async function render() {
  const ownFilters = isolation();
  const configBytes = read('/input/config.json', 1024 * 1024), cfg = JSON.parse(configBytes);
  if (cfg.fingerprint_frames !== undefined && (cfg.fingerprint_frames !== true || cfg.version !== 1)) {
    fail('MOTION_RENDER_PROFILE_INVALID');
  }
  if (![1, 2].includes(cfg.version) || cfg.fps !== 30 || !Number.isSafeInteger(cfg.duration_ms) || cfg.duration_ms < 1 || cfg.duration_ms > 60000 ||
      !Number.isSafeInteger(cfg.width) || !Number.isSafeInteger(cfg.height) || cfg.width < 64 || cfg.height < 64 ||
      cfg.width > 1920 || cfg.height > 1920 || cfg.width % 2 || cfg.height % 2 || !Array.isArray(cfg.assets) || cfg.assets.length > 32 ||
      !Array.isArray(cfg.sample_frames) || cfg.sample_frames.length < 1 || cfg.sample_frames.length > 64 ||
      cfg.sample_frames.some(index => !Number.isSafeInteger(index) || index < 0 || index >= Math.ceil(cfg.duration_ms * 30 / 1000))) fail('MOTION_RENDER_PROFILE_INVALID');
  const html = read('/input/index.html', 2 * 1024 * 1024, cfg.html_sha256);
  const scene = read('/input/scene.js', 1024 * 1024, cfg.scene_sha256);
  const assets = new Map(), audioPaths = new Map();
  let inputBytes = html.length + scene.length;
  for (const [index, asset] of cfg.assets.entries()) {
    if (!/^assets\/[A-Za-z0-9_.-]{1,80}$/.test(asset.id) || assets.has(asset.id) || asset.file !== `asset-${index}` ||
        !['video/mp4', 'image/png', 'image/jpeg', 'font/ttf', 'font/woff2', 'audio/wav', 'audio/ogg', 'audio/mpeg'].includes(asset.mime_type)) {
      fail('MOTION_RENDER_ASSET_INVALID');
    }
    const file = `/input/${asset.file}`, body = read(file, MAX_INPUT, asset.sha256);
    inputBytes += body.length;
    if (inputBytes > MAX_INPUT) fail('MOTION_RENDER_INPUT_LIMIT');
    assets.set(asset.id, { body, contentType: asset.mime_type });
    if (asset.mime_type.startsWith('audio/') || asset.mime_type === 'video/mp4') audioPaths.set(asset.id, file);
  }
  const audio = buildAudioArgs(cfg.audio, audioPaths, cfg.duration_ms);
  const audioSourceSpans = [];
  for (const track of cfg.version === 2 ? [] : cfg.audio.tracks) {
    const metadata = JSON.parse(command('/usr/bin/ffprobe', ['-v', 'error', '-protocol_whitelist', 'file,pipe',
      '-show_entries', 'format=duration:stream=codec_type', '-of', 'json', audioPaths.get(track.asset_id)]));
    const availableMs = Number(metadata.format.duration) * 1000;
    if (!metadata.streams.some(stream => stream.codec_type === 'audio') || !Number.isFinite(availableMs) ||
        availableMs <= 0 || track.trim_start_ms >= availableMs) fail('MOTION_RENDER_AUDIO_INVALID');
    // New optional audio must cover the declared event; never silently stretch or truncate it.
    if (cfg.audio.version === 'motion-audio-v2' && track.role !== 'original' &&
        track.trim_end_ms > availableMs + 1) fail('MOTION_RENDER_AUDIO_INVALID');
    // Preserve the qualified mixer: atrim stops at EOF; no padding or synthetic speech is added.
    audioSourceSpans.push({ asset_id: track.asset_id, available_ms: availableMs,
      trim_start_ms: track.trim_start_ms, trim_end_ms: track.trim_end_ms,
      ends_before_planned_trim: track.trim_end_ms > availableMs });
  }
  fs.mkdirSync('/tmp/render/frames', { recursive: true, mode: 0o700 });
  fs.mkdirSync('/tmp/home', { recursive: true, mode: 0o700 });
  const { chromium } = require('/opt/playwright');
  let browser;
  try {
    browser = await chromium.launch({ executablePath: '/opt/browser/chrome-headless-shell', headless: true,
      chromiumSandbox: true, env: { PATH: '/usr/bin:/bin', HOME: '/tmp/home', TMPDIR: '/tmp', LANG: 'C.UTF-8' }, timeout: 15000 });
    const context = await browser.newContext({ viewport: { width: cfg.width, height: cfg.height }, deviceScaleFactor: 1,
      serviceWorkers: 'block', acceptDownloads: false });
    await controls(context);
    let denied = 0, errors = 0, popups = 0, downloads = 0;
    const csp = "default-src 'none'; script-src 'none'; style-src 'unsafe-inline'; img-src https://motion-fixture.invalid; " +
      "media-src https://motion-fixture.invalid; font-src https://motion-fixture.invalid; connect-src 'none'; worker-src 'none'; " +
      "frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
    await context.route('**/*', async route => {
      const request = route.request(), url = request.url(), id = url.startsWith(`${ORIGIN}/`) ? url.slice(ORIGIN.length + 1) : '';
      const asset = assets.get(id);
      if (request.method() !== 'GET' || (url !== `${ORIGIN}/` && !asset)) { denied++; return route.abort(); }
      if (!id) return route.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', headers: { 'content-security-policy': csp }, body: html });
      const requested = request.headers().range;
      if (requested) {
        const selection = asset.contentType === 'video/mp4' ? range(requested, asset.body.length) : null;
        if (!selection) { denied++; return route.abort(); }
        return route.fulfill({ status: 206, contentType: asset.contentType,
          headers: { 'accept-ranges': 'bytes', 'content-range': `bytes ${selection.first}-${selection.last}/${asset.body.length}` },
          body: asset.body.subarray(selection.first, selection.last + 1) });
      }
      return route.fulfill({ status: 200, headers: { 'accept-ranges': 'bytes' }, ...asset });
    });
    const probe = await context.newPage();
    let blocked = false;
    try { await probe.goto('https://outbound-probe.invalid/', { timeout: 5000 }); } catch { blocked = true; }
    await probe.close();
    if (!blocked || denied !== 1) fail('MOTION_RENDER_ROUTE_PROBE_FAILED');
    denied = 0;
    const page = await context.newPage();
    context.on('page', other => { if (other !== page) { popups++; void other.close(); } });
    page.on('pageerror', () => errors++);
    page.on('console', message => { if (message.type() === 'error') errors++; });
    page.on('download', () => downloads++);
    page.setDefaultTimeout(10000);
    await page.goto(`${ORIGIN}/`, { waitUntil: 'load', timeout: 15000 });
    const mediaReady = await deadline(page.evaluate(async () => {
      await document.fonts.ready;
      for (const video of document.querySelectorAll('video')) {
        video.pause();
        if (video.error) return false;
        if (video.readyState < 2) {
          const loaded = await new Promise(resolve => {
            video.addEventListener('loadeddata', () => resolve(true), { once: true });
            video.addEventListener('error', () => resolve(false), { once: true });
          });
          if (!loaded) return false;
        }
      }
      return true;
    }));
    if (!mediaReady) fail('MOTION_RENDER_MEDIA_FAILED');
    await deadline(page.evaluate(scene.toString('utf8')));
    if (!await page.evaluate(() => typeof window.seek === 'function')) fail('MOTION_RENDER_SEEK_MISSING');
    const count = Math.ceil(cfg.duration_ms * 30 / 1000), end = Date.now() + 600000;
    if (cfg.version === 2) {
      const frames = [], images = [];
      let total = 0;
      for (const index of cfg.sample_frames) {
        if (Date.now() > end) fail('MOTION_RENDER_DEADLINE');
        await deadline(page.evaluate(async ms => { await window.seek(ms); }, index * 1000 / 30));
        await deadline(page.evaluate(async () => {
          await document.fonts.ready;
          for (const image of document.querySelectorAll('img')) await image.decode();
        }));
        const png = await page.screenshot({type:'png', animations:'allow', timeout:10000});
        total += png.length;
        if (png.length > 8 * 1024 * 1024 || total > MAX_EVIDENCE) fail('MOTION_RENDER_EVIDENCE_LIMIT');
        const pts = (index / 30).toFixed(6);
        frames.push({ms:Math.round(Number(pts) * 1000), frame_index:index, pts_seconds:pts,
          size:png.length, sha256:hash(png)});
        images.push(png);
      }
      if (denied || errors || popups || downloads) fail('MOTION_RENDER_BROWSER_VIOLATION');
      const rendererFilters = browserSandbox(ownFilters);
      const diagnostics = {frame_count:count, width:cfg.width, height:cfg.height, duration_ms:cfg.duration_ms,
        fps:30, sandbox:true, seccomp:2, host_seccomp_filters:ownFilters, renderer_seccomp_filters:rendererFilters,
        denied_requests:denied, evidence_source:'browser_keyframes', protocol_version:2,
        html_sha256:cfg.html_sha256, scene_sha256:cfg.scene_sha256, config_sha256:hash(configBytes)};
      const empty = Buffer.alloc(0);
      process.stdout.write(Buffer.from(JSON.stringify({version:2, video:{size:0, sha256:hash(empty)}, frames, diagnostics})+'\n'));
      for (const png of images) process.stdout.write(png);
      await context.close();
      return;
    }
    const fingerprints = [];
    const fingerprintEnvironment = cfg.fingerprint_frames ? hash(JSON.stringify({
      browser: browser.version(), node: process.version, platform: process.platform, arch: process.arch,
      runner: hash(fs.readFileSync(__filename)), screenshot: {type:'jpeg', quality:95},
    })) : null;
    let bytes = 0;
    for (let index = 0; index < count; index++) {
      if (Date.now() > end) fail('MOTION_RENDER_DEADLINE');
      await deadline(page.evaluate(async ms => { await window.seek(ms); }, index * 1000 / 30));
      const frame = await page.screenshot({ type: 'jpeg', quality: 95, animations: 'allow', timeout: 10000 });
      if (cfg.fingerprint_frames) fingerprints.push(hash(frame));
      bytes += frame.length;
      if (bytes > 1536 * 1024 * 1024) fail('MOTION_RENDER_FRAME_LIMIT');
      fs.writeFileSync(`/tmp/render/frames/frame-${String(index).padStart(4, '0')}.jpg`, frame, { mode: 0o600 });
    }
    if (denied || errors || popups || downloads) fail('MOTION_RENDER_BROWSER_VIOLATION');
    const rendererFilters = browserSandbox(ownFilters);
    await context.close();
    await browser.close();
    browser = null;
    const output = '/tmp/render/render.mp4';
    command('/usr/bin/ffmpeg', ['-nostdin', '-v', 'error', '-protocol_whitelist', 'file,pipe', '-framerate', '30',
      '-i', '/tmp/render/frames/frame-%04d.jpg', ...audio.inputs, ...(audio.filter ? ['-filter_complex', audio.filter] : []),
      ...audio.mapArgs, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20',
      ...(audio.filter ? ['-c:a', 'aac', '-b:a', '192k'] : []), '-t', (count / 30).toFixed(6), '-movflags', '+faststart', output], 300000);
    const metadata = JSON.parse(command('/usr/bin/ffprobe', ['-v', 'error', '-protocol_whitelist', 'file,pipe',
      '-show_entries', 'format=duration,size:stream=codec_name,codec_type,width,height,avg_frame_rate,duration', '-of', 'json', output]));
    const video = metadata.streams.filter(stream => stream.codec_type === 'video');
    if (video.length !== 1 || video[0].codec_name !== 'h264' || video[0].width !== cfg.width || video[0].height !== cfg.height ||
        video[0].avg_frame_rate !== '30/1' || Math.abs(Number(metadata.format.duration) - count / 30) > 0.1) fail('MOTION_RENDER_OUTPUT_INVALID');
    command('/usr/bin/ffmpeg', ['-nostdin', '-v', 'error', '-protocol_whitelist', 'file,pipe', '-i', output, '-f', 'null', '-']);
    const decoded = JSON.parse(command('/usr/bin/ffprobe', ['-v', 'error', '-protocol_whitelist', 'file,pipe',
      '-select_streams', 'v:0', '-show_frames', '-show_entries', 'frame=best_effort_timestamp_time', '-of', 'json', output]));
    if (decoded.frames.length !== count) fail('MOTION_RENDER_OUTPUT_INVALID');
    const select = cfg.sample_frames.map(index => `eq(n\\,${index})`).join('+');
    command('/usr/bin/ffmpeg', ['-nostdin', '-v', 'error', '-protocol_whitelist', 'file,pipe', '-i', output,
      '-vf', `select=${select}`, '-fps_mode', 'vfr', '/tmp/render/evidence-%04d.png']);
    const frames = [], images = [];
    let evidenceBytes = 0;
    for (const [ordinal, index] of cfg.sample_frames.entries()) {
      const pts = decoded.frames[index].best_effort_timestamp_time;
      if (typeof pts !== 'string' || !/^\d{1,2}\.\d{6}$/.test(pts) || Math.abs(Number(pts) * 1000 - index * 1000 / 30) > 0.5) {
        fail('MOTION_RENDER_TIMESTAMPS_INVALID');
      }
      const png = read(`/tmp/render/evidence-${String(ordinal + 1).padStart(4, '0')}.png`, 8 * 1024 * 1024);
      evidenceBytes += png.length;
      if (evidenceBytes > MAX_EVIDENCE) fail('MOTION_RENDER_EVIDENCE_LIMIT');
      frames.push({ ms: Math.round(Number(pts) * 1000), frame_index: index, pts_seconds: pts, size: png.length, sha256: hash(png) });
      images.push(png);
    }
    const mp4 = read(output, MAX_VIDEO);
    const audioMeasurement = cfg.audio.version === 'motion-audio-v2' ? audioMetrics(output) : null;
    const diagnostics = { frame_count: count, width: cfg.width, height: cfg.height, duration_ms: cfg.duration_ms,
      fps: 30, sandbox: true, seccomp: 2, host_seccomp_filters: ownFilters, renderer_seccomp_filters: rendererFilters,
      denied_requests: denied, audio_mode: cfg.audio.mode, audio_source_spans: audioSourceSpans,
      video_codec: 'h264', protocol_version: 1, evidence_source: 'decoded_mp4',
      ...(audioMeasurement ? {audio_measurements: audioMeasurement} : {}),
      ...(cfg.fingerprint_frames ? {frame_fingerprints: fingerprints, fingerprint_environment: fingerprintEnvironment} : {}),
      html_sha256: cfg.html_sha256, scene_sha256: cfg.scene_sha256, config_sha256: hash(configBytes) };
    const header = Buffer.from(JSON.stringify({ version: 1, video: { size: mp4.length, sha256: hash(mp4) }, frames, diagnostics }) + '\n');
    process.stdout.write(header);
    process.stdout.write(mp4);
    for (const png of images) process.stdout.write(png);
  } finally { if (browser) await browser.close(); }
}

module.exports = { RenderFault, hash, read, command, audioMetrics, deadline, status, isolation, browserSandbox, range, controls, render };
if (require.main === module) {
  render().catch(error => {
    process.stderr.write(JSON.stringify({ event: 'motion.render.failed', code: error instanceof RenderFault ? error.code : 'MOTION_RENDER_EXECUTION_FAILED' }) + '\n');
    process.exitCode = 1;
  });
}
