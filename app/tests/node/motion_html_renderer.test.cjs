'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const vm = require('node:vm');
const renderer = require('../../assets/motion_html_renderer/runner.cjs');
const { environment, origin, sha } = require('../fixtures/motion_html_environment.cjs');

test('bounded immutable inputs reject symlinks, large files and changed hashes', t => {
  const folder = fs.mkdtempSync(path.join(os.tmpdir(), 'motion-runner-test-'));
  t.after(() => fs.rmSync(folder, { recursive: true, force: true }));
  const file = path.join(folder, 'data');
  fs.writeFileSync(file, 'content');
  const data = renderer.read(file, 7, renderer.hash(Buffer.from('content')));
  assert.equal(data.toString(), 'content');
  assert.throws(() => renderer.read(file, 6), /INPUT_LIMIT/);
  assert.throws(() => renderer.read(folder, 10), /INPUT_LIMIT/);
  fs.symlinkSync(file, path.join(folder, 'link'));
  assert.throws(() => renderer.read(path.join(folder, 'link'), 10), /INPUT_LIMIT/);
  assert.throws(() => renderer.read(file, 10, '0'.repeat(64)), /INPUT_CHANGED/);
});

test('byte ranges reject suffix, invalid order and overflow', () => {
  assert.deepEqual(renderer.range('bytes=0-', 10), { first: 0, last: 9 });
  assert.deepEqual(renderer.range('bytes=2-4', 10), { first: 2, last: 4 });
  assert.deepEqual(renderer.range('bytes=2-20', 10), { first: 2, last: 9 });
  for (const value of ['bytes=-2', 'bytes=4-2', 'bytes=10-', 'bytes=999999999999999999-', 'wrong']) {
    assert.equal(renderer.range(value, 10), null);
  }
});

test('local commands have bounded output and operational errors', () => {
  assert.equal(renderer.command('/bin/echo', ['ok']).toString(), 'ok\n');
  assert.throws(() => renderer.command('/missing/tool', []), /MEDIA_FAILED/);
  assert.throws(() => renderer.command(process.execPath, ['-e', 'process.exit(1)']), /MEDIA_FAILED/);
});

test('deadline settles successful work and rejects stalled browser evaluation', async () => {
  assert.equal(await renderer.deadline(Promise.resolve(7)), 7);
  await assert.rejects(renderer.deadline(new Promise(() => {}), 1), /BROWSER_TIMEOUT/);
});

test('browser controls make external peer APIs immutable and block WebSocket', async () => {
  let init, socketHandler;
  await renderer.controls({
    addInitScript: async fn => { init = fn; },
    routeWebSocket: async (pattern, fn) => { assert.equal(pattern, '**/*'); socketHandler = fn; },
  });
  const window = {};
  vm.runInNewContext(`(${init.toString()})();`, { window });
  assert.equal(window.RTCPeerConnection, undefined);
  assert.equal(window.WebTransport, undefined);
  assert.equal(window.open('https://external.invalid'), null);
  assert.equal(Object.getOwnPropertyDescriptor(window, 'RTCPeerConnection').configurable, false);
  let closed;
  socketHandler({ close: value => { closed = value; } });
  assert.equal(closed.code, 1008);
});

test('OS isolation refuses missing privilege and seccomp boundaries', t => {
  let values = { CapEff: '0000000000000000', NoNewPrivs: '1', Seccomp: '2', Seccomp_filters: '1' };
  let uid = 65532;
  t.mock.method(process, 'getuid', () => uid);
  t.mock.method(fs, 'readFileSync', () => Object.entries(values).map(([key, value]) => `${key}:\t${value}`).join('\n'));
  assert.equal(renderer.isolation(), 1);
  for (const [key, value] of [['CapEff', '1'], ['NoNewPrivs', '0'], ['Seccomp', '0']]) {
    const original = values[key]; values[key] = value;
    assert.throws(() => renderer.isolation(), /OS_ISOLATION_FAILED/);
    values[key] = original;
  }
  for (const value of [undefined, 'invalid', '1.5', '9007199254740992', '0']) {
    if (value === undefined) delete values.Seccomp_filters;
    else values.Seccomp_filters = value;
    assert.throws(() => renderer.isolation(), /OS_ISOLATION_FAILED/);
  }
  values.Seccomp_filters = '1';
  uid = 0;
  assert.throws(() => renderer.isolation(), /OS_ISOLATION_FAILED/);
});

