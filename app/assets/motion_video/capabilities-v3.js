function installVideoCapabilitiesV3(plan) {
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
    let el;
    if (e.role === 'image') {
      el = document.createElement('img');
      el.src = e.asset_id;
    } else {
      el = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      el.setAttribute('viewBox', '0 0 100 100');
      el.setAttribute('preserveAspectRatio', 'none');
      const mark = document.createElementNS('http://www.w3.org/2000/svg', layer.shape === 'ellipse' ? 'ellipse' : 'rect');
      if (layer.shape === 'ellipse') {
        mark.setAttribute('cx', '50'); mark.setAttribute('cy', '50');
        mark.setAttribute('rx', '50'); mark.setAttribute('ry', '50');
      } else {
        mark.setAttribute('x', '0'); mark.setAttribute('y', layer.shape === 'bar' ? '35' : '0');
        mark.setAttribute('width', '100'); mark.setAttribute('height', layer.shape === 'bar' ? '30' : '100');
        if (layer.shape === 'rounded') mark.setAttribute('rx', '12');
      }
      mark.setAttribute('fill', layer.color);
      el.appendChild(mark);
    }
    el.id = e.id;
    document.body.append(el);
    owned.set(e.id, el);
  }
  const radius = shape => shape === 'ellipse' ? '50%' : shape === 'rounded' ? '12px' : '0px';
  const coverAt = (design, scene, ms) => design.layers.some(layer => {
    if (Math.abs(layer.box.x) > 1e-9 || Math.abs(layer.box.y) > 1e-9 || Math.abs(layer.box.width - 1) > 1e-9 || Math.abs(layer.box.height - 1) > 1e-9) return false;
    const e = scene.elements.find(el => el.id === layer.element_id);
    const b = e.beats.find(beat => beat.start_ms <= ms && ms <= beat.end_ms);
    if (!b) return false;
    const a = JSON.parse(b.start_state), z = JSON.parse(b.end_state), f = (ms - b.start_ms) / (b.end_ms - b.start_ms || 1);
    const opacity = (a.opacity ?? 0) + ((z.opacity ?? 0) - (a.opacity ?? 0)) * f;
    return opacity >= .95 && layer.z_index < 10;
  });
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
    const handoff = edit.transition === 'dissolve' || edit.transition === 'fade';
    if (handoff) {
      const edge = Math.min(500, span / 4);
      const local = ms - scene.start_ms;
      if (local < edge) opacity = local / edge;
      if (local > span - edge) opacity = (span - local) / edge;
      if (opacity < .99 && !coverAt(design, scene, ms)) fail();
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
      if (e.role === 'graphic') {
        if (el.tagName.toLowerCase() !== 'svg' || el.children.length < 1 || el.textContent.trim()) fail();
        const mark = el.children[0];
        mark.setAttribute('fill', layer.color);
      }
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
        borderRadius: e.role === 'graphic' ? '0px' : radius(layer.shape), backgroundColor: e.role === 'graphic' ? 'transparent' : layer.color,
        objectFit: 'cover', overflow: 'visible',
        transform: `translate(${v('x')}px,${v('y')}px) scale(${scale})`, opacity: String(v('opacity')), pointerEvents: 'none'
      });
      const s = getComputedStyle(el), m = new DOMMatrixReadOnly(s.transform);
      if (s.display !== 'block' || s.visibility !== 'visible' || Math.abs(Number(s.opacity) - v('opacity')) > .001 ||
        Math.abs(m.e - v('x')) > .01 || Math.abs(m.f - v('y')) > .01 || Math.abs(m.a - scale) > .0001) fail();
    }
  };
}
