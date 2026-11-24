// Original VR3 example: absolute linear typography, no source/audio manipulation.
function videoTextSeek(element, beats, ms) {
  const beat = beats.find(b => b.start_ms <= ms && ms <= b.end_ms);
  if (!beat) { element.style.opacity = '0'; return; }
  const a = JSON.parse(beat.start_state), z = JSON.parse(beat.end_state);
  const p = (ms - beat.start_ms) / (beat.end_ms - beat.start_ms);
  const value = key => a[key] + (z[key] - a[key]) * p;
  element.style.transform = `translate(${value('x')}px, ${value('y')}px)`;
  element.style.opacity = String(value('opacity'));
}
