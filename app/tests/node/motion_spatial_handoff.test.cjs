'use strict';
// Exercise the example transmitted by the product, with the real movement runtime and synthetic DOM.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.resolve(__dirname, '../../assets');
const source = fs.readFileSync(path.join(root, 'motion_skills/instagram-reel-v13.md'), 'utf8');
const examples = [...source.matchAll(/```javascript\n([\s\S]*?)\n```/g)].map(match => match[1]);
const handoff = examples.find(example => example.includes('function makeGroundedPassage'));
assert.ok(handoff);

const ids = {background:'background', recording:'recording', object:'object', shadow:'shadow', text:'text'};
const timing = {prepareStart:100, prepareEnd:600, handoffStart:800, handoffEnd:1200,
  revealStart:1400, revealEnd:2000, returnStart:3000, returnEnd:3600};
const geometry = {backgroundShift:-48, enterX:100, lift:36, startScale:0.9, shadowOpacity:0.25};

function setup() {
  const nodes = Object.fromEntries(Object.values(ids).map(id => [id, {style:{}, children:[]}]));
  const recording = {src:'assets/source.mp4', currentTime:1.25, paused:true};
  const object = {src:'assets/authorized.png'};
  nodes.recording.children.push(recording);
  nodes.object.children.push(object);
  Object.assign(nodes.recording.style, {borderRadius:'12px', border:'0px'});
  const context = {document:{getElementById:id => nodes[id]}};
  context.window = context;
  vm.runInNewContext(fs.readFileSync(path.join(root,'motion_html_renderer/movement-v3.js'),'utf8'),context);
  vm.runInNewContext(handoff,context);
  return {context, nodes, recording, object};
}

test('grounded passage coordinates preparation, reveal, rest and clean return deterministically', () => {
  const {context,nodes,recording,object} = setup();
  const result = context.makeGroundedPassage({ids,timing,geometry});
  const state = ms => {result.seek(ms); return JSON.stringify(nodes);};
  state(0);
  assert.equal(nodes.recording.style.opacity,'1');
  assert.equal(nodes.object.style.opacity,'0');
  assert.equal(nodes.shadow.style.opacity,'0');
  const prep = state(600);
  assert.match(nodes.background.style.transform,/translate\(-48px, 0px\)/);
  assert.equal(nodes.recording.style.opacity,'1');
  state(1200);
  assert.equal(nodes.recording.style.opacity,'0');
  const middle = state(1700);
  assert.match(nodes.object.style.transform,/translate\(50px, -18px\)/);
  assert.match(nodes.shadow.style.transform,/translate\(50px, 0px\)/);
  assert.equal(nodes.text.style.opacity,'0.5');
  const rest = state(2000);
  assert.equal(state(2800),rest);
  assert.match(nodes.object.style.transform,/translate\(0px, 0px\).*scale\(1, 1\)/);
  assert.equal(nodes.shadow.style.opacity,'0.25');
  assert.equal(nodes.text.style.opacity,'1');
  const end = state(3600);
  assert.equal(nodes.recording.style.opacity,'1');
  assert.equal(nodes.object.style.opacity,'0');
  assert.equal(nodes.shadow.style.opacity,'0');
  assert.equal(nodes.text.style.opacity,'0');
  assert.match(nodes.background.style.transform,/translate\(0px, 0px\)/);
  assert.equal(nodes.recording.style.clipPath,undefined);
  assert.equal(nodes.recording.style.borderRadius,'12px');
  assert.equal(nodes.recording.style.border,'0px');
  assert.equal(state(5000),end);
  assert.equal(state(1700),middle);
  assert.equal(state(1700),middle);
  assert.equal(state(600),prep);
  assert.equal(nodes.recording.children[0],recording);
  assert.deepEqual(recording,{src:'assets/source.mp4', currentTime:1.25, paused:true});
  assert.equal(nodes.object.children[0],object);
  const direct = setup();
  direct.context.makeGroundedPassage({ids,timing,geometry}).seek(1700);
  assert.equal(JSON.stringify(direct.nodes),middle);
  assert.equal(result.tracks.length,5);
});

test('invalid timing, duplicated layers and invalid geometry fail before changing DOM', () => {
  const {context,nodes} = setup();
  const before = JSON.stringify(nodes);
  for (const spec of [
    {ids:{...ids,shadow:'object'},timing,geometry},
    {ids:{...ids,object:'missing'},timing,geometry},
    {ids,timing:{...timing,revealStart:1100},geometry},
    {ids,timing:{...timing,returnEnd:60001},geometry},
    {ids,timing,geometry:{...geometry,lift:-1}},
    {ids,timing,geometry:{...geometry,startScale:0}},
    {ids,timing,geometry:{...geometry,shadowOpacity:2}},
    {ids,timing,geometry:{...geometry,backgroundShift:NaN}},
  ]) {
    assert.throws(()=>context.makeGroundedPassage(spec),/MOTION_GROUNDED_PASSAGE_INVALID/);
    assert.equal(JSON.stringify(nodes),before);
  }
});

test('same mechanism works for an authorized page without imposing a cup, mask or orbit', () => {
  const {context,nodes,object} = setup();
  object.src = 'assets/authorized-page.png';
  const pageGeometry = {...geometry, enterX:-120, lift:0, startScale:1, shadowOpacity:0.1};
  const passage = context.makeGroundedPassage({ids,timing,geometry:pageGeometry});
  passage.seek(1700);
  assert.match(nodes.object.style.transform,/translate\(-60px, 0px\)/);
  assert.match(nodes.shadow.style.transform,/translate\(-60px, 0px\)/);
  assert.equal(nodes.object.style.clipPath,undefined);
  passage.seek(3600);
  assert.equal(nodes.recording.style.opacity,'1');
  assert.equal(nodes.object.style.opacity,'0');
  assert.equal(object.src,'assets/authorized-page.png');
});
