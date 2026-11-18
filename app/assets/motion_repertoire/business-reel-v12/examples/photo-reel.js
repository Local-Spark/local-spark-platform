// O1: instantiate for EVERY photo scene, including middle scenes; cover remains continuous.
// Crop exception is per scene, decided in the plan, never an automatic blur fallback.
// O3: brand wrapper is transparent; CTA remains readable over a local neutral scrim until end.
// N1–N3: crop feasibility first. Never use landscape + blur as the default.
// Use a local scrim, never a cream plate behind the logo.
// Adapt numerical endpoints to the approved plan; constrained crop requires a related animated overlay.
// Photo ad example: adapt in scene_init and call animatePhoto(ms) in absolute seek.
// Layout at 720x1280 (scale with output). All assets/text/colors come from the kit.
// <main style="position:relative;width:720px;height:1280px;overflow:hidden">
//   <div id="closing" style="position:absolute;inset:0;overflow:hidden">
//     <img id="closingPhoto" src="AUTHORIZED_PHOTO" style="object-position:50% 40%">
//   </div>
//   <div id="outgoing" style="position:absolute;inset:0;overflow:hidden">
//     <img id="photo" src="AUTHORIZED_PHOTO" style="object-position:50% 40%">
//   </div>
//   <div style="position:absolute;inset:0;background:linear-gradient(transparent,#0009);pointer-events:none"></div>
//   <div id="copy" style="position:absolute;left:8%;right:8%;bottom:22%;color:white">AUTHORIZED_COPY</div>
//   <div style="position:absolute;inset:0;display:grid;place-items:center;pointer-events:none">
//     <img id="brand" src="assets/logo.png" style="width:36%;height:auto;object-fit:contain">
//   </div>
//   <div id="cta" style="position:absolute;left:8%;right:8%;bottom:12%;color:white;text-shadow:0 2px 6px #000">AUTHORIZED_CTA</div>
// </main>
// Pass cta as its own node; keep it outside outgoing so the closing message survives the handoff.
// No cream card or inset photo as default. Protect the photo focal point and use a local
// scrim for contrast. Logo width 32–44%, oriented minimum 28%; compensate transparent
// asset padding from preview. Brand name is subordinate. No geometric/pixel gate here.
// The full-frame closing photo is a sibling of outgoing, never its child. Text and logo
// transforms have separate wrappers. Use authorized logo only when available; without
// one, brand may be the authorized brand name. This example never fabricates a logo.
// Timing parameters come from plan beats: handoffEnd < end; keep moving until end.
// Text fully enters before its <=2500ms reading interval; split long copy into real beats.
// Repeat/adapt for each planned idea with its absolute times; do not stretch one card
// over the entire reel. Helpers are not auto-injected; appearance still needs MP4 review.
window.makePhotoReelMotion = ({photo, outgoing, brand, lines, start, end,
  textIn, textOut, handoffStart, handoffEnd, panX = 1, panY = -1, scaleStart = 1.04, scaleEnd = 1.20, closingPhotos = [], cta = null}) => {
  if (!(start < end && start <= textIn && textIn + 350 + Math.max(0, lines.length - 1) * 90 < textOut &&
    textOut + 300 <= handoffStart && handoffStart < handoffEnd && handoffEnd < end &&
    textOut - (textIn + 350) <= 2500))
    throw new Error('Photo example requires ordered plan windows and a reading interval');
  const seconds = (handoffEnd-start)/1000;
  if (![scaleStart,scaleEnd,panX,panY].every(Number.isFinite) || Math.min(scaleStart,scaleEnd) <= 0 ||
    (Math.abs(scaleEnd-scaleStart) + 1e-9 < Math.max(.04,.02*seconds) &&
     2*Math.max(Math.min(1,Math.abs(panX)),Math.min(1,Math.abs(panY))) + 1e-9 < Math.max(2,seconds)))
    throw new Error('Photo example requires perceptible plan motion; shorten the idea or coordinate a crop-safe overlay');
  const progress = (ms, a, b) => Math.max(0, Math.min(1, (ms-a)/(b-a)));
  const smooth = p => p*p*(3-2*p);
  Object.assign(photo.style, {transformOrigin:'50% 50%', width:'100%', height:'100%', objectFit:'cover'});
  outgoing.style.transformOrigin = '50% 50%';
  Object.assign(brand.style, {transformOrigin:'50% 50%', width:'36%', height:'auto', objectFit:'contain'});
  return ms => {
    // Linear drift keeps moving throughout the hold; initial overscan must be checked against the essential region.
    // Use one helper per idea, not one 15s drift; numeric endpoints are plan inputs.
    const p = progress(ms, start, handoffEnd);
    const x = Math.max(-1, Math.min(1, panX));
    const y = Math.max(-1, Math.min(1, panY));
    photo.style.transform = `translate(${x*(2*p-1)}%, ${y*(2*p-1)}%) scale(${scaleStart+(scaleEnd-scaleStart)*p})`;
    const exit = smooth(progress(ms, textOut, textOut+300));
    lines.forEach((line,i) => {
      const enter = smooth(progress(ms,textIn+i*90,textIn+i*90+350));
      line.style.transform = `translateY(${24*(1-enter)-18*exit}px)`;
      line.style.opacity = String(enter*(1-exit));
    });
    const h = smooth(progress(ms,handoffStart,handoffEnd));
    outgoing.style.transform = `scale(${1-.12*h}) translateY(${-4*h}%)`;
    outgoing.style.opacity = String(1-h);
    const closing = progress(ms, handoffEnd, end);
    closingPhotos.forEach((image, i) => {
      Object.assign(image.style, {width:'100%', height:'100%', objectFit:'cover', transformOrigin:'50% 50%'});
      image.style.transform = `translate(${(i%2 ? -1 : 1)*closing}%, ${-closing}%) scale(${1.04+.08*closing})`;
    });
    brand.style.transform = `scale(${.92+.08*h+.025*closing}) translateY(${12*(1-h)}px)`;
    brand.style.opacity = String(h);
    if (cta) {
      cta.style.opacity = String(h);
      cta.style.transform = `translateY(${18*(1-h)}px)`;
    }
  };
};

