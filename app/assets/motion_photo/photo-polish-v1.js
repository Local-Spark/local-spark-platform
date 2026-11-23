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
    let blurred = false;
    for (const part of parts) {
      const m = part.trim().match(/^rgb\(0,\s*0,\s*0\) (-?[\d.]+)px (-?[\d.]+)px ([\d.]+)px$/);
      if (!m || Math.abs(Number(m[1])) > 4 || Math.abs(Number(m[2])) > 4) return false;
      blurred ||= Number(m[3]) >= 2;
    }
    return blurred;
  };
  window.seek = async function(ms) {
    await original.call(window, ms);
    const texts = plan.texts.flatMap(id => [...document.querySelectorAll(`[id="${id}"]`)]);
    const textNodes = new Set(texts.flatMap(el => [el, ...el.querySelectorAll('*')]).filter(el => el.textContent.trim()));
    for (const el of textNodes) {
      if (!visible(el)) continue;
      const s = getComputedStyle(el), c = color(s.color), r = el.getBoundingClientRect();
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
    const allowed = [...texts, ...plan.images.flatMap(id => [...document.querySelectorAll(`[id="${id}"]`)])];
    for (const el of document.querySelectorAll('body *')) {
      if (!visible(el)) continue;
      const s = getComputedStyle(el);
      const border = ['Top','Right','Bottom','Left'].some(side => parseFloat(s[`border${side}Width`]) > 0 && s[`border${side}Style`] !== 'none');
      const pseudo = ['::before','::after'].some(p => {
        const ps = getComputedStyle(el,p);
        return ps.content !== 'none' && ps.content !== 'normal' && ps.display !== 'none';
      });
      if (border || (parseFloat(s.outlineWidth) > 0 && s.outlineStyle !== 'none') || pseudo ||
          ['svg','canvas','hr'].includes(el.tagName.toLowerCase()) ||
          !allowed.some(a => a === el || a.contains(el) || el.contains(a)))
        throw new Error('MOTION_PHOTO_DECORATION_FORBIDDEN');
    }
  };
}