test('Chromium renderer must install an additional seccomp filter', t => {
  let command = ['chrome', '--type=renderer'];
  let separator = '\0';
  let child = 'Seccomp:\t2\nNoNewPrivs:\t1\nSeccomp_filters:\t2\n';
  let failure;
  t.mock.method(fs, 'readdirSync', () => ['self', '10']);
  t.mock.method(fs, 'readFileSync', file => {
    if (failure) throw failure;
    return file.endsWith('cmdline') ? command.join(separator) : child;
  });
  assert.equal(renderer.browserSandbox(1), 2);
  // Chromium's rewritten process title can be whitespace-delimited, while
  // ordinary /proc cmdline retains NUL-separated argv. Both still need proof.
  for (const value of [' ', '\t', '\0 ']) {
    separator = value;
    assert.equal(renderer.browserSandbox(1), 2);
  }
  for (const field of ['--no-sandbox', 'Seccomp', 'NoNewPrivs', 'Seccomp_filters']) {
    const original = child;
    if (field.startsWith('--')) command.push(field);
    else child = child.replace(new RegExp(`${field}:\\t\\d+`), `${field}:\t0`);
    assert.throws(() => renderer.browserSandbox(1), /BROWSER_SANDBOX_FAILED/);
    command = ['chrome', '--type=renderer']; child = original;
  }
  for (const value of [undefined, 'invalid', '1.5', '9007199254740992']) {
    const original = child;
    child = value === undefined ? child.replace(/Seccomp_filters:\t\d+\n/, '')
      : child.replace(/Seccomp_filters:\t\d+/, `Seccomp_filters:\t${value}`);
    assert.throws(() => renderer.browserSandbox(1), /BROWSER_SANDBOX_FAILED/);
    child = original;
  }
  command = ['chrome', '--type=utility'];
  assert.throws(() => renderer.browserSandbox(1), /SANDBOX_UNPROVEN/);
  command = ['chrome', '--type=renderer'];
  for (const code of ['ENOENT', 'ESRCH']) {
    failure = Object.assign(new Error('process exited'), { code });
    assert.throws(() => renderer.browserSandbox(1), /SANDBOX_UNPROVEN/);
  }
  failure = Object.assign(new Error('unreadable status'), { code: 'EACCES' });
  assert.throws(() => renderer.browserSandbox(1), /unreadable status/);
});

test('runner renders each exact frame and binds decoded MP4 evidence to private inputs', async () => {
  const fixture = environment({requests: [
    [`${origin}/assets/source.mp4`, 'GET', {range: 'bytes=1-3'}],
    [`${origin}/assets/image.png`, 'GET', {}],
  ]});
  await fixture.run();
  assert.equal(fixture.chromium.options.chromiumSandbox, true);
  assert.equal(fixture.browser.contextOptions.serviceWorkers, 'block');
  assert.equal(fixture.browser.contextOptions.acceptDownloads, false);
  assert.deepEqual(fixture.window.times, [0, 1000 / 30, 2000 / 30]);
  assert.equal(fixture.video.paused, true);
  assert.equal(fixture.window.open('https://external.invalid'), null);
  assert.deepEqual(fixture.closed(), {browser: 1, context: 1, deniedProbe: 1});
  const header = JSON.parse(fixture.stdout[0]);
  assert.equal(header.video.sha256, sha(fixture.stdout[1]));
  assert.equal(header.diagnostics.config_sha256, sha(fixture.files.get('/input/config.json')));
  assert.equal(header.diagnostics.html_sha256, fixture.cfg.html_sha256);
  assert.equal(header.diagnostics.scene_sha256, fixture.cfg.scene_sha256);
  assert.equal(header.diagnostics.evidence_source, 'decoded_mp4');
  assert.deepEqual(header.diagnostics.audio_source_spans, []);
  assert.deepEqual(header.frames.map(x => x.frame_index), [0, 2]);
  assert.deepEqual(header.frames.map(x => x.pts_seconds), ['0.000000', '0.066667']);
  assert.ok(header.frames.every((x, i) => x.sha256 === sha(fixture.stdout[i + 2])));
  const ranged = fixture.responses.find(x => x.status === 206);
  assert.equal(ranged.headers['content-range'], 'bytes 1-3/6');
  assert.equal(ranged.body.toString(), 'our');
  assert.match(fixture.responses[0].headers['content-security-policy'], /connect-src 'none'/);
  assert.ok(fixture.commands.some(x => x.args.includes('select=eq(n\\,0)+eq(n\\,2)')));
  assert.ok(fixture.commands.some(x => x.args.includes('-an')));
});

