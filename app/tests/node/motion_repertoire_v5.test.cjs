'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
function element() {
  return {id:'',style:{},attrs:{},children:[],setAttribute(k,v){this.attrs[k]=v;},
    appendChild(node){this.children.push(node);}};
}
test('qualified mechanisms have deterministic reverse seeks without taking over the media clock', () => {
  const root=path.resolve(__dirname,'../../assets');
  const context={document:{createElementNS:element}};context.window=context;
  vm.runInNewContext(fs.readFileSync(path.join(root,'motion_html_renderer/movement-v3.js'),'utf8'),context);
  for(const name of ['type-portal','depth-handoff'])
    vm.runInNewContext(fs.readFileSync(path.join(root,`motion_repertoire/business-reel-v5/examples/${name}.js`),'utf8'),context);
  const host=element(), media=element(), next=element(), title=element();host.id='unique';
  Object.defineProperty(media,'currentTime',{set(){throw Error('Media clock overwritten');}});
  const kit={background:'#eee',foreground:'#222',font:'Own Kit'};
  const aperture=context.makeTypePortal({host,media,label:'VIEW',kit,width:720,height:1280,start:100,end:700});
  const pass=context.makeDepthHandoff({outgoing:host,incoming:next,title,width:720,start:700,end:1000,kit});
  function state(ms){aperture(ms);pass(ms);return JSON.stringify([host,next,title]);}
  const middle=state(800);state(1100);state(0);assert.equal(state(800),middle);
  assert.notEqual(state(0),middle);assert.equal(state(1000),state(2000));
  assert.equal(host.children[0],media);assert.equal(media.style.objectFit,'contain');
  assert.equal(host.children[1].children[0].children[0].id,'unique-portal-mask');
});
