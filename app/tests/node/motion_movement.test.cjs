'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.resolve(__dirname, '../../assets/motion_html_renderer/movement-v1.js'), 'utf8');
function setup() {
  const elements = {title: {style: {}}, card: {style: {}}}, window = {};
  vm.runInNewContext(source, {window, document: {getElementById: id => elements[id]}});
  return {m: window.MotionV1, elements, window};
}
const beat = (start_ms, end_ms, to, curve = {kind:'linear', parameters:[]}) => ({start_ms,end_ms,to,curve});
const track = () => ({id:'title', initial:{x:0,opacity:0,clipRight:100}, beats:[
  beat(100,300,{x:80,opacity:1,clipRight:0}), beat(700,900,{x:160,opacity:0})]});

test('random access, repeat, reverse and holds produce the same complete visual state', () => {
  const {m,elements} = setup(), t=m.timeline([track()]);
  t.seek(200); const middle = {...elements.title.style};
  assert.equal(middle.opacity,'0.5'); assert.match(middle.transform,/translate\(40px/);
  assert.equal(middle.clipPath,'inset(0% 50% 0% 0%)');
  for (const ms of [500,1000,-1,200,200]) t.seek(ms);
  assert.deepEqual(elements.title.style,middle);
  t.seek(500); assert.equal(elements.title.style.opacity,'1');
  t.seek(-1); assert.equal(elements.title.style.opacity,'0');
  t.seek(1000); assert.match(elements.title.style.transform,/translate\(160px/);
});
test('coordinated tracks and stagger preserve identities and inputs', () => {
  const {m,elements}=setup(), a=track(), b={...track(),id:'card'}, original=JSON.stringify([a,b]);
  const t=m.timeline(m.stagger([a,b],100));
  t.seek(200); assert.equal(elements.title.style.opacity,'0.5'); assert.equal(elements.card.style.opacity,'0');
  t.seek(300); assert.equal(elements.card.style.opacity,'0.5');
  assert.equal(JSON.stringify([a,b]),original);
});
test('Bézier solves time on x; overshoot remains available for spatial motion', () => {
  const {m}=setup();
  assert.ok(Math.abs(m.progress(500,0,1000,{kind:'cubic_bezier',parameters:[0,0,1,1]})-.5)<1e-9);
  assert.ok(m.progress(500,0,1000,{kind:'cubic_bezier',parameters:[0,1.8,1,1.8]})>1);
  const easing={kind:'cubic_bezier',parameters:[0,0,0,1]};
  const t=Math.cbrt(.5), expected=3*(1-t)*t*t+t**3;
  assert.ok(Math.abs(m.progress(500,0,1000,easing)-expected)<1e-9);
});
test('named curves and spring damping regimes have continuous finite endpoints', () => {
  const {m}=setup();
  for (const spec of [{kind:'linear',parameters:[]},{kind:'ease_in',parameters:[]},
    {kind:'ease_out',parameters:[]},{kind:'ease_in_out',parameters:[]},
    ...[8,20,40].map(d=>({kind:'spring',parameters:[100,d,1]}))]) {
    assert.equal(m.progress(0,0,1000,spec),0); assert.equal(m.progress(1000,0,1000,spec),1);
    assert.ok(Math.abs(m.progress(999.999,0,1000,spec)-1)<.001);
    for (const ms of [100,250,500,750]) assert.ok(Number.isFinite(m.progress(ms,0,1000,spec)));
  }
  assert.ok(m.progress(250,0,1000,{kind:'ease_in',parameters:[]})<.25);
  assert.ok(m.progress(250,0,1000,{kind:'ease_out',parameters:[]})>.25);
  assert.equal(m.progress(500,0,1000,{kind:'ease_in_out',parameters:[]}),.5);
});
test('compiled timeline is independent of later mutations to direction data', () => {
  const {m,elements}=setup(), a=track();
  a.beats[0].curve={kind:'cubic_bezier',parameters:[0,0,1,1]};
  const t=m.timeline([a]); t.seek(200); const expected={...elements.title.style};
  a.beats[0].to.x=999; a.initial.x=888; a.beats[0].curve.parameters[1]=99;
  t.seek(200); assert.deepEqual(elements.title.style,expected);
});
test('masks and opacity clamp overshoot while translation and rotation retain it', () => {
  const {m,elements}=setup();
  const t=m.timeline([{id:'title',initial:{opacity:0,clipLeft:100},beats:[beat(0,1000,
    {x:100,opacity:1,clipLeft:0,rotate:90,radius:12},{kind:'cubic_bezier',parameters:[0,1.8,1,1.8]})]}]);
  t.seek(500); assert.equal(elements.title.style.opacity,'1');
  assert.equal(elements.title.style.clipPath,'inset(0% 0% 0% 0%)');
  assert.ok(parseFloat(elements.title.style.borderRadius)>12);
});
test('invalid curves, nonfinite times, overlapping beats, missing and duplicate DOM IDs fail', () => {
  const {m}=setup();
  for (const spec of [null,{kind:'linear',parameters:[1]},{kind:'cubic_bezier',parameters:[2,0,1,1]},
    {kind:'spring',parameters:[1,0,1]},{kind:'spring',parameters:[1,NaN,1]}, {kind:'other',parameters:[]}]) {
    assert.throws(()=>m.progress(100,0,200,spec),/MOVEMENT_INVALID/);
  }
  for (const tracks of [[],[track(),track()],[{...track(),id:'missing'}],
    [{...track(),initial:{unknown:1}}],[{...track(),beats:[beat(0,300,{x:1}),beat(100,500,{x:2})]}],
    [{...track(),beats:[beat(100,100,{x:1})]}]]) assert.throws(()=>m.timeline(tracks),/MOVEMENT_INVALID/);
  assert.throws(()=>m.timeline([track()]).seek(NaN),/MOVEMENT_INVALID/);
  assert.throws(()=>m.stagger([track()],-1),/MOVEMENT_INVALID/);
});
test('public runtime cannot be replaced and needs no scheduler or network globals', () => {
  const {m,window}=setup();
  assert.equal(m.version,'motion-movement-v1'); assert.ok(Object.isFrozen(m));
  assert.throws(()=>{window.MotionV1={};},TypeError);
});
