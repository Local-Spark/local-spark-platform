'use strict';

const videoId = '11111111-1111-4111-8111-111111111111';
const imageId = '22222222-2222-4222-8222-222222222222';
const ids = ['33333333-3333-4333-8333-333333333333', '44444444-4444-4444-8444-444444444444',
  '55555555-5555-4555-8555-555555555555'];
const registry = { sources: new Map([[videoId, { kind: 'video', duration_ms: 10000 }],
  [imageId, { kind: 'image' }]]), fonts: new Set(['kit_sans']) };
const profiles = {
  preview: { width_px: 720, height_px: 1280, fps: 30 },
  portrait: { width_px: 1080, height_px: 1920, fps: 30 },
  carousel: { width_px: 1080, height_px: 1350, fps: 30 },
};
const frame = (time_ms, x = 0) => ({
  time_ms, x, y: 0, width: 10000, height: 10000, scale: 10000, opacity: 10000, rotation: 0,
  clip: { top: 0, right: 0, bottom: 0, left: 0 }, easing: 'linear',
});
const base = (kind, id, start_ms, end_ms) => ({
  kind, id, start_ms, end_ms, enter: { kind: 'cut', duration_ms: 0 }, exit: { kind: 'cut', duration_ms: 0 },
  frames: [frame(0), frame(end_ms - start_ms, 1000)],
});
const reel = () => ({
  format: 'reel', duration_ms: 6000, background: '#244739',
  layers: [
    { ...base('video', ids[0], 0, 6000), source_id: videoId, fit: 'cover',
      focus: { x: 5000, y: 5000 }, trim_start_ms: 1000, trim_end_ms: 7000 },
    { ...base('text', ids[1], 500, 5500), text: 'Pausa fictícia', font_id: 'kit_sans',
      font_size: 500, weight: 700, align: 'center', vertical_align: 'center',
      line_height: 12000, letter_spacing: 0, color: '#f5f0e7' },
  ],
});
const carouselPage = () => ({
  format: 'carousel_motion', duration_ms: 5000, background: '#f5f0e7',
  layers: [
    { ...base('image', ids[0], 0, 5000), source_id: imageId, fit: 'contain', focus: { x: 0, y: 10000 } },
    { ...base('rectangle', ids[1], 0, 5000), color: '#244739' },
    { ...base('circle', ids[2], 0, 5000), color: '#bb7a48' },
  ],
});

module.exports = { reel, carouselPage, registry, profiles, frame, ids, videoId, imageId };