test('runner keeps video audio authorized separately and encodes the measured mix', async () => {
  const fixture = environment({loadedVideo: true, configure(cfg) {
    cfg.audio = {mode: 'mix', tracks: [{asset_id: 'assets/source.mp4', offset_ms: 0,
      trim_start_ms: 0, trim_end_ms: 100, volume: 1}]};
  }});
  await fixture.run();
  const encode = fixture.commands.find(x => x.args.includes('libx264'));
  assert.ok(encode.args.includes('-filter_complex') && encode.args.includes('aac'));
  const diagnostics = JSON.parse(fixture.stdout[0]).diagnostics;
  assert.equal(diagnostics.audio_mode, 'mix');
  assert.equal(diagnostics.audio_source_spans[0].ends_before_planned_trim, false);
});

test('historical absolute asset URLs remain byte-identical under the fixed private origin', async () => {
  // Generated HTML may omit a charset declaration: preserve Portuguese and symbols.
  const historical = Buffer.from('<h1>Café Pausa — Faça uma pausa →</h1><video src="https://motion-fixture.invalid/assets/source.mp4"></video>');
  const fixture = environment({
    requests: [['https://motion-fixture.invalid/assets/source.mp4', 'GET', {}]],
    configure(cfg, files) {
      files.set('/input/index.html', historical);
      cfg.html_sha256 = sha(historical);
    },
  });
  await fixture.run();
  const document = fixture.responses.find(response => response.url === 'https://motion-fixture.invalid/');
  assert.equal(document.contentType, 'text/html; charset=utf-8');
  assert.equal(document.url, 'https://motion-fixture.invalid/');
  assert.deepEqual(document.body, historical);
  const policy = document.headers['content-security-policy'];
  for (const kind of ['img', 'media', 'font']) {
    assert.ok(policy.includes(`${kind}-src https://motion-fixture.invalid;`));
  }
  assert.ok(!policy.includes('motion-render.invalid'));
  assert.equal(fixture.responses.find(response => response.url.endsWith('/assets/source.mp4')).body.toString(), 'source');
  assert.equal(JSON.parse(fixture.stdout[0]).diagnostics.html_sha256, sha(historical));
});

for (const host of ['https://motion-render.invalid', 'https://motion-fixture.invalid.example', 'http://motion-fixture.invalid']) {
  test(`same asset path cannot authorize a different origin ${host}`, async () => {
    const fixture = environment({requests: [[`${host}/assets/source.mp4`, 'GET', {}]]});
    await assert.rejects(fixture.run(), /BROWSER_VIOLATION/);
    assert.equal(fixture.stdout.length, 0);
    assert.ok(!fixture.responses.some(response => response.url.startsWith(`${host}/`)));
  });
}

const badProfiles = [
  ['version', 0], ['fps', 24], ['duration_ms', 0], ['duration_ms', 60001], ['duration_ms', 0.5],
  ['width', 63], ['width', 1922], ['width', 65], ['width', 64.5],
  ['height', 63], ['height', 1922], ['height', 65], ['height', 64.5],
  ['assets', null], ['assets', Array(33).fill({})],
  ['sample_frames', null], ['sample_frames', []], ['sample_frames', Array(65).fill(0)],
  ['sample_frames', [-1]], ['sample_frames', [3]], ['sample_frames', [0.5]],
];
for (const [field, value] of badProfiles) test(`runner rejects invalid profile ${field}=${JSON.stringify(value)}`, async () => {
  const fixture = environment({configure(cfg) { cfg[field] = value; }});
  await assert.rejects(fixture.run(), /PROFILE_INVALID/);
  assert.equal(fixture.stdout.length, 0);
  assert.equal(fixture.chromium.options, undefined);
});

for (const [field, value] of [['id', '../escape'], ['id', 'assets/source.mp4'], ['file', 'other'], ['mime_type', 'text/html']]) {
  test(`runner rejects untrusted or duplicate asset ${field}=${value}`, async () => {
    const fixture = environment({configure(cfg) { cfg.assets[1][field] = value; }});
    await assert.rejects(fixture.run(), /ASSET_INVALID/);
    assert.equal(fixture.chromium.options, undefined);
  });
}

