'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
function setup(overrides = {}) {
  const context = {window:{}};
  vm.runInNewContext(fs.readFileSync(path.resolve(__dirname,
    '../../assets/motion_repertoire/business-reel-v6/examples/photo-reel.js'),'utf8'), context);
  const node = () => ({style:{}});
  const nodes = {photo:node(),outgoing:node(),brand:node(),lines:[node(),node(),node()]};
  const seek = context.window.makePhotoReelMotion({...nodes,start:0,end:15000,
    textIn:500,textOut:11500,handoffStart:12000,handoffEnd:14000,...overrides});
  return {...nodes,seek,state:ms => {seek(ms);return JSON.stringify(nodes);}};
}
test('long holds keep photo scale and pan moving while all text remains readable', () => {
  const c = setup();
  let previous;
  for(let ms=2800;ms<=11000;ms+=200) {
    c.seek(ms);
    assert.notEqual(c.photo.style.transform,previous);
    previous=c.photo.style.transform;
    for(const line of c.lines) {
      assert.equal(line.style.opacity,'1');
      assert.equal(line.style.transform,'translateY(0px)');
    }
    assert.equal(c.outgoing.style.opacity,'1');
    assert.equal(c.brand.style.opacity,'0');
  }
});
test('typography staggers spatially and exits before brand scale handoff', () => {
  const c=setup();c.seek(650);
  assert.notEqual(c.lines[0].style.transform,c.lines[1].style.transform);
  assert.ok(Number(c.lines[0].style.opacity)>Number(c.lines[1].style.opacity));
  c.seek(11600);assert.notEqual(c.lines[0].style.transform,'translateY(0px)');
  c.seek(12000);for(const l of c.lines) assert.equal(l.style.opacity,'0');
  c.seek(13000);
  assert.match(c.outgoing.style.transform,/scale\(0\.94\)/);
  assert.match(c.brand.style.transform,/scale\(0\.96/);
  c.seek(14000);assert.equal(c.brand.style.opacity,'1');assert.equal(c.outgoing.style.opacity,'0');
});
test('absolute seeks are deterministic, clamped and bounded for crop margin', () => {
  const c=setup({panX:99,panY:-99});
  const mid=c.state(7300);c.state(15000);c.state(-100);assert.equal(c.state(7300),mid);
  assert.equal(c.state(-100),c.state(0));assert.equal(c.state(15000),c.state(20000));
  c.seek(0);assert.equal(c.photo.style.transform,'translate(-1%, 1%) scale(1.04)');
  c.seek(15000);assert.equal(c.photo.style.transform,'translate(1%, -1%) scale(1.12)');
  const noLines=setup({lines:[]});assert.equal(noLines.state(20),noLines.state(20));
});
test('example refuses windows without reading time or with text crossing handoff', () => {
  for(const overrides of [{end:0},{textIn:-1},{textOut:800},{handoffStart:11600},
    {handoffEnd:11000},{handoffEnd:16000}]) assert.throws(()=>setup(overrides),/ordered plan windows/);
});
