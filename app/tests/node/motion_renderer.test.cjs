'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { compileScene, InvalidScene } = require('../../assets/motion_renderer/compiler.cjs');
const { mountScene } = require('../../assets/motion_renderer/runtime.cjs');
const { reel, carouselPage, registry, profiles, frame, ids } = require('../fixtures/motion_layouts.cjs');

test('two layouts compile independently with ordered layers and explicit resource identities', () => {
  const a = reel(), b = carouselPage();
  assert.deepEqual(compileScene(a, profiles.preview, registry).layers.map(x => x.kind), ['video', 'text']);
  assert.deepEqual(compileScene(b, profiles.carousel, registry).layers.map(x => x.kind), ['image', 'rectangle', 'circle']);
  assert.notEqual(compileScene(a, profiles.preview, registry).layers[0].frames, a.layers[0].frames);
  assert.equal(compileScene(a, profiles.portrait, registry).width, 1080);
  a.format = 'story_video';
  assert.equal(compileScene(a, profiles.preview, registry).height, 1280);
  assert.equal(compileScene(a, profiles.portrait, registry).fps, 30);
});

test('trusted profile selects fixed format-specific dimensions and 30 fps', () => {
  const wrong = [null, {}, { ...profiles.preview, height_px: 1920 },
    { ...profiles.preview, width_px: 1080 }, { ...profiles.preview, width_px: 1000 },
    { ...profiles.preview, width_px: 0 }, { ...profiles.preview, height_px: 0 },
    { ...profiles.preview, width_px: 3841 }, { ...profiles.preview, height_px: 3841 },
    { ...profiles.preview, fps: 24 }, { ...profiles.preview, arbitrary: 'value' }, profiles.carousel];
  for (const profile of wrong) assert.throws(() => compileScene(reel(), profile, registry), InvalidScene);
  for (const profile of [profiles.preview, profiles.portrait,
    { ...profiles.carousel, height_px: 1351 }, { ...profiles.carousel, width_px: 1081 }]) {
    assert.throws(() => compileScene(carouselPage(), profile, registry), InvalidScene);
  }
  for (const duration of [4999, 8001]) {
    const page = carouselPage(); page.duration_ms = duration;
    assert.throws(() => compileScene(page, profiles.carousel, registry), InvalidScene);
  }
});

