'use strict';

// Private evaluation helper. Asset paths MUST already have been verified by hash
// and their audio streams/durations inspected by the trusted caller. A trim end
// past EOF yields a shorter event, as FFmpeg does; the caller must disclose it.
// This does not
// certify audio rights, speech semantics, loudness or perceptual quality.
const path = require('node:path');
const ID = /^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$/;
const MAX_MS = 60000;
const MAX_TRACKS = 16;

function invalid() { throw new Error('invalid evaluation audio plan'); }
function objectWithKeys(value, keys) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) invalid();
  const actual = Object.keys(value).sort();
  if (actual.length !== keys.length || actual.some((key, i) => key !== keys[i])) invalid();
}
function millis(value) {
  if (!Number.isSafeInteger(value) || value < 0 || value > MAX_MS) invalid();
  return value;
}
function seconds(ms) {
  return (ms / 1000).toFixed(3).replace(/0+$/, '').replace(/\.$/, '') || '0';
}

/**
 * Returns arguments for FFmpeg, without invoking a command or using a shell.
 * Video is input 0, so callers append `inputs` after the image/video input.
 * A mix contains independently timed events; the same asset can recur.
 * `volume` is a linear multiplier in [0, 1], with at most 6 decimal places.
 * The mixer does not normalize or
 * change any gain: clipping is possible and requires separate review.
 * No untrusted text is interpolated in the filter graph.
 */
function buildAudioArgs(plan, assets, durationMs) {
  objectWithKeys(plan, ['mode', 'tracks']);
  const duration = millis(durationMs);
  if (duration === 0 || !(assets instanceof Map) || !Array.isArray(plan.tracks)) invalid();
  if (plan.mode === 'silent') {
    if (plan.tracks.length !== 0) invalid();
    return { inputs: [], filter: null, mapArgs: ['-map', '0:v:0', '-an'] };
  }
  if (plan.mode !== 'mix' || plan.tracks.length < 1 || plan.tracks.length > MAX_TRACKS) invalid();
  const inputs = [];
  const filters = [];
  for (const [i, track] of plan.tracks.entries()) {
    objectWithKeys(track, ['asset_id', 'offset_ms', 'trim_end_ms', 'trim_start_ms', 'volume']);
    if (typeof track.asset_id !== 'string' || !ID.test(track.asset_id)) invalid();
    const assetPath = assets.get(track.asset_id);
    if (typeof assetPath !== 'string' || !path.isAbsolute(assetPath) || assetPath.includes('\0')) invalid();
    const start = millis(track.trim_start_ms);
    const end = millis(track.trim_end_ms);
    const offset = millis(track.offset_ms);
    if (end <= start || offset + end - start > duration || typeof track.volume !== 'number' ||
        !Number.isFinite(track.volume) || track.volume < 0 || track.volume > 1 ||
        !Number.isSafeInteger(track.volume * 1000000)) invalid();
    inputs.push('-protocol_whitelist', 'file,pipe', '-i', assetPath);
    // Fixed decimal conversion prevents filter syntax injection and defines the
    // precision explicitly; 0.08 and 0.1 are unchanged, as in the baseline.
    const gain = track.volume.toFixed(6).replace(/0+$/, '').replace(/\.$/, '') || '0';
    filters.push(`[${i + 1}:a]atrim=start=${seconds(start)}:duration=${seconds(end - start)},asetpts=PTS-STARTPTS,volume=${gain},adelay=${offset}:all=1[t${i}]`);
  }
  const filter = filters.join(';') + ';' + plan.tracks.map((_, i) => `[t${i}]`).join('') +
    `amix=inputs=${plan.tracks.length}:duration=longest:normalize=0,atrim=duration=${seconds(duration)}[a]`;
  return { inputs, filter, mapArgs: ['-map', '0:v:0', '-map', '[a]'] };
}
module.exports = { buildAudioArgs };
