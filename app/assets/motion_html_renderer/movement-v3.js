/* Immutable browser-only motion primitives. No clock, timers, network or mutable playhead. */
(() => {
  'use strict';
  const invalid = () => { throw new Error('MOTION_MOVEMENT_INVALID'); };
  const finite = value => typeof value === 'number' && Number.isFinite(value);
  const clamp = (value, low = 0, high = 1) => Math.max(low, Math.min(high, value));
  const defaults = Object.freeze({x: 0, y: 0, scaleX: 1, scaleY: 1, rotate: 0,
    opacity: 1, clipTop: 0, clipRight: 0, clipBottom: 0, clipLeft: 0, radius: 0});
  const linear = Object.freeze({kind: 'linear', parameters: Object.freeze([])});
  function interval(start, end) {
    if (!finite(start) || !finite(end) || start < 0 || end <= start || end > 60000) invalid();
  }
  function curve(spec = linear, duration = 1000) {
    if (!spec || !Array.isArray(spec.parameters) || !spec.parameters.every(finite)) invalid();
    const kind = spec.kind, p = [...spec.parameters];
    if (kind === 'cubic_bezier') {
      if (p.length !== 4 || p[0] < 0 || p[0] > 1 || p[2] < 0 || p[2] > 1) invalid();
      const cubic = (t, a, b) => 3 * (1-t)**2 * t * a + 3 * (1-t) * t*t * b + t**3;
      return x => {
        let low = 0, high = 1;
        for (let i = 0; i < 40; i++) {
          const mid = (low + high) / 2;
          if (cubic(mid, p[0], p[2]) < x) low = mid; else high = mid;
        }
        return cubic((low + high) / 2, p[1], p[3]);
      };
    }
    if (kind === 'spring') {
      if (p.length !== 3 || p.some(v => v <= 0)) invalid();
      const [stiffness, damping, mass] = p;
      const omega = Math.sqrt(stiffness / mass), zeta = damping / (2 * Math.sqrt(stiffness * mass));
      if (!finite(omega) || !finite(zeta)) invalid();
      const response = t => {
        if (Math.abs(zeta - 1) < 1e-7) return 1 - Math.exp(-omega*t) * (1 + omega*t);
        if (zeta < 1) {
          const w = omega * Math.sqrt(1-zeta*zeta);
          return 1 - Math.exp(-zeta*omega*t) * (Math.cos(w*t) + zeta*omega/w * Math.sin(w*t));
        }
        const root = Math.sqrt(zeta*zeta-1);
        const r1 = -omega / (zeta+root), r2 = -omega * (zeta+root);
        return 1 - (r2*Math.exp(r1*t) - r1*Math.exp(r2*t)) / (r2-r1);
      };
      const end = response(duration/1000);
      if (!finite(end)) invalid();
      // Finite-duration normalization avoids snapping to the target at the endpoint.
      return x => end < 1e-8 ? x : response(x*duration/1000)/end;
    }
    if (p.length) invalid();
    switch (kind) {
      case 'linear': return x => x;
      case 'ease_in': return x => x*x*x;
      case 'ease_out': return x => 1-(1-x)**3;
      case 'ease_in_out': return x => x < 0.5 ? 4*x*x*x : 1-(-2*x+2)**3/2;
      default: return invalid();
    }
  }
  function progress(ms, start, end, spec = linear) {
    interval(start, end);
    if (!finite(ms)) invalid();
    const easing = curve(spec, end-start);
    return ms <= start ? 0 : ms >= end ? 1 : easing((ms-start)/(end-start));
  }
  function state(base, patch) {
    if (!patch || typeof patch !== 'object' || Array.isArray(patch)) invalid();
    for (const [key, value] of Object.entries(patch)) {
      if (!Object.hasOwn(defaults, key) || !finite(value)) invalid();
    }
    return {...base, ...patch};
  }
  function stagger(tracks, step_ms) {
    if (!Array.isArray(tracks) || !finite(step_ms) || step_ms < 0) invalid();
    return tracks.map((track, index) => ({...track, beats: track.beats.map(beat => ({...beat,
      start_ms: beat.start_ms + index*step_ms, end_ms: beat.end_ms + index*step_ms}))}));
  }
  function timeline(tracks) {
    if (!Array.isArray(tracks) || tracks.length < 1 || tracks.length > 192) invalid();
    const ids = new Set();
    const compiled = tracks.map(track => {
      if (typeof track.id !== 'string' || !/^[a-zA-Z][a-zA-Z0-9_-]{0,63}$/.test(track.id) || ids.has(track.id)) invalid();
      ids.add(track.id);
      const element = document.getElementById(track.id);
      if (!element || !Array.isArray(track.beats) || track.beats.length < 1 || track.beats.length > 12) invalid();
      const initial = state(defaults, track.initial || {});
      let previous = initial, previousEnd = 0;
      const beats = track.beats.map(beat => {
        const start = beat.start_ms, end = beat.end_ms;
        interval(start, end);
        if (start < previousEnd) invalid();
        const from = previous, to = state(from, beat.to);
        const easing = curve(beat.curve, end-start);
        previous = to; previousEnd = end;
        return {start, end, from, to, easing};
      });
      const clips = ['clipTop', 'clipRight', 'clipBottom', 'clipLeft'];
      const ownsClip = [track.initial || {}, ...track.beats.map(beat => beat.to)]
        .some(patch => clips.some(key => Object.hasOwn(patch, key)));
      const ownsRadius = [track.initial || {}, ...track.beats.map(beat => beat.to)]
        .some(patch => Object.hasOwn(patch, 'radius'));
      return {element, initial, beats, ownsClip, ownsRadius};
    });
    return Object.freeze({seek(ms) {
      if (!finite(ms)) invalid();
      for (const {element, initial, beats, ownsClip, ownsRadius} of compiled) {
        let value = initial;
        for (const beat of beats) {
          if (ms < beat.start) break;
          if (ms >= beat.end) { value = beat.to; continue; }
          const p = ms === beat.start ? 0 : beat.easing((ms-beat.start)/(beat.end-beat.start));
          value = Object.fromEntries(Object.keys(defaults).map(key => [key, beat.from[key] + (beat.to[key]-beat.from[key])*p]));
          break;
        }
        const s = element.style;
        s.transform = `translate(${value.x}px, ${value.y}px) rotate(${value.rotate}deg) scale(${value.scaleX}, ${value.scaleY})`;
        s.opacity = String(clamp(value.opacity));
        if (ownsClip) s.clipPath = `inset(${clamp(value.clipTop, 0, 100)}% ${clamp(value.clipRight, 0, 100)}% ${clamp(value.clipBottom, 0, 100)}% ${clamp(value.clipLeft, 0, 100)}%)`;
        if (ownsRadius) s.borderRadius = `${Math.max(0, value.radius)}px`;
      }
    }});
  }
  Object.defineProperty(window, 'MotionV1', {value: Object.freeze({version: 'motion-movement-v3', progress, stagger, timeline}),
    writable: false, configurable: false});
})();
