(function () {
  'use strict';
  const NS = 'http://www.w3.org/2000/svg';
  const catalog = __MOTION_ELEMENTS_CATALOG__;
  const entries = new Map(catalog.items.map(item => [item.id, item]));
  function mount(host, name, options = {}) {
    const item = entries.get(name);
    if (!host || !item) throw new Error('MOTION_ELEMENT_UNKNOWN');
    const color = options.color;
    if (typeof color !== 'string' || !/^#[a-f0-9]{6}$/i.test(color)) throw new Error('MOTION_ELEMENT_COLOR');
    const width = options.strokeWidth === undefined ? 1.5 : options.strokeWidth;
    if (!Number.isFinite(width) || width <= 0 || width > 4) throw new Error('MOTION_ELEMENT_STROKE');
    const svg = document.createElementNS(NS, 'svg');
    for (const [key, value] of Object.entries({viewBox:'0 0 24 26', width:'100%', height:'100%',
      fill:'none', stroke:color, 'stroke-width':String(width), 'stroke-linecap':'round', 'stroke-linejoin':'round'})) {
      svg.setAttribute(key, value);
    }
    const parts = {};
    for (const [key, d] of Object.entries(item.parts)) {
      const path = document.createElementNS(NS, 'path');
      path.setAttribute('d', d);
      path.setAttribute('data-part', key);
      path.setAttribute('pathLength', '1');
      svg.appendChild(path);
      parts[key] = path;
    }
    host.replaceChildren(svg);
    return {svg, parts};
  }
  // Deterministic draw-on: call with MotionV1.progress(ms, start, end, curve).
  function reveal(part, progress) {
    if (!part || !Number.isFinite(progress)) throw new Error('MOTION_ELEMENT_PROGRESS');
    part.style.strokeDasharray = '1';
    part.style.strokeDashoffset = String(1 - Math.max(0, Math.min(1, progress)));
  }
  function node(host, name, options = {}) {
    if (typeof options.label !== 'string' || options.label.length > 100 ||
        typeof options.font !== 'string' || !options.font.length ||
        !/^#[a-f0-9]{6}$/i.test(options.background || '')) throw new Error('MOTION_ELEMENT_NODE');
    const art = document.createElement('div');
    const text = document.createElement('div');
    const mounted = mount(art, name, options);
    Object.assign(art.style, {width:'100%', height:'75%', minHeight:'0'});
    Object.assign(text.style, {fontFamily:options.font, color:options.color,
      textAlign:'center', overflowWrap:'anywhere'});
    text.textContent = options.label;
    Object.assign(host.style, {background:options.background, display:'flex', flexDirection:'column'});
    host.replaceChildren(art, text);
    return {...mounted, art, label:text};
  }
  function connector(host, points, options = {}) {
    if (!host || !Array.isArray(points) || points.length < 2 || points.length > 12 ||
        points.some(p => !Array.isArray(p) || p.length !== 2 || p.some(n => !Number.isFinite(n))) ||
        !/^#[a-f0-9]{6}$/i.test(options.color || '')) throw new Error('MOTION_ELEMENT_CONNECTOR');
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('width', '100%'); svg.setAttribute('height', '100%');
    svg.style.overflow = 'visible';
    const path = document.createElementNS(NS, 'path');
    path.setAttribute('d', points.map((p, i) => `${i ? 'L' : 'M'}${p[0]} ${p[1]}`).join(' '));
    path.setAttribute('fill', 'none'); path.setAttribute('stroke', options.color);
    path.setAttribute('stroke-width', '2'); path.setAttribute('pathLength', '1');
    svg.appendChild(path); host.replaceChildren(svg);
    return {svg, parts:{line:path}};
  }
  window.MotionElementsV1 = Object.freeze({mount, reveal, node, connector});
}());
