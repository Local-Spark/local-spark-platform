// Original platform example. One media clock; typography reveals the supplied image.
// Adapt dimensions, text and intervals to the plan. This is not an installed API.
window.makeTypePortal = ({host, media, label, kit, width, height, start, end}) => {
  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
  Object.assign(svg.style, {position:'absolute', inset:'0', width:'100%', height:'100%'});
  const defs = document.createElementNS(ns, 'defs');
  const mask = document.createElementNS(ns, 'mask');
  // Caller must give each host a unique id if several instances coexist.
  const id = `${host.id}-portal-mask`;
  mask.id = id;
  mask.setAttribute('maskUnits', 'userSpaceOnUse');
  mask.setAttribute('x', '0'); mask.setAttribute('y', '0');
  mask.setAttribute('width', width); mask.setAttribute('height', height);
  const rect = color => {
    const r = document.createElementNS(ns, 'rect');
    r.setAttribute('width', width); r.setAttribute('height', height); r.setAttribute('fill', color);
    return r;
  };
  mask.appendChild(rect('white'));
  const word = document.createElementNS(ns, 'text');
  word.textContent = label;
  word.setAttribute('x', width / 2); word.setAttribute('y', height / 2);
  word.setAttribute('text-anchor', 'middle'); word.setAttribute('dominant-baseline', 'central');
  word.setAttribute('fill', 'black');
  Object.assign(word.style, {fontFamily:kit.font, fontWeight:'900', fontSize:`${width * .25}px`});
  mask.appendChild(word);
  const opening = document.createElementNS(ns, 'circle');
  opening.setAttribute('cx', width / 2); opening.setAttribute('cy', height / 2);
  opening.setAttribute('fill', 'black'); mask.appendChild(opening);
  defs.appendChild(mask); svg.appendChild(defs);
  const matte = rect(kit.background); matte.setAttribute('mask', `url(#${id})`); svg.appendChild(matte);
  Object.assign(host.style, {position:'relative', overflow:'hidden'});
  Object.assign(media.style, {position:'absolute', inset:'0', width:'100%', height:'100%', objectFit:'contain'});
  host.appendChild(media); host.appendChild(svg);
  return ms => {
    const p = MotionV1.progress(ms, start, end, {kind:'ease_in_out', parameters:[]});
    opening.setAttribute('r', p * Math.hypot(width, height) / 2);
    word.setAttribute('transform', `translate(${width/2} ${height/2}) scale(${1+p*1.2}) translate(${-width/2} ${-height/2})`);
    // No currentTime, cloning or audio changes. Protect filmed action outside this interval.
  };
};