for (const probe of ['bypassed', 'unrouted']) test(`route probe must demonstrate a real block: ${probe}`, async () => {
  const fixture = environment({probe});
  await assert.rejects(fixture.run(), /ROUTE_PROBE_FAILED/);
  assert.equal(fixture.closed().browser, 1);
  assert.equal(fixture.stdout.length, 0);
});

for (const requests of [
  [[`${origin}/assets/source.mp4`, 'POST', {}]],
  [[`${origin}/assets/source.mp4`, 'GET', {range: 'bytes=-1'}]],
  [[`${origin}/assets/image.png`, 'GET', {range: 'bytes=0-1'}]],
]) test(`route refuses method and range misuse ${JSON.stringify(requests)}`, async () => {
  const fixture = environment({requests});
  await assert.rejects(fixture.run(), /BROWSER_VIOLATION/);
  assert.equal(fixture.stdout.length, 0);
  assert.equal(fixture.closed().browser, 1);
});

for (const violation of ['request', 'error', 'console', 'download', 'popup']) test(`browser ${violation} fails closed`, async () => {
  const fixture = environment({violation});
  await assert.rejects(fixture.run(), /BROWSER_VIOLATION/);
  assert.equal(fixture.stdout.length, 0);
  assert.equal(fixture.closed().browser, 1);
});

for (const [options, expected] of [
  [{noSeek: true}, /SEEK_MISSING/], [{expired: true}, /RENDER_DEADLINE/],
  [{launchError: true}, /private launch detail/], [{videoError: true}, /MEDIA_FAILED/],
  [{videoAlreadyFailed: true}, /MEDIA_FAILED/],
  [{commandFailure: true}, /MEDIA_FAILED/],
]) test(`runner stops and closes browser on ${expected}`, async () => {
  const fixture = environment(options);
  await assert.rejects(fixture.run(), expected);
  assert.equal(fixture.stdout.length, 0);
  assert.equal(fixture.closed().browser, options.launchError ? 0 : 1);
});

const badMetadata = [
  data => { data.streams = []; }, data => { data.streams.push({...data.streams[0]}); },
  data => { data.streams[0].codec_name = 'vp9'; }, data => { data.streams[0].width = 66; },
  data => { data.streams[0].height = 66; }, data => { data.streams[0].avg_frame_rate = '24/1'; },
  data => { data.format.duration = 2; },
];
for (const [index, metadata] of badMetadata.entries()) test(`encoded video metadata mismatch ${index}`, async () => {
  const fixture = environment({metadata});
  await assert.rejects(fixture.run(), /OUTPUT_INVALID/);
  assert.equal(fixture.stdout.length, 0);
});

test('decoded frame count and timestamps must match the rendered timeline', async () => {
  const short = environment({decoded(data) { data.frames.pop(); }});
  await assert.rejects(short.run(), /OUTPUT_INVALID/);
  for (const pts of [0, 'bad', '0.999999']) {
    const fixture = environment({decoded(data) { data.frames[0].best_effort_timestamp_time = pts; }});
    await assert.rejects(fixture.run(), /TIMESTAMPS_INVALID/);
    assert.equal(fixture.stdout.length, 0);
  }
});

for (const [index, audioMetadata] of [
  data => { data.streams = [{codec_type: 'video'}]; },
  data => { data.format.duration = 'invalid'; },
  data => { data.format.duration = 0; },
  data => { data.format.duration = -1; },
].entries()) test(`audio plan is verified against supplied media ${index}`, async () => {
  const fixture = environment({audioMetadata, configure(cfg) {
    cfg.audio = {mode: 'mix', tracks: [{asset_id: 'assets/source.mp4', offset_ms: 0,
      trim_start_ms: 0, trim_end_ms: 100, volume: 1}]};
  }});
  await assert.rejects(fixture.run(), /AUDIO_INVALID/);
  assert.equal(fixture.chromium.options, undefined);
});

