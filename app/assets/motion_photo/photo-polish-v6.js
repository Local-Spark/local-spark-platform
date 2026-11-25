function installPhotoPolish(plan) {
  const original = window.seek;
  const color = value => {
    const m = value.match(/^rgba?\(([^)]+)\)$/);
    return m ? m[1].split(',').map(Number) : [];
  };
  const visible = el => {
    const r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0 || r.right <= 0 || r.bottom <= 0 || r.left >= innerWidth || r.top >= innerHeight) return false;
    for (let n = el; n; n = n.parentElement) {
      const s = getComputedStyle(n);
      if (s.display === 'none' || s.visibility !== 'visible' || Number(s.opacity) === 0) return false;
    }
    return true;
  };
  const shadow = value => {
    const parts = value.split(/,(?![^()]*\))/);
    if (parts.length !== 1) return false;
    let blurred = false;
    for (const part of parts) {
      const m = part.trim().match(/^rgb\(0,\s*0,\s*0\) (-?[\d.]+)px (-?[\d.]+)px ([\d.]+)px$/);
      if (!m || Math.abs(Number(m[1])) > 2 || Math.abs(Number(m[2])) > 2 || Number(m[3]) > 4) return false;
      blurred ||= Number(m[3]) >= 2;
    }
    return blurred;
  };
  // U1 applies even when another backing would satisfy the legacy T2 check.
  const restrained = (el, text) => {
    const s = getComputedStyle(el), r = el.getBoundingClientRect(), t = text.getBoundingClientRect();
    const bg = color(s.backgroundColor);
    const painted = s.backgroundImage !== 'none' || (bg[3] ?? 1) > 0;
    if (s.textShadow !== 'none' && !shadow(s.textShadow)) return false;
    if (s.boxShadow !== 'none' || s.filter !== 'none') return false;
    if (!painted) return true;
    // Solid local backing only: no radial pool, ellipse or gradient stacking.
    return s.backgroundImage === 'none' && bg.length >= 3 && bg.slice(0,3).every(v => v === 0) &&
      (bg[3] ?? 1) <= .8 && s.borderRadius === '0px' &&
      r.width < innerWidth*.95 && r.height < innerHeight*.4 &&
      r.left <= t.left && r.top <= t.top && r.right >= t.right && r.bottom >= t.bottom &&
      t.left-r.left <= 16 && t.top-r.top <= 16 && r.right-t.right <= 16 && r.bottom-t.bottom <= 16;
  };
  window.seek = async function(ms) {
    await original.call(window, ms);
    // Cover scenes still full-bleed; contain_blur (declared) may inset without failing V8.
    const layouts = plan.layouts || [];
    const activeLayout = layouts.filter(s => s.start <= ms && (ms < s.end || ms === plan.end && s.end === plan.end))
      .sort((a,b) => b.start-a.start)[0];
    const active = (plan.cover || []).filter(s => s.start <= ms && (ms < s.end || ms === plan.end && s.end === plan.end));
    const scene = active.sort((a,b) => b.start-a.start)[0];
    const contain = activeLayout && activeLayout.mode === 'contain_blur';
    if (!contain) {
      if (!scene) throw new Error('MOTION_PHOTO_FULL_BLEED_REQUIRED');
      const photos = document.querySelectorAll(`[id="${scene.id}"]`);
      const fills = r => r.left <= .01 && r.top <= .01 && r.right >= innerWidth-.01 && r.bottom >= innerHeight-.01;
      const photo = photos[0];
      if (photos.length !== 1 || photo.tagName !== 'IMG' || !photo.complete || !photo.naturalWidth ||
          getComputedStyle(photo).objectFit !== 'cover' || !fills(photo.getBoundingClientRect()))
        throw new Error('MOTION_PHOTO_FULL_BLEED_REQUIRED');
      for (let n=photo; n; n=n.parentElement) {
        const s=getComputedStyle(n);
        if (s.display==='none' || s.visibility!=='visible' || Number(s.opacity)<.95 ||
            s.filter!=='none' || s.maskImage!=='none' ||
            (s.clipPath!=='none' && !/^inset\(0(?:px|%)?(?: 0(?:px|%)?){0,3}\)$/.test(s.clipPath)) ||
            ((s.overflowX!=='visible' || s.overflowY!=='visible') && !fills(n.getBoundingClientRect())))
          throw new Error('MOTION_PHOTO_FULL_BLEED_REQUIRED');
      }
    }
    // Absolute seek check of declared primary N2 motion, including the middle.
    for (const b of plan.continuity || []) {
      if (ms < b.start || ms > b.end) continue;
      const nodes = document.querySelectorAll(`[id="${b.id}"]`);
      if (nodes.length !== 1) throw new Error('MOTION_PHOTO_CONTINUITY_NOT_EXECUTED');
      const el = nodes[0], p = (ms-b.start)/(b.end-b.start);
      const [scale,x,y] = b.a.map((a,i) => a+(b.z[i]-a)*p);
      const m = new DOMMatrixReadOnly(getComputedStyle(el).transform);
      if (!m.is2D || Math.abs(m.a-scale)>.00001 || Math.abs(m.d-scale)>.00001 ||
          Math.abs(m.b)>.00001 || Math.abs(m.c)>.00001 ||
          Math.abs(m.e-x*innerWidth/100)>.01 || Math.abs(m.f-y*innerHeight/100)>.01)
        throw new Error('MOTION_PHOTO_CONTINUITY_NOT_EXECUTED');
      for (let n=el.parentElement; n; n=n.parentElement) {
        if (!new DOMMatrixReadOnly(getComputedStyle(n).transform).isIdentity)
          throw new Error('MOTION_PHOTO_CONTINUITY_NOT_EXECUTED');
      }
    }
    const texts = plan.texts.flatMap(id => [...document.querySelectorAll(`[id="${id}"]`)]);
    const textNodes = new Set(texts.flatMap(el => [el, ...el.querySelectorAll('*')]).filter(el => el.textContent.trim()));
    for (const el of textNodes) {
      if (!visible(el)) continue;
      const s = getComputedStyle(el), c = color(s.color), r = el.getBoundingClientRect();
      for (let n = el; n && n !== document.body && n !== document.documentElement; n = n.parentElement) {
        if (!restrained(n, texts.find(t => t === el || t.contains(el)) || el)) throw new Error('MOTION_PHOTO_POLISH_STYLE_REQUIRED');
      }
      let scrim = false;
      for (let n = el; n; n = n.parentElement) {
        const bg = color(getComputedStyle(n).backgroundColor), b = n.getBoundingClientRect();
        scrim ||= b.width < innerWidth * .95 && b.left <= r.left && b.top <= r.top &&
          b.right >= r.right && b.bottom >= r.bottom && bg.length >= 3 &&
          bg.slice(0,3).every(v => v === 0) && (bg[3] ?? 1) >= .75;
      }
      if (!el.textContent.trim() || parseFloat(s.fontSize) < 24 || c.length < 3 ||
          c.slice(0,3).some(v => v < 220) || (c[3] ?? 1) < 1 || (!scrim && !shadow(s.textShadow)))
        throw new Error('MOTION_PHOTO_TEXT_READABILITY_REQUIRED');
    }
    const graphics = (plan.graphics || []).flatMap(id => [...document.querySelectorAll(`[id="${id}"]`)]);
    const allowed = [...texts, ...plan.images.flatMap(id => [...document.querySelectorAll(`[id="${id}"]`)]), ...graphics];
    // Declared graphic subtree may use SVG/canvas/hr/border/pseudo; undeclared residual still fails.
    const underGraphic = el => graphics.some(g => g === el || g.contains(el));
    // A sibling scrim is a local readability support, not a free decorative leaf.
    // Its exact ID binds it to a declared text; geometry and paint must also agree.
    const localScrim = el => {
      const text = texts.find(t => el.id === `${t.id}-scrim`);
      if (!text || !visible(text) || el.children.length || el.textContent.trim()) return false;
      const s = getComputedStyle(el), r = el.getBoundingClientRect(), t = text.getBoundingClientRect();
      if (r.width >= innerWidth*.95 || r.height >= innerHeight*.4 ||
          r.left > t.left || r.top > t.top || r.right < t.right || r.bottom < t.bottom ||
          s.boxShadow !== 'none' || s.filter !== 'none' || s.maskImage !== 'none' || s.clipPath !== 'none') return false;
      return restrained(el, text) && color(s.backgroundColor)[3] > 0;
    };
    for (const el of document.querySelectorAll('body *')) {
      if (!visible(el)) continue;
      if (underGraphic(el)) continue;
      const s = getComputedStyle(el);
      const border = ['Top','Right','Bottom','Left'].some(side => parseFloat(s[`border${side}Width`]) > 0 && s[`border${side}Style`] !== 'none');
      const pseudo = ['::before','::after'].some(p => {
        const ps = getComputedStyle(el,p);
        return ps.content !== 'none' && ps.content !== 'normal' && ps.display !== 'none';
      });
      if (border || (parseFloat(s.outlineWidth) > 0 && s.outlineStyle !== 'none') || pseudo ||
          ['svg','canvas','hr'].includes(el.tagName.toLowerCase()) ||
          (!allowed.some(a => a === el || a.contains(el) || el.contains(a)) && !localScrim(el)))
        throw new Error('MOTION_PHOTO_DECORATION_FORBIDDEN');
    }
  };
}
