'use strict';

// IO-only substitutions: the production runner and its browser callbacks execute
// unchanged, with in-memory files and a deterministic browser/media boundary.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
const filename = path.resolve(__dirname, '../../assets/motion_html_renderer/runner.cjs');
const source = fs.readFileSync(filename, 'utf8');
const sha = value => crypto.createHash('sha256').update(value).digest('hex');
const origin = 'https://motion-fixture.invalid';

function environment(options = {}) {
  const html = Buffer.from('<video src="assets/source.mp4"></video>');
  const scene = Buffer.from('window.seek = async ms => window.times.push(ms)');
  const files = new Map([
    ['/input/index.html', html], ['/input/scene.js', scene],
    ['/input/asset-0', Buffer.from('source')], ['/input/asset-1', Buffer.from('image')],
    ['/tmp/render/render.mp4', Buffer.from('encoded final mp4')],
  ]);
  const cfg = {
    version: 1, fps: 30, width: 64, height: 64, duration_ms: 100,
    html_sha256: sha(html), scene_sha256: sha(scene), sample_frames: [0, 2],
    assets: [
      {id: 'assets/source.mp4', file: 'asset-0', mime_type: 'video/mp4', sha256: sha(files.get('/input/asset-0'))},
      {id: 'assets/image.png', file: 'asset-1', mime_type: 'image/png', sha256: sha(files.get('/input/asset-1'))},
    ], audio: {mode: 'silent', tracks: []},
  };
  if (options.configure) options.configure(cfg, files);
  files.set('/input/config.json', Buffer.from(JSON.stringify(cfg)));
  for (let ordinal = 0; ordinal < (Array.isArray(cfg.sample_frames) ? cfg.sample_frames.length : 0); ordinal++) {
    const key = `/tmp/render/evidence-${String(ordinal + 1).padStart(4, '0')}.png`;
    if (!files.has(key)) files.set(key, Buffer.from(`PNG decoded frame ${ordinal}`));
  }
  const writes = [], commands = [], stdout = [], stderr = [], responses = [], events = {};
  const window = {times: []};
  const video = {
    readyState: options.loadedVideo ? 2 : 1,
    error: options.videoAlreadyFailed ? {code: 4} : null,
    pause() { this.paused = true; },
    addEventListener(name, callback) {
      if (name === (options.videoError ? 'error' : 'loadeddata')) queueMicrotask(() => callback(new Error('video read failed')));
    },
  };
  let router, opened = 0, browserClosed = 0, contextClosed = 0, deniedProbe = 0;
  const proc = {
    version: 'synthetic-node', platform: 'synthetic-platform', arch: 'synthetic-arch',
    getuid: () => 65532,
    stdout: {write: value => stdout.push(Buffer.from(value))},
    stderr: {write: value => stderr.push(String(value))},
  };
  const module = {exports: {}};
  let sandbox;
  async function request(url, method = 'GET', headers = {}) {
    let aborted = false;
    const route = {
      request: () => ({url: () => url, method: () => method, headers: () => headers}),
      abort: async () => { aborted = true; },
      fulfill: async response => { responses.push({url, ...response}); },
    };
    await router(route);
    return aborted;
  }
  const page = {
    on(name, callback) { events[name] = callback; },
    setDefaultTimeout(value) { this.timeout = value; },
    async goto(url) {
      await request(url);
      for (const [target, method, headers] of options.requests || []) await request(target, method, headers);
      if (options.violation === 'request') await request('https://external.invalid/');
    },
    async evaluate(fn, arg) {
      if (typeof fn === 'string') {
        if (!options.noSeek) vm.runInContext(fn, sandbox);
        return;
      }
      return fn(arg);
    },
    async screenshot() {
      if (options.violation === 'error') events.pageerror(new Error('private detail'));
      if (options.violation === 'console') events.console({type: () => 'error'});
      events.console({type: () => 'log'});
      if (options.violation === 'download') events.download({});
      if (options.violation === 'popup') events.page({close: async () => {}});
      events.page(page);
      return options.screenshot || Buffer.from('jpeg');
    },
  };
  const context = {
    async addInitScript(fn) { fn(); },
    async routeWebSocket(pattern, callback) { callback({close: value => { this.websocket = value; }}); },
    async route(pattern, callback) { router = callback; },
    async newPage() {
      opened++;
      if (opened > 1) return page;
      return {
        async goto(url) {
          if (options.probe === 'bypassed') return;
          if (options.probe === 'unrouted') throw Error('probe never reached route');
          const aborted = await request(url);
          deniedProbe += Number(aborted);
          if (aborted) throw Error('expected network block');
        }, async close() {},
      };
    },
    on(name, fn) { events[name] = fn; },
    async close() { contextClosed++; },
  };
  const browser = {
    version: () => 'synthetic-browser',
    async newContext(config) { this.contextOptions = config; return context; },
    async close() { browserClosed++; },
  };
  const chromium = {async launch(config) {
    this.options = config;
    if (options.launchError) throw Error('untrusted private launch detail');
    return browser;
  }};
  const io = {
    lstatSync(file) {
      const body = files.get(file);
      if (!body) throw Error(`missing fixture ${file}`);
      return {isFile: () => true, size: body.length};
    },
    readFileSync(file, encoding) {
      if (file === filename) return Buffer.from(source);
      if (file.startsWith('/proc/')) {
        if (file.endsWith('cmdline')) return 'chrome\0--type=renderer\0';
        const filters = file === '/proc/self/status' ? 1 : 2;
        return `Name:\trenderer\nCapEff:\t0000000000000000\nNoNewPrivs:\t1\nSeccomp:\t2\nSeccomp_filters:\t${filters}\n`;
      }
      const body = files.get(file);
      if (!body) throw Error(`missing fixture ${file}`);
      return encoding ? body.toString(encoding) : body;
    },
    readdirSync: () => ['self', '100'],
    mkdirSync: (...args) => writes.push({mkdir: args}),
    writeFileSync: (...args) => writes.push({file: args}),
  };
  const spawnSync = (binary, args, config) => {
    commands.push({binary, args, config});
    if (options.commandFailure) return {status: 1, stdout: Buffer.alloc(0)};
    const count = Math.ceil(cfg.duration_ms * 30 / 1000);
    let result = {};
    if (binary.endsWith('ffprobe') && args.includes('-show_frames')) {
      result = {frames: Array.from({length: count}, (_, i) => ({best_effort_timestamp_time: (i / 30).toFixed(6)}))};
      if (options.decoded) options.decoded(result);
    } else if (binary.endsWith('ffprobe') && args.at(-1) === '/tmp/render/render.mp4') {
      result = {streams: [{codec_type: 'video', codec_name: 'h264', width: cfg.width, height: cfg.height, avg_frame_rate: '30/1'}], format: {duration: count / 30}};
      if (options.metadata) options.metadata(result);
    } else if (binary.endsWith('ffprobe')) {
      result = {streams: [{codec_type: 'audio'}], format: {duration: 1}};
      if (options.audioMetadata) options.audioMetadata(result);
    }
    return {status: 0, stdout: Buffer.from(JSON.stringify(result))};
  };
  const mocks = {'node:fs': io, 'node:child_process': {spawnSync}, '/opt/playwright': {chromium},
    './audio.cjs': require('../../assets/motion_html_renderer/audio.cjs')};
  const load = name => Object.hasOwn(mocks, name) ? mocks[name] : require(name);
  load.main = options.main ? module : undefined;
  let ticks = 0;
  sandbox = vm.createContext({require: load, module, __filename: filename, process: proc, Buffer, Map, setTimeout, clearTimeout,
    window, document: {fonts: {ready: Promise.resolve()}, querySelectorAll: () => [video]},
    Date: options.expired ? {now: () => (++ticks === 1 ? 0 : 600001)} : Date});
  new vm.Script(source, {filename}).runInContext(sandbox);
  return {runner: module.exports, run: () => module.exports.render(), cfg, files, writes, commands,
    stdout, stderr, responses, window, video, chromium, browser, context, process: proc,
    closed: () => ({browser: browserClosed, context: contextClosed, deniedProbe})};
}

module.exports = {environment, origin, sha};
