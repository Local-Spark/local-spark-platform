'use strict';

// Production audio argument builder; adapted from the qualified local evaluation helper. Asset paths MUST already have been verified by hash
// and their audio streams/durations inspected by the trusted caller. A trim end
// past EOF yields a shorter event, as FFmpeg does; the caller must disclose it.
// This does not
// certify audio rights, speech semantics, loudness or perceptual quality.
const path = require('node:path');
const ID = /^assets\/[A-Za-z0-9_.-]{1,80}$/;
const MAX_MS = 60000;
const MAX_TRACKS = 16;

function invalid() { throw new Error('invalid motion audio plan'); }
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
  return (ms / 1000).toFixed(3).replace(/0+$/, '').replace(/\.$/, '');
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
  if (plan && plan.version === 'motion-audio-v2') return buildAudioV2(plan, assets, durationMs);
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
    const gain = track.volume.toFixed(6).replace(/0+$/, '').replace(/\.$/, '');
    filters.push(`[${i + 1}:a]atrim=start=${seconds(start)}:duration=${seconds(end - start)},asetpts=PTS-STARTPTS,volume=${gain},adelay=${offset}:all=1[t${i}]`);
  }
  const filter = filters.join(';') + ';' + plan.tracks.map((_, i) => `[t${i}]`).join('') +
    `amix=inputs=${plan.tracks.length}:duration=longest:normalize=0,atrim=duration=${seconds(duration)}[a]`;
  return { inputs, filter, mapArgs: ['-map', '0:v:0', '-map', '[a]'] };
}

// V2 is an explicitly authorized mix. The source branch is never ducked,
// trimmed differently, gain-adjusted or duplicated; only music is compressed.
function buildAudioV2(plan, assets, durationMs) {
  objectWithKeys(plan, ['ducking', 'mode', 'tracks', 'version']);
  if (plan.mode !== 'mix' || !Array.isArray(plan.tracks) || !plan.tracks.length) invalid();
  const raw = [];
  for (const track of plan.tracks) {
    objectWithKeys(track, ['asset_id', 'fade_in_ms', 'fade_out_ms', 'offset_ms', 'role', 'trim_end_ms', 'trim_start_ms', 'volume']);
    if (!['original','music','effect'].includes(track.role)) invalid();
    const inMs = millis(track.fade_in_ms), outMs = millis(track.fade_out_ms);
    const start = millis(track.trim_start_ms), end = millis(track.trim_end_ms);
    if (end <= start || inMs + outMs > end - start) invalid();
    if (track.role === 'original') {
      if (track.asset_id !== 'assets/source.mp4' || start !== 0 || track.offset_ms !== 0 ||
          track.volume !== 1 || inMs !== 0 || outMs !== 0) invalid();
    } else if (track.asset_id === 'assets/source.mp4') invalid();
    raw.push({asset_id:track.asset_id, offset_ms:track.offset_ms, trim_start_ms:start, trim_end_ms:end, volume:track.volume});
  }
  const checked = buildAudioArgs({mode:'mix',tracks:raw}, assets, durationMs);
  const originals = plan.tracks.filter(track => track.role === 'original');
  if (originals.length > 1 || (originals.length === 1 && plan.tracks[0].role !== 'original')) invalid();
  const musicIndices = plan.tracks.flatMap((track, i) => track.role === 'music' ? [i] : []);
  if (plan.ducking !== null) {
    objectWithKeys(plan.ducking, ['attack_ms','ratio','release_ms','threshold']);
    const d = plan.ducking;
    if (originals.length !== 1 || !musicIndices.length || typeof d.threshold !== 'number' ||
        !Number.isFinite(d.threshold) || d.threshold < 0.00097563 || d.threshold > 1 ||
        typeof d.ratio !== 'number' || !Number.isFinite(d.ratio) || d.ratio < 1 || d.ratio > 20 ||
        !Number.isSafeInteger(d.attack_ms) || d.attack_ms < 1 || d.attack_ms > 2000 ||
        !Number.isSafeInteger(d.release_ms) || d.release_ms < 5 || d.release_ms > 9000) invalid();
  }
  const filters = [];
  for (const [i, track] of plan.tracks.entries()) {
    const duration = track.trim_end_ms - track.trim_start_ms;
    const gain = track.volume.toFixed(6).replace(/0+$/, '').replace(/\.$/, '');
    const fades = (track.fade_in_ms ? `,afade=t=in:st=0:d=${seconds(track.fade_in_ms)}` : '') +
      (track.fade_out_ms ? `,afade=t=out:st=${seconds(duration-track.fade_out_ms)}:d=${seconds(track.fade_out_ms)}` : '');
    filters.push(`[${i+1}:a]atrim=start=${seconds(track.trim_start_ms)}:duration=${seconds(duration)},asetpts=PTS-STARTPTS,volume=${gain}${fades},adelay=${track.offset_ms}:all=1[t${i}]`);
  }
  const labels = plan.tracks.map((_, i) => `t${i}`);
  if (plan.ducking !== null) {
    const channels = musicIndices.map((_, i) => `[key${i}]`).join('');
    filters.push(`[t0]asplit=${musicIndices.length+1}[voice]${channels}`);
    labels[0] = 'voice';
    for (const [index, trackIndex] of musicIndices.entries()) {
      const d = plan.ducking;
      filters.push(`[t${trackIndex}][key${index}]sidechaincompress=threshold=${d.threshold.toFixed(8)}:ratio=${d.ratio.toFixed(6)}:attack=${d.attack_ms}:release=${d.release_ms}[duck${index}]`);
      labels[trackIndex] = `duck${index}`;
    }
  }
  filters.push(labels.map(label => `[${label}]`).join('') +
    `amix=inputs=${labels.length}:duration=longest:normalize=0,atrim=duration=${seconds(durationMs)}[a]`);
  return {inputs:checked.inputs, filter:filters.join(';'), mapArgs:['-map','0:v:0','-map','[a]']};
}

function parseAudioMetrics(stderr) {
  if (typeof stderr !== 'string') invalid();
  const pos = stderr.lastIndexOf('Summary:');
  if (pos < 0) invalid();
  const summary = stderr.slice(pos);
  const integrated = summary.match(/Integrated loudness:\s*I:\s*(-?\d+(?:\.\d+)?)\s+LUFS/);
  const peak = summary.match(/Sample peak:\s*Peak:\s*(-?(?:\d+(?:\.\d+)?|inf))\s+dBFS/);
  if (!integrated || !peak) invalid();
  const loudness = Number(integrated[1]), peakDb = peak[1] === '-inf' ? null : Number(peak[1]);
  if (!Number.isFinite(loudness) || (peakDb !== null && !Number.isFinite(peakDb))) invalid();
  return {integrated_lufs:loudness, sample_peak_dbfs:peakDb, peak_kind:'sample', source:'decoded_output'};
}
module.exports = { buildAudioArgs, parseAudioMetrics };
