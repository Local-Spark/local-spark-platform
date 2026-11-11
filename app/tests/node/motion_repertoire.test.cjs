'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '../../assets');
const pack = path.join(root, 'motion_repertoire/business-reel-v1');
const manifest = JSON.parse(fs.readFileSync(path.join(pack, 'manifest.json'), 'utf8'));
const kit = {background:'#eeeae0', foreground:'#20382a', accent:'#996a20', font:'Kit Font'};
function element() {
  return {style:{}, attrs:{}, children:[], setAttribute(k,v){this.attrs[k]=v;},
    appendChild(node){this.children.push(node);}, replaceChildren(...nodes){this.children=nodes;}};
}
function setup() {
  const context = {document:{createElement:element,createElementNS:element}};
  context.window = context;
  vm.runInNewContext(fs.readFileSync(path.join(root,'motion_html_renderer/movement-v1.js'),'utf8'), context);
  const catalog = fs.readFileSync(path.join(root,'motion_elements/v1/catalog.json'),'utf8');
  vm.runInNewContext(fs.readFileSync(path.join(root,'motion_elements/v1/runtime.js'),'utf8')
    .replace('__MOTION_ELEMENTS_CATALOG__',catalog), context);
  for (const example of manifest.examples) {
    vm.runInNewContext(fs.readFileSync(path.join(pack,example.file),'utf8'),context);
    assert.equal(typeof context[example.entrypoint], 'function');
  }
  return context;
}
test('DOM examples use provided kit/material and support repeated and reverse seeks', () => {
  const context=setup(), host=element(), typeHost=element();
  const evidence=context.makeLayeredEvidence({host,imageAssetId:'assets/authorized.png',label:'Detalhe confirmado',kit});
  const type=context.makeLayeredType({host:typeHost,lines:['Pausa','com cuidado'],kit});
  assert.equal(host.children[0].children[0].src,'assets/authorized.png');
  assert.equal(host.children[0].style.background,kit.background);
  const state=ms=>{evidence(ms);type(ms);return JSON.stringify([host,typeHost]);};
  const middle=state(800); state(4000); state(0);
  assert.equal(state(800),middle);
  assert.equal(state(800),middle);
  assert.notEqual(state(0),middle);
  assert.equal(state(4000),state(5000)); // Settled reading state.
});
test('Canvas route redraws deterministically with actual MotionV1, without rendering media', () => {
  const context=setup(), calls=[], values={};
  const g = new Proxy(values, {
    get(target,key){return target[key] || ((...args)=>calls.push([key,...args]));},
    set(target,key,value){calls.push([key,value]);target[key]=value;return true;}
  });
  const seek=context.makeRouteAction({canvas:{width:720,height:480,getContext:()=>g},labels:['Origem','Preparo','Entrega'],kit});
  const state=ms=>{calls.length=0;seek(ms);return JSON.stringify(calls);};
  const middle=state(1200);state(4000);state(0);
  assert.equal(state(1200),middle);
  assert.notEqual(state(0),middle);
  assert.equal(state(4000),state(5000));
  assert.ok(middle.includes('Entrega'));
  assert.ok(middle.includes(kit.accent));
});