// R2: instantiate once per planned numeric transform, for EVERY scene (middle included).
// No guessed crop. x/y are viewport percentages, not percentages of a small overlay.
window.makePhotoSceneMotion = ({photo, start, end, scaleStart, scaleEnd,
  xStart = 0, xEnd = 0, yStart = 0, yEnd = 0, fit = 'cover'}) => {
  if (![start,end,scaleStart,scaleEnd,xStart,xEnd,yStart,yEnd].every(Number.isFinite) ||
      end <= start || Math.min(scaleStart,scaleEnd) <= 0 || !['cover','contain'].includes(fit))
    throw new Error('Photo scene requires ordered times and approved numeric states');
  // Geometry is the implementer's responsibility: never silently change crop/window size.
  photo.style.objectFit = fit;
  photo.style.transformOrigin = '50% 50%';
  return ms => {
    const p = Math.max(0,Math.min(1,(ms-start)/(end-start)));
    const x = (xStart+(xEnd-xStart)*p)*innerWidth/100;
    const y = (yStart+(yEnd-yStart)*p)*innerHeight/100;
    photo.style.transform = `translate(${x}px, ${y}px) scale(${scaleStart+(scaleEnd-scaleStart)*p})`;
  };
};
// R3: brand ancestors must also be transparent; the DOM guard rejects a painted wrapper.
window.preparePhotoBrandOverlay = ({brand, wrapper, cta}) => {
  Object.assign(wrapper.style, {background:'none',border:'0',padding:'0',boxShadow:'none'});
  Object.assign(brand.style, {background:'none',border:'0',padding:'0',boxShadow:'none',
    width:'36%',height:'auto',objectFit:'contain'});
  Object.assign(cta.style, {color:'#fff',fontSize:'32px',textShadow:'0 2px 6px #000'});
};