test('qualified Intensa trim keeps its plan when source ends 3.312ms earlier, and discloses it', async () => {
  const fixture = environment({audioMetadata(data) { data.format.duration = 11.176688; }, configure(cfg) {
    cfg.duration_ms = 11200;
    cfg.audio = {mode:'mix',tracks:[{asset_id:'assets/source.mp4',offset_ms:0,
      trim_start_ms:0,trim_end_ms:11180,volume:1}]};
  }});
  await fixture.run();
  const span = JSON.parse(fixture.stdout[0]).diagnostics.audio_source_spans[0];
  assert.equal(span.asset_id, 'assets/source.mp4');
  assert.equal(span.trim_start_ms, 0);
  assert.equal(span.trim_end_ms, 11180);
  assert.ok(Math.abs(span.available_ms - 11176.688) < 0.000001);
  assert.equal(span.ends_before_planned_trim, true);
  const args = fixture.commands.find(x => x.args.includes('libx264')).args;
  const filter = args[args.indexOf('-filter_complex') + 1];
  assert.match(filter, /atrim=start=0:duration=11\.18,asetpts=PTS-STARTPTS,volume=1/);
  assert.ok(!filter.includes('apad'));
});

for (const start of [100,101]) test(`audio cannot begin at or after EOF (${start}ms)`, async () => {
  const fixture = environment({audioMetadata(data) { data.format.duration = 0.1; }, configure(cfg) {
    cfg.duration_ms = 200;
    cfg.audio = {mode:'mix',tracks:[{asset_id:'assets/source.mp4',offset_ms:0,
      trim_start_ms:start,trim_end_ms:150,volume:1}]};
  }});
  await assert.rejects(fixture.run(), /AUDIO_INVALID/);
  assert.equal(fixture.chromium.options, undefined);
  assert.equal(fixture.stdout.length, 0);
});

test('entry point emits only stable codes for known and unexpected failures', async () => {
  for (const options of [{configure(cfg) { cfg.version = 3; }}, {launchError: true}]) {
    const fixture = environment({...options, main: true});
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(fixture.process.exitCode, 1);
    const record = JSON.parse(fixture.stderr.join(''));
    assert.equal(record.event, 'motion.render.failed');
    assert.equal(record.code, options.launchError ? 'MOTION_RENDER_EXECUTION_FAILED' : 'MOTION_RENDER_PROFILE_INVALID');
    assert.ok(!fixture.stderr.join('').includes('private'));
    assert.equal(fixture.stdout.length, 0);
  }
});

// Model reported IO sizes without allocating hundreds of megabytes in a unit
// test. The real runner's guards must stop before storing/serializing the data.
function sizedBytes(length) {
  const bytes = Buffer.from('bounded fixture');
  Object.defineProperty(bytes, 'length', {value: length});
  return bytes;
}

test('total input, captured frames and decoded evidence each have an independent cap', async () => {
  const inputs = environment({configure(cfg, files) {
    for (const item of cfg.assets) {
      const body = sizedBytes(130 * 1024 * 1024);
      files.set(`/input/${item.file}`, body);
      item.sha256 = sha(body);
    }
  }});
  await assert.rejects(inputs.run(), /INPUT_LIMIT/);
  assert.equal(inputs.chromium.options, undefined);

  const capture = environment({screenshot: sizedBytes(1536 * 1024 * 1024 + 1)});
  await assert.rejects(capture.run(), /FRAME_LIMIT/);
  assert.equal(capture.closed().browser, 1);
  assert.ok(!capture.writes.some(x => x.file));

  const evidence = environment({configure(cfg, files) {
    cfg.duration_ms = 200;
    cfg.sample_frames = [0, 1, 2, 3, 4];
    for (let index = 1; index <= 5; index++) {
      files.set(`/tmp/render/evidence-${String(index).padStart(4, '0')}.png`, sizedBytes(7 * 1024 * 1024));
    }
  }});
  await assert.rejects(evidence.run(), /EVIDENCE_LIMIT/);
  assert.equal(evidence.stdout.length, 0);
});

test('storyboard protocol seeks only requested scenes and never encodes video or audio', async () => {
  const png = Buffer.from('\x89PNG\r\n\x1a\nsynthetic', 'binary');
  const env = environment({screenshot:png});
  env.cfg.version = 2;
  env.cfg.sample_frames = [0,2];
  env.files.set('/input/config.json', Buffer.from(JSON.stringify(env.cfg)));
  // The fixture exposes a video for every selector; no synthetic image needs decode.
  env.video.decode = async () => {};
  await env.run();
  const result = Buffer.concat(env.stdout);
  const header = JSON.parse(result.subarray(0,result.indexOf(10)).toString());
  assert.equal(header.version,2);
  assert.equal(header.video.size,0);
  assert.equal(header.diagnostics.evidence_source,'browser_keyframes');
  assert.deepEqual(header.frames.map(f=>f.frame_index),[0,2]);
  assert.equal(env.commands.length,0);
  assert.equal(env.window.times.length,2);
});
