/** Declared SVG accent for video layers — adapt; runtime owns the node for role=graphic. */
function videoSvgAccentSeek(el, ms, start, end, from, to) {
  if (!el || el.tagName.toLowerCase() !== 'svg' || !el.children.length) return;
  const span = Math.max(1, end - start);
  const p = Math.min(1, Math.max(0, (ms - start) / span));
  const mix = (a, b) => a + (b - a) * p;
  const x = mix(from.x, to.x), y = mix(from.y, to.y), o = mix(from.opacity, to.opacity);
  const s = mix(from.scale ?? 1, to.scale ?? 1);
  el.style.transform = `translate(${x}px,${y}px) scale(${s})`;
  el.style.opacity = String(o);
}
