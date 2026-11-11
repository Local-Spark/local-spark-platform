'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '../../assets/motion_elements/v1');
const catalog = JSON.parse(fs.readFileSync(path.join(root, 'catalog.json'), 'utf8'));
const source = fs.readFileSync(path.join(root, 'runtime.js'), 'utf8').replace('__MOTION_ELEMENTS_CATALOG__', JSON.stringify(catalog));
function el() { return {style:{}, attrs:{}, children:[], setAttribute(k,v){this.attrs[k]=v;}, appendChild(n){this.children.push(n);}, replaceChildren(...n){this.children=n;}}; }
function runtime() {
  const ctx = {window:{}, document:{createElement:el, createElementNS:el}};
  vm.runInNewContext(source, ctx);
  return ctx.window.MotionElementsV1;
}
test('every component produces independent parts with kit color and deterministic backward seek', () => {
  const lib = runtime();
  for (const item of catalog.items) {
    const host = el();
    const {svg, parts} = lib.mount(host, item.id, {color:'#123456'});
    assert.equal(svg.attrs.stroke, '#123456');
    assert.deepEqual(Object.keys(parts), Object.keys(item.parts));
    for (const part of Object.values(parts)) {
      lib.reveal(part, 1); assert.equal(part.style.strokeDashoffset, '0');
      lib.reveal(part, 0); assert.equal(part.style.strokeDashoffset, '1');
      lib.reveal(part, .4); assert.equal(part.style.strokeDashoffset, '0.6');
    }
  }
});
test('diagrams use text labels safely and animated connectors', () => {
  const lib = runtime(), host = el();
  const node = lib.node(host, 'cup', {color:'#123456',background:'#eeeeee',font:'Kit Font',label:'<b>tempo</b>'});
  assert.equal(node.label.textContent, '<b>tempo</b>');
  assert.equal(node.label.style.fontFamily, 'Kit Font');
  const link = lib.connector(el(), [[10,20],[30,20],[30,40]], {color:'#123456'});
  assert.equal(link.parts.line.attrs.d, 'M10 20 L30 20 L30 40');
  lib.reveal(link.parts.line, .5);
  assert.equal(link.parts.line.style.strokeDashoffset, '0.5');
});
test('invalid declarations fail without fetching or generating a replacement', () => {
  const lib = runtime();
  assert.throws(() => lib.mount(el(),'unknown',{color:'#123456'}), /UNKNOWN/);
  assert.throws(() => lib.mount(el(),'cup',{color:'red'}), /COLOR/);
  assert.throws(() => lib.mount(el(),'cup',{color:'#123456',strokeWidth:0}), /STROKE/);
  assert.throws(() => lib.reveal(el(), NaN), /PROGRESS/);
  assert.throws(() => lib.node(el(),'cup',{}), /NODE/);
  assert.throws(() => lib.connector(el(),[[0,NaN],[1,2]],{color:'#123456'}), /CONNECTOR/);
});
