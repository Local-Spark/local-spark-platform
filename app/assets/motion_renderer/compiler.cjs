'use strict';

// Bounded per-page intermediate contract. The service must authorize and adapt
// MotionDirection and select the render profile before calling this compiler.
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const COLOR = /^#[0-9a-fA-F]{6}$/;
const TOKEN = /^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,79}$/;
const EASING = Object.freeze({
  linear: 'linear', ease_in: 'ease-in', ease_out: 'ease-out', ease_in_out: 'ease-in-out',
});

class InvalidScene extends Error {}
function fail() { throw new InvalidScene('invalid or unsupported scene'); }
function object(value, fields) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) fail();
  const keys = Object.keys(value).sort();
  const required = [...fields].sort();
  if (keys.length !== required.length || keys.some((key, index) => key !== required[index])) fail();
  return value;
}
function integer(value, min, max) {
  if (!Number.isSafeInteger(value) || value < min || value > max) fail();
  return value;
}
function choice(value, values) {
  if (!values.includes(value)) fail();
  return value;
}
function pattern(value, expression) {
  if (typeof value !== 'string' || !expression.test(value)) fail();
  return value;
}
function boundedList(value, min, max) {
  if (!Array.isArray(value) || value.length < min || value.length > max) fail();
  return value;
}

function compileFrame(value, duration) {
  const f = object(value, ['time_ms', 'x', 'y', 'width', 'height', 'scale', 'opacity', 'rotation', 'clip', 'easing']);
  const c = object(f.clip, ['top', 'right', 'bottom', 'left']);
  const clip = {
    top: integer(c.top, 0, 10000), right: integer(c.right, 0, 10000),
    bottom: integer(c.bottom, 0, 10000), left: integer(c.left, 0, 10000),
  };
  if (clip.top + clip.bottom >= 10000 || clip.left + clip.right >= 10000) fail();
  return {
    time_ms: integer(f.time_ms, 0, duration), x: integer(f.x, -20000, 30000),
    y: integer(f.y, -20000, 30000), width: integer(f.width, 1, 30000),
    height: integer(f.height, 1, 30000), scale: integer(f.scale, 1, 40000),
    opacity: integer(f.opacity, 0, 10000), rotation: integer(f.rotation, -360000, 360000),
    clip, easing: choice(f.easing, Object.keys(EASING)),
  };
}

function compileTransition(value, duration) {
  const transition = object(value, ['kind', 'duration_ms']);
  const kind = choice(transition.kind, ['cut', 'fade']);
  const time = integer(transition.duration_ms, 0, duration);
  if ((kind === 'cut') !== (time === 0)) fail();
  return { kind, duration_ms: time };
}

function compileLayer(value, pageDuration, registry) {
  const base = ['kind', 'id', 'start_ms', 'end_ms', 'frames', 'enter', 'exit'];
  if (!value || typeof value !== 'object') fail();
  const kind = choice(value.kind, ['text', 'rectangle', 'circle', 'video', 'image']);
  const fields = kind === 'text' ? [...base, 'text', 'font_id', 'font_size', 'weight', 'align',
    'vertical_align', 'line_height', 'letter_spacing', 'color']
    : kind === 'video' ? [...base, 'source_id', 'fit', 'focus', 'trim_start_ms', 'trim_end_ms']
      : kind === 'image' ? [...base, 'source_id', 'fit', 'focus'] : [...base, 'color'];
  const v = object(value, fields);
  const id = pattern(v.id, UUID);
  const start = integer(v.start_ms, 0, pageDuration - 1);
  const end = integer(v.end_ms, start + 1, pageDuration);
  const duration = end - start;
  const enter = compileTransition(v.enter, duration);
  const exit = compileTransition(v.exit, duration);
  if (enter.duration_ms + exit.duration_ms > duration) fail();
  const frames = boundedList(v.frames, 2, 64).map(frame => compileFrame(frame, duration));
  if (frames[0].time_ms !== 0 || frames.at(-1).time_ms !== duration) fail();
  if (frames.some((frame, index) => index > 0 && frames[index - 1].time_ms >= frame.time_ms)) fail();
  const result = { kind, id, start_ms: start, end_ms: end, enter, exit, frames };
  if (kind === 'text') {
    if (typeof v.text !== 'string' || !v.text.trim() || v.text.length > 500) fail();
    const fontId = pattern(v.font_id, TOKEN);
    if (!registry.fonts.has(fontId)) fail();
    Object.assign(result, { text: v.text, font_id: fontId, font_size: integer(v.font_size, 1, 10000),
      weight: choice(v.weight, [400, 700]), align: choice(v.align, ['left', 'center', 'right']),
      vertical_align: choice(v.vertical_align, ['top', 'center', 'bottom']),
      line_height: integer(v.line_height, 5000, 30000), letter_spacing: integer(v.letter_spacing, -5000, 5000),
      color: pattern(v.color, COLOR) });
  } else if (kind === 'rectangle' || kind === 'circle') {
    result.color = pattern(v.color, COLOR);
  } else {
    const source = pattern(v.source_id, UUID);
    const sourceInfo = registry.sources.get(source);
    if (!sourceInfo || sourceInfo.kind !== kind) fail();
    const focus = object(v.focus, ['x', 'y']);
    Object.assign(result, { source_id: source, fit: choice(v.fit, ['cover', 'contain']),
      focus: { x: integer(focus.x, 0, 10000), y: integer(focus.y, 0, 10000) } });
    if (kind === 'video') {
      integer(sourceInfo.duration_ms, 1, 60000);
      const trimStart = integer(v.trim_start_ms, 0, 60000);
      const trimEnd = integer(v.trim_end_ms, trimStart + 1, 60000);
      if (trimEnd - trimStart !== duration || trimEnd > sourceInfo.duration_ms) fail(); // No hidden speed adjustment.
      Object.assign(result, { trim_start_ms: trimStart, trim_end_ms: trimEnd });
    }
  }
  return result;
}

function compileScene(value, profile, registry) {
  const v = object(value, ['format', 'duration_ms', 'background', 'layers']);
  const format = choice(v.format, ['reel', 'story_video', 'carousel_motion']);
  const p = object(profile, ['width_px', 'height_px', 'fps']);
  const width = integer(p.width_px, 1, 3840);
  const height = integer(p.height_px, 1, 3840);
  const fps = choice(p.fps, [30]);
  if (format === 'carousel_motion') {
    if (width !== 1080 || height !== 1350) fail();
  } else if (!((width === 720 && height === 1280) || (width === 1080 && height === 1920))) {
    fail();
  }
  const duration = format === 'carousel_motion'
    ? integer(v.duration_ms, 5000, 8000) : integer(v.duration_ms, 1, 60000);
  const layers = boundedList(v.layers, 1, 64).map(layer => compileLayer(layer, duration, registry));
  if (new Set(layers.map(layer => layer.id)).size !== layers.length) fail();
  return { format, width, height, fps, duration_ms: duration, background: pattern(v.background, COLOR), layers };
}

module.exports = { InvalidScene, compileScene, EASING };
