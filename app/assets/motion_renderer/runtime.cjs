'use strict';

// Internal code only: scene must come from compileScene; source IDs are resolved
// by a trusted, authenticated driver serving exactly /media/<UUID> locally.
function mountScene(doc, scene, seekMedia) {
  const root = doc.createElement('div');
  Object.assign(root.style, {
    position: 'relative', overflow: 'hidden', width: `${scene.width}px`, height: `${scene.height}px`,
    backgroundColor: scene.background,
  });
  const handles = [];
  for (const layer of scene.layers) {
    // The outer opacity is multiplied by the inner keyframed opacity by CSS.
    const envelope = doc.createElement('div');
    Object.assign(envelope.style, { position: 'absolute', inset: '0' });
    const wrapper = doc.createElement('div');
    Object.assign(wrapper.style, { position: 'absolute', overflow: 'hidden', transformOrigin: 'center center' });
    if (layer.kind === 'text') {
      wrapper.textContent = layer.text;
      Object.assign(wrapper.style, {
        color: layer.color, fontFamily: `"motion_${layer.font_id}"`, fontWeight: String(layer.weight),
        fontSize: `${scene.height * layer.font_size / 10000}px`, textAlign: layer.align,
        display: 'flex', alignItems: { top: 'flex-start', center: 'center', bottom: 'flex-end' }[layer.vertical_align],
        justifyContent: { left: 'flex-start', center: 'center', right: 'flex-end' }[layer.align],
        lineHeight: String(layer.line_height / 10000), letterSpacing: `${layer.letter_spacing / 10000}em`,
        whiteSpace: 'pre-wrap', overflowWrap: 'anywhere',
      });
    } else if (layer.kind === 'rectangle' || layer.kind === 'circle') {
      wrapper.style.backgroundColor = layer.color;
      if (layer.kind === 'circle') wrapper.style.borderRadius = '50%';
    } else {
      const media = doc.createElement(layer.kind === 'video' ? 'video' : 'img');
      media.src = `/media/${layer.source_id}`;
      if (layer.kind === 'video') { media.muted = true; media.playsInline = true; }
      Object.assign(media.style, {
        width: '100%', height: '100%', objectFit: layer.fit,
        objectPosition: `${layer.focus.x / 100}% ${layer.focus.y / 100}%`,
      });
      wrapper.appendChild(media);
    }
    envelope.appendChild(wrapper);
    root.appendChild(envelope);
    const duration = layer.end_ms - layer.start_ms;
    const fadeIn = layer.enter.duration_ms;
    const fadeOut = layer.exit.duration_ms;
    const points = [...new Set([0, fadeIn, duration - fadeOut, duration])].sort((a, b) => a - b);
    const fadeFrames = points.map(time => ({
      offset: time / duration,
      opacity: Math.min(fadeIn ? time / fadeIn : 1, fadeOut ? (duration - time) / fadeOut : 1, 1),
      easing: 'linear',
    }));
    const fadeAnimation = envelope.animate(fadeFrames, { duration, fill: 'both' });
    fadeAnimation.pause();
    const frames = layer.frames.map(frame => ({
      offset: frame.time_ms / duration,
      left: `${frame.x / 100}%`, top: `${frame.y / 100}%`,
      width: `${frame.width / 100}%`, height: `${frame.height / 100}%`,
      transform: `scale(${frame.scale / 10000}) rotate(${frame.rotation / 100}deg)`,
      opacity: frame.opacity / 10000,
      clipPath: `inset(${frame.clip.top / 100}% ${frame.clip.right / 100}% ${frame.clip.bottom / 100}% ${frame.clip.left / 100}%)`,
      easing: { linear: 'linear', ease_in: 'ease-in', ease_out: 'ease-out', ease_in_out: 'ease-in-out' }[frame.easing],
    }));
    const animation = wrapper.animate(frames, { duration, fill: 'both' });
    animation.pause();
    handles.push({ layer, envelope, wrapper, animation, fadeAnimation });
  }
  return {
    root,
    async seek(time) {
      if (!Number.isFinite(time) || time < 0 || time >= scene.duration_ms) throw new RangeError('outside page');
      for (const { layer, envelope, wrapper, animation, fadeAnimation } of handles) {
        const visible = time >= layer.start_ms && time < layer.end_ms;
        envelope.style.visibility = visible ? 'visible' : 'hidden';
        animation.currentTime = Math.min(layer.end_ms - layer.start_ms, Math.max(0, time - layer.start_ms));
        fadeAnimation.currentTime = animation.currentTime;
        if (visible && layer.kind === 'video') {
          await seekMedia(wrapper.firstChild, layer.trim_start_ms + time - layer.start_ms);
        }
      }
    },
  };
}

module.exports = { mountScene };
