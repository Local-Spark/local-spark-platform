// Original photo example. Copy/adapt into scene_init, instantiate once with plan times,
// then call animatePhoto(ms) from seek(ms). No timers, media clock, IO or generated objects.
// Example markup (only when logo exists): <img id="brand" src="assets/logo.png" style="object-fit:contain">
// Closing photos remain visible in their own clipped wrappers, outside outgoing:
// <div class="closing-photo"><img class="closing-image" src="AUTHORIZED_PHOTO"></div>
// Use full-bleed 9:16 cover with protected focal point, overlays with contrast.
// Keep reading beats <= ~2–2.5s; adapt timing to the validated plan, not fixed templates.
// photo is inside a clipped viewport inside outgoing; lines are separate text wrappers.
// Use authorized assets, object-fit:cover and a protected focal point selected from the photo.
window.makePhotoReelMotion = ({photo, outgoing, brand, lines, start, end,
  textIn, textOut, handoffStart, handoffEnd, panX = 1, panY = -1, closingPhotos = []}) => {
  if (!(start < end && start <= textIn && textIn + 350 + Math.max(0, lines.length - 1) * 90 < textOut &&
    textOut + 300 <= handoffStart && handoffStart < handoffEnd && handoffEnd < end))
    throw new Error('Photo example requires ordered plan windows and a reading interval');
  const progress = (ms, a, b) => Math.max(0, Math.min(1, (ms-a)/(b-a)));
  const smooth = p => p*p*(3-2*p);
  Object.assign(photo.style, {transformOrigin:'50% 50%', width:'100%', height:'100%', objectFit:'cover'});
  outgoing.style.transformOrigin = '50% 50%';
  brand.style.transformOrigin = '50% 50%';
  return ms => {
    // Linear drift keeps moving throughout the hold; initial overscan contains <=1% pan.
    const p = progress(ms, start, end);
    const x = Math.max(-1, Math.min(1, panX));
    const y = Math.max(-1, Math.min(1, panY));
    photo.style.transform = `translate(${x*(2*p-1)}%, ${y*(2*p-1)}%) scale(${1.04+.08*p})`;
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
  };
};
