function installPhotoGuard(plan) {
  // Service-owned v9 contract. Computed DOM only: no pixel sampling, IO or animation injection.
  const original = window.seek;
  const fail = code => { throw new Error(code); };
  if (typeof original !== 'function') fail('MOTION_PHOTO_SEEK_REQUIRED');
  const css = node => getComputedStyle(node);
  const node = id => {
    const matches = document.querySelectorAll(`[id="${id}"]`);
    if (matches.length !== 1) fail('MOTION_PHOTO_DOM_BINDING_REQUIRED');
    return matches[0];
  };
  const ancestors = el => {
    const result = [];
    for (let n = el; n; n = n.parentElement) result.push(n);
    return result;
  };
  const rect = el => el.getBoundingClientRect();
  const visible = el => {
    const r = rect(el);
    return r.width > 1 && r.height > 1 && r.right > 0 && r.bottom > 0 &&
      r.left < innerWidth && r.top < innerHeight && ancestors(el).every(n => {
        const s = css(n);
        return s.display !== 'none' && s.visibility === 'visible' && Number(s.opacity) >= .95 &&
          s.filter === 'none' && s.clipPath === 'none' && s.maskImage === 'none';
      });
  };
  const image = (id, asset) => {
    const el = node(id);
    if (el.tagName !== 'IMG' || el.getAttribute('src') !== asset || !el.complete || !el.naturalWidth)
      fail('MOTION_PHOTO_DOM_ASSET_REQUIRED');
    return el;
  };
  const fills = r => r.left <= 1 && r.top <= 1 && r.right >= innerWidth-1 && r.bottom >= innerHeight-1;
  const inside = r => r.left >= 0 && r.top >= 0 && r.right <= innerWidth && r.bottom <= innerHeight;
  const transparent = value => value === 'transparent' || /^rgba\([^)]*,\s*0\)$/.test(value);
  const unpainted = s => transparent(s.backgroundColor) && s.backgroundImage === 'none' &&
    s.boxShadow === 'none' && ['Top','Right','Bottom','Left'].every(side =>
      parseFloat(s[`border${side}Width`]) === 0 && parseFloat(s[`padding${side}`]) === 0);
  const overlay = el => {
    for (const n of ancestors(el)) {
      if (!unpainted(css(n))) fail('MOTION_PHOTO_BRAND_PLATE_FORBIDDEN');
      for (const pseudo of ['::before','::after']) {
        const s = getComputedStyle(n, pseudo);
        if (s.content !== 'none' && s.content !== 'normal' && s.display !== 'none')
          fail('MOTION_PHOTO_BRAND_PLATE_FORBIDDEN');
      }
    }
  };
  const matchesMotion = (beat, ms) => {
    const el = node(beat.id);
    if (!visible(el) || ancestors(el).slice(1).some(n => {
      const t = css(n).transform;
      return t !== 'none' && !new DOMMatrixReadOnly(t).isIdentity;
    })) return false;
    const p = Math.max(0, Math.min(1, (ms-beat.start)/(beat.end-beat.start)));
    const [scale, x, y] = beat.a.map((a,i) => a+(beat.z[i]-a)*p);
    const m = new DOMMatrixReadOnly(css(el).transform);
    const close = (a,b) => Math.abs(a-b) <= .001;
    return m.is2D && close(m.a,scale) && close(m.d,scale) && close(m.b,0) && close(m.c,0) &&
      Math.abs(m.e-x*innerWidth/100) <= .1 && Math.abs(m.f-y*innerHeight/100) <= .1;
  };
  const check = ms => {
    if (!Number.isFinite(ms) || ms < 0 || ms > plan.end) fail('MOTION_PHOTO_TIME_INVALID');
    if (Math.abs(innerWidth/innerHeight-9/16) > .001) fail('MOTION_PHOTO_FRAME_REQUIRED');
    for (const scene of plan.scenes) {
      if (ms < scene.start_ms || ms >= scene.end_ms && !(ms === plan.end && scene.end_ms === plan.end)) continue;
      if (scene.photo_layout) {
        const layout = scene.photo_layout;
        const primary = scene.elements.find(e => e.id === layout.primary_element_id);
        const el = image(primary.id, primary.asset_id);
        if (!visible(el)) fail('MOTION_PHOTO_VISIBLE_REQUIRED');
        if (layout.mode === 'cover') {
          if (css(el).objectFit !== 'cover' || !fills(rect(el)) || ancestors(el).some(n => {
            const s = css(n);
            return (s.overflowX !== 'visible' || s.overflowY !== 'visible') && !fills(rect(n));
          })) fail('MOTION_PHOTO_COVER_REQUIRED');
        } else if (css(el).objectFit !== 'contain') fail('MOTION_PHOTO_LAYOUT_CHANGED');
      }
      const active = scene.energy.filter(b => b.start <= ms && ms < b.end);
      if (active.length && !active.some(b => matchesMotion(b,ms))) fail('MOTION_PHOTO_ENERGY_NOT_EXECUTED');
      if (scene.photo_closing && ms >= plan.handoff_end) {
        for (const b of scene.closing_motion.filter(b => b.start <= ms && (ms < b.end || ms === plan.end))) {
          if (!matchesMotion(b,ms)) fail('MOTION_PHOTO_CLOSING_MOTION_NOT_EXECUTED');
          const e = scene.elements.find(e => e.id === b.id);
          image(e.id,e.asset_id);
        }
        const closing = scene.photo_closing;
        for (const logo of scene.elements.filter(e => e.asset_id === 'assets/logo.png')) {
          const brand = image(logo.id, 'assets/logo.png');
          overlay(brand);
          if (!inside(rect(brand)) || css(brand).objectFit !== 'contain') fail('MOTION_PHOTO_BRAND_LAYOUT_REQUIRED');
        }
        const cta = node(closing.cta_element_id), s = css(cta);
        if (!visible(cta) || !inside(rect(cta)) || !cta.textContent.trim() ||
            parseFloat(s.fontSize) < innerWidth/30 || s.color !== 'rgb(255, 255, 255)' ||
            !/^rgb\(0, 0, 0\) -?[\d.]+px -?[\d.]+px (?:[2-9]|[1-9]\d+)(?:\.\d+)?px$/.test(s.textShadow)) fail('MOTION_PHOTO_CTA_READABILITY_REQUIRED');
      }
    }
  };
  // The producer cannot replace the guarded entrypoint on a later seek.
  Object.defineProperty(window, 'seek', {configurable:false, writable:false, value:async ms => {
    await original.call(window, ms);
    check(ms);
  }});
}
