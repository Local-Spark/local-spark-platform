function installVideoCapabilitiesV2(plan) {
  const original = window.seek;
  const fail = () => { throw new Error('MOTION_VIDEO_LAYER_NOT_EXECUTED'); };
  const owned = new Map();
  const viewport = document.createElement('div');
  viewport.id = 'video-c-viewport';
  if (document.getElementById(viewport.id)) fail();
  document.body.append(viewport);
  for (const scene of plan.scenes) for (const layer of scene.video_layout.design.layers) {
    const e = scene.elements.find(e => e.id === layer.element_id);
    if (document.getElementById(e.id)) fail();
    const el = document.createElement(e.role === 'image' ? 'img' : 'div');
    el.id = e.id;
    if (e.role === 'image') el.src = e.asset_id;
    document.body.append(el);
    owned.set(e.id, el);
  }
  const radius = shape => shape === 'ellipse' ? '50%' : shape === 'rounded' ? '12px' : '0px';
  window.seek = async function(ms) {
    if (!Number.isFinite(ms) || ms < 0 || ms > plan.duration_ms) fail();
    for (const el of owned.values()) el.style.display = 'none';
    await original.call(window, ms);
    const scene = [...plan.scenes].reverse().find(s => s.start_ms <= ms);
    const layout = scene.video_layout, design = layout.design, edit = layout.edit, box = design.viewport;
    const videos = document.querySelectorAll('video');
    if (videos.length !== 1) fail();
    const video = videos[0];
    video.id = layout.video_element_id;
    if (video.parentElement !== viewport) viewport.append(video);
    Object.assign(viewport.style, {
      position: 'absolute', left: box.x * innerWidth + 'px', top: box.y * innerHeight + 'px',
      width: box.width * innerWidth + 'px', height: box.height * innerHeight + 'px', overflow: 'hidden', zIndex: '10',
      transform: 'none', opacity: '1', borderRadius: '0px'
    });
    const span = scene.end_ms - scene.start_ms;
    const srcSpan = edit.source_out_ms - edit.source_in_ms;
    const p = (ms - scene.start_ms) / span;
    const value = k => edit.crop_from[k] + (edit.crop_to[k] - edit.crop_from[k]) * p;
    let opacity = 1;
    if (edit.transition === 'dissolve' || edit.transition === 'fade') {
      const edge = Math.min(250, span / 4);
      const local = ms - scene.start_ms;
      if (local < edge) opacity = local / edge;
      if (local > span - edge) opacity = (span - local) / edge;
    }
    Object.assign(video.style, {
      position: 'absolute', left: '0px', top: '0px', width: '100%', height: '100%',
      objectFit: 'cover', objectPosition: '50% 50%', transformOrigin: '50% 50%', opacity: String(opacity),
      transform: `translate(${value('x') * box.width * innerWidth}px,${value('y') * box.height * innerHeight}px) scale(${value('scale')})`
    });
    const sourceMs = edit.source_in_ms + (ms - scene.start_ms) * srcSpan / span;
    const t = Math.min(video.duration * 1000 - 1, edit.source_out_ms - 1, sourceMs) / 1000;
    if (!Number.isFinite(t)) fail();
    if (Math.abs(video.currentTime - t) > .00001) await new Promise((resolve, reject) => {
      const timer = setTimeout(() => { video.removeEventListener('seeked', done); reject(new Error('MOTION_VIDEO_EDIT_NOT_EXECUTED')); }, 5000);
      function done() { clearTimeout(timer); resolve(); }
      video.addEventListener('seeked', done, { once: true });
      video.currentTime = t;
    });
    if (video.seeking || !Number.isFinite(video.currentTime) || Math.abs(video.currentTime - t) > .002) fail();
    for (const layer of design.layers) {
      const el = owned.get(layer.element_id), e = scene.elements.find(e => e.id === layer.element_id);
      const b = e.beats.find(b => b.start_ms <= ms && ms <= b.end_ms);
      if (!el.isConnected || document.querySelectorAll(`[id="${e.id}"]`).length !== 1 || !b) fail();
      if (e.role === 'graphic' && (el.children.length || el.textContent)) fail();
      if (e.role === 'image') {
        if (!new URL(el.src).pathname.endsWith('/' + e.asset_id)) fail();
        await el.decode();
      }
      const a = JSON.parse(b.start_state), z = JSON.parse(b.end_state), f = (ms - b.start_ms) / (b.end_ms - b.start_ms);
      const v = k => (a[k] ?? (k === 'scale' ? 1 : 0)) + ((z[k] ?? (k === 'scale' ? 1 : 0)) - (a[k] ?? (k === 'scale' ? 1 : 0))) * f;
      const r = layer.box, scale = v('scale');
      Object.assign(el.style, {
        display: 'block', position: 'absolute', left: r.x * innerWidth + 'px', top: r.y * innerHeight + 'px',
        width: r.width * innerWidth + 'px', height: r.height * innerHeight + 'px', zIndex: String(layer.z_index),
        borderRadius: radius(layer.shape), backgroundColor: layer.color, objectFit: 'cover',
        transform: `translate(${v('x')}px,${v('y')}px) scale(${scale})`, opacity: String(v('opacity')), pointerEvents: 'none'
      });
      const s = getComputedStyle(el), m = new DOMMatrixReadOnly(s.transform);
      if (s.display !== 'block' || s.visibility !== 'visible' || Math.abs(Number(s.opacity) - v('opacity')) > .001 ||
        Math.abs(m.e - v('x')) > .01 || Math.abs(m.f - v('y')) > .01 || Math.abs(m.a - scale) > .0001) fail();
    }
  };
}
