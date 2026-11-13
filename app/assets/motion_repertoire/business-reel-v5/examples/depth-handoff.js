// Original platform example: outgoing material crosses the lens; destination settles behind it.
// Each node is supplied by the composition with authorized content, never external media.
window.makeDepthHandoff = ({outgoing, incoming, title, width, start, end, kit}) => {
  Object.assign(outgoing.style, {transformOrigin:'50% 55%', boxShadow:`0 24px 60px ${kit.foreground}44`});
  Object.assign(incoming.style, {transformOrigin:'50% 50%'});
  Object.assign(title.style, {fontFamily:kit.font, color:kit.foreground, transformOrigin:'0 100%'});
  return ms => {
    const p = MotionV1.progress(ms, start, end, {kind:'ease_in_out', parameters:[]});
    const q = MotionV1.progress(ms, start+(end-start)*.35, end, {kind:'ease_out', parameters:[]});
    outgoing.style.transform = `translateX(${-width * 1.6 * p}px) scale(${1 + .8*p}) rotate(${-8*p}deg)`;
    outgoing.style.opacity = p === 1 ? '0' : '1';
    incoming.style.transform = `translateX(${width * .18 * (1-p)}px) scale(${.86+.14*p})`;
    incoming.style.opacity = String(p);
    title.style.transform = `translateY(${(1-q)*45}px) rotate(${(1-q)*3}deg)`;
    title.style.opacity = String(q);
    // The destination contains new content; motion alone cannot supply it.
  };
};