const bad = [
  ['null scene', () => null], ['array scene', () => []],
  ['extra scene field', s => { s.javascript = 'alert(1)'; }],
  ['missing scene field', s => { delete s.format; }],
  ['untrusted dimensions on scene', s => { s.width_px = 720; }],
  ['unknown format', s => { s.format = 'post'; }],
  ['zero duration', s => { s.duration_ms = 0; }], ['NaN duration', s => { s.duration_ms = NaN; }],
  ['no layers', s => { s.layers = []; }], ['non-array layers', s => { s.layers = {}; }],
  ['too many layers', s => { s.layers = Array(65).fill(s.layers[0]); }],
  ['null layer', s => { s.layers[0] = null; }], ['unknown layer', s => { s.layers[0].kind = 'lottie'; }],
  ['layer missing field', s => { delete s.layers[0].frames; }],
  ['transition missing', s => { delete s.layers[0].enter; }],
  ['transition extra field', s => { s.layers[0].enter.delay = 1; }],
  ['unknown transition', s => { s.layers[0].enter.kind = 'wipe'; }],
  ['cut with duration', s => { s.layers[0].enter.duration_ms = 1; }],
  ['fade without duration', s => { s.layers[0].enter.kind = 'fade'; }],
  ['negative fade duration', s => { s.layers[0].enter = { kind: 'fade', duration_ms: -1 }; }],
  ['fractional fade duration', s => { s.layers[0].enter = { kind: 'fade', duration_ms: 1.5 }; }],
  ['fade beyond layer', s => { s.layers[0].exit = { kind: 'fade', duration_ms: 6001 }; }],
  ['overlapping fades', s => { s.layers[0].enter = { kind: 'fade', duration_ms: 3001 };
    s.layers[0].exit = { kind: 'fade', duration_ms: 3000 }; }],
  ['invalid uuid', s => { s.layers[0].id = '../../etc/passwd'; }],
  ['invalid start', s => { s.layers[0].start_ms = 6000; }],
  ['invalid end', s => { s.layers[0].end_ms = 0; }],
  ['missing frames', s => { s.layers[0].frames = []; }],
  ['start frame later', s => { s.layers[0].frames[0].time_ms = 1; }],
  ['final frame early', s => { s.layers[0].frames[1].time_ms = 5999; }],
  ['duplicate frame', s => { s.layers[0].frames = [frame(0), frame(0), frame(6000)]; }],
  ['clip outside', s => { s.layers[0].frames[0].clip.top = 10001; }],
  ['clip empty height', s => { s.layers[0].frames[0].clip.top = 10000; }],
  ['clip empty width', s => { s.layers[0].frames[0].clip.left = 10000; }],
  ['unknown easing', s => { s.layers[0].frames[0].easing = 'url(https://evil)'; }],
  ['bad source uuid', s => { s.layers[0].source_id = 'https://evil'; }],
  ['missing source', s => { s.layers[0].source_id = ids[2]; }],
  ['wrong fit', s => { s.layers[0].fit = 'stretch'; }],
  ['invalid focus', s => { s.layers[0].focus.x = -1; }],
  ['negative trim', s => { s.layers[0].trim_start_ms = -1; }],
  ['trim end before start', s => { s.layers[0].trim_end_ms = 999; }],
  ['implicit speed change', s => { s.layers[0].trim_end_ms = 6999; }],
  ['duplicate layer id', s => { s.layers[1].id = s.layers[0].id; }],
  ['empty text', s => { s.layers[1].text = '  '; }],
  ['non-string text', s => { s.layers[1].text = 3; }],
  ['oversized text', s => { s.layers[1].text = 'x'.repeat(2001); }],
  ['unknown font', s => { s.layers[1].font_id = 'other'; }],
  ['font CSS injection', s => { s.layers[1].font_id = 'a;src:url(evil)'; }],
  ['invalid alignment', s => { s.layers[1].align = 'justify'; }],
  ['invalid vertical alignment', s => { s.layers[1].vertical_align = 'baseline'; }],
  ['invalid font weight', s => { s.layers[1].weight = 600; }],
  ['invalid line height', s => { s.layers[1].line_height = 4999; }],
  ['invalid letter spacing', s => { s.layers[1].letter_spacing = 5001; }],
  ['invalid page color', s => { s.background = 'url(https://evil)'; }],
  ['CSS injection color', s => { s.layers[1].color = 'red;background:url(evil)'; }],
  ['unsupported audio', s => { s.audio = []; }],
];

for (const [name, mutate] of bad) test(`rejects ${name}`, () => {
  const scene = reel();
  const replacement = mutate(scene);
  assert.throws(() => compileScene(replacement === undefined ? scene : replacement, profiles.preview, registry), InvalidScene);
});

test('rejects a source with wrong media type or insufficient duration', () => {
  const scene = reel();
  const wrong = { fonts: registry.fonts, sources: new Map([[scene.layers[0].source_id, { kind: 'image' }]]) };
  assert.throws(() => compileScene(scene, profiles.preview, wrong), InvalidScene);
  wrong.sources.set(scene.layers[0].source_id, { kind: 'video', duration_ms: 6500 });
  assert.throws(() => compileScene(scene, profiles.preview, wrong), InvalidScene);
  wrong.sources.set(scene.layers[0].source_id, { kind: 'video' });
  assert.throws(() => compileScene(scene, profiles.preview, wrong), InvalidScene);
});

class MockElement {
  constructor(tag) { this.tag = tag; this.children = []; this.style = {}; this.textContent = ''; }
  appendChild(child) { this.children.push(child); this.firstChild = this.children[0]; }
  animate(frames, timing) {
    this.frames = frames; this.timing = timing;
    this.animation = { pause() { this.paused = true; }, currentTime: null };
    return this.animation;
  }
}
const doc = { createElement: tag => new MockElement(tag) };

