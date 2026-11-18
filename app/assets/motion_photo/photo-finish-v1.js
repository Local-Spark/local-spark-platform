function installPhotoFinish(plan) {
  // Installed before the immutable v2 wrapper. Absolute seeks, no motion injection.
  const original = window.seek;
  window.seek = async function(ms) {
    await original.call(window, ms);
    for (const scene of plan.scenes) {
      if (ms < scene.start || ms > scene.end) continue;
      for (const id of scene.texts) {
        const el = document.querySelectorAll(`[id="${id}"]`)[0];
        for (let n=el; n; n=n.parentElement) {
          const s=getComputedStyle(n), r=n.getBoundingClientRect();
          const clear = s.backgroundColor==='transparent' || /^rgba\([^)]*,\s*0\)$/.test(s.backgroundColor);
          if (s.display!=='none' && s.visibility==='visible' && Number(s.opacity)>0 &&
              r.width >= innerWidth*.95 && r.height < innerHeight*.9 &&
              (!clear || s.backgroundImage!=='none'))
            throw new Error('MOTION_PHOTO_LOCAL_SCRIM_REQUIRED');
        }
      }
    }
    for (const b of plan.typography) {
      if (ms < b.start || ms > b.end) continue;
      const nodes = document.querySelectorAll(`[id="${b.id}"]`);
      if (nodes.length !== 1) throw new Error('MOTION_PHOTO_TYPOGRAPHY_NOT_EXECUTED');
      const el = nodes[0], p = (ms-b.start)/(b.end-b.start);
      for (let n=el; n; n=n.parentElement) {
        const s=getComputedStyle(n), r=n.getBoundingClientRect();
        if (s.display==='none' || s.visibility!=='visible' || Number(s.opacity)<.95 ||
            s.filter!=='none' || (s.clipPath!=='none' && !/^inset\(0(?:px|%)?(?: 0(?:px|%)?){0,3}\)$/.test(s.clipPath)) || s.maskImage!=='none' ||
            r.width<=1 || r.height<=1 || r.right<=0 || r.bottom<=0 || r.left>=innerWidth || r.top>=innerHeight ||
            (n!==el && !new DOMMatrixReadOnly(s.transform).isIdentity))
          throw new Error('MOTION_PHOTO_TYPOGRAPHY_NOT_EXECUTED');
      }
      const [scale,x,y]=b.a.map((a,i)=>a+(b.z[i]-a)*p);
      const m=new DOMMatrixReadOnly(getComputedStyle(el).transform);
      if (!el.textContent.trim() || !m.is2D || Math.abs(m.a-scale)>.00001 || Math.abs(m.d-scale)>.00001 ||
          Math.abs(m.b)>.00001 || Math.abs(m.c)>.00001 ||
          Math.abs(m.e-x*innerWidth/100)>.01 || Math.abs(m.f-y*innerHeight/100)>.01)
        throw new Error('MOTION_PHOTO_TYPOGRAPHY_NOT_EXECUTED');
    }
  };
}