test('runtime uses textContent and fixed DOM styles; video seek is delegated with offsets', async () => {
  const input = reel();
  input.layers[1].text = '<script>alert(1)</script>';
  const scene = compileScene(input, profiles.preview, registry);
  const seeks = [];
  const mounted = mountScene(doc, scene, async (media, time) => seeks.push([media.src, time]));
  const videoEnvelope = mounted.root.children[0], textEnvelope = mounted.root.children[1];
  const videoLayer = videoEnvelope.firstChild, textLayer = textEnvelope.firstChild;
  assert.equal(textLayer.textContent, '<script>alert(1)</script>');
  assert.equal(mounted.root.style.backgroundColor, '#244739');
  assert.equal(textLayer.style.whiteSpace, 'pre-wrap');
  assert.equal(textLayer.children.length, 0);
  assert.equal(videoLayer.firstChild.muted, true);
  await mounted.seek(250);
  assert.equal(textEnvelope.style.visibility, 'hidden');
  await mounted.seek(1000);
  assert.equal(textEnvelope.style.visibility, 'visible');
  assert.equal(textLayer.animation.currentTime, 500);
  assert.equal(textEnvelope.animation.currentTime, 500);
  assert.deepEqual(seeks.map(x => x[1]), [1250, 2000]);
  await assert.rejects(mounted.seek(-1), RangeError);
  await assert.rejects(mounted.seek(6000), RangeError);
  await assert.rejects(mounted.seek(NaN), RangeError);
});

test('runtime paints image, rectangle and circle in array order', async () => {
  const scene = compileScene(carouselPage(), profiles.carousel, registry);
  const mounted = mountScene(doc, scene, async () => { throw Error('no video'); });
  assert.deepEqual(mounted.root.children.map(x => x.tag), ['div', 'div', 'div']);
  assert.equal(mounted.root.children[0].firstChild.firstChild.tag, 'img');
  assert.equal(mounted.root.children[1].firstChild.style.backgroundColor, '#244739');
  assert.equal(mounted.root.children[2].firstChild.style.borderRadius, '50%');
  await mounted.seek(2000);
});

test('fade envelope remains separate from animated layer opacity and geometry', async () => {
  const input = reel();
  const layer = input.layers[1];
  layer.enter = { kind: 'fade', duration_ms: 1000 };
  layer.exit = { kind: 'fade', duration_ms: 2000 };
  layer.frames[0].opacity = 5000;
  layer.frames[1].opacity = 2000;
  const mounted = mountScene(doc, compileScene(input, profiles.preview, registry), async () => {});
  const envelope = mounted.root.children[1];
  const inner = envelope.firstChild;
  assert.deepEqual(envelope.frames.map(f => [f.offset, f.opacity]), [[0, 0], [0.2, 1], [0.6, 1], [1, 0]]);
  assert.deepEqual(inner.frames.map(f => f.opacity), [0.5, 0.2]);
  assert.equal(inner.frames[1].left, '10%');
  await mounted.seek(1000);
  assert.equal(envelope.animation.currentTime, 500);
  assert.equal(inner.animation.currentTime, 500);
});

test('fade envelopes handle cuts and adjacent or full-duration fades', () => {
  for (const [enter, exit, expected] of [
    [0, 0, [[0, 1], [1, 1]]],
    [2000, 3000, [[0, 0], [0.4, 1], [1, 0]]],
    [5000, 0, [[0, 0], [1, 1]]],
    [0, 5000, [[0, 1], [1, 0]]],
  ]) {
    const input = reel();
    input.layers[1].enter = { kind: enter ? 'fade' : 'cut', duration_ms: enter };
    input.layers[1].exit = { kind: exit ? 'fade' : 'cut', duration_ms: exit };
    const mounted = mountScene(doc, compileScene(input, profiles.preview, registry), async () => {});
    assert.deepEqual(mounted.root.children[1].frames.map(f => [f.offset, f.opacity]), expected);
  }
});
