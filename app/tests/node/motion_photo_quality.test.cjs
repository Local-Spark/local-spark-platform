const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
test('v7 closing photos and logo move through 11–15s with deterministic reverse seeks', () => {
  const context = {window:{}};
  vm.runInNewContext(fs.readFileSync('app/assets/motion_repertoire/business-reel-v7/examples/photo-reel.js','utf8'),context);
  const node=()=>({style:{}});
  const nodes={photo:node(), outgoing:node(), brand:node(), lines:[node()], closingPhotos:[node(),node()]};
  const seek=context.window.makePhotoReelMotion({...nodes,start:0,end:15000,textIn:500,textOut:2400,
    handoffStart:10000,handoffEnd:11000});
  let previous;
  for(let t=11000;t<=15000;t+=250) {
    seek(t);
    const state=[nodes.brand,...nodes.closingPhotos].map(n=>n.style.transform);
    if(previous) state.forEach((s,i)=>assert.notEqual(s,previous[i]));
    assert.equal(nodes.brand.style.opacity,'1');
    previous=state;
  }
  seek(13500); const mid=JSON.stringify(nodes);
  seek(15000); seek(0); seek(13500); assert.equal(JSON.stringify(nodes),mid);
  seek(15000); const end=JSON.stringify(nodes); seek(20000); assert.equal(JSON.stringify(nodes),end);
  seek(-100); const start=JSON.stringify(nodes); seek(0); assert.equal(JSON.stringify(nodes),start);
  assert.throws(()=>context.window.makePhotoReelMotion({...nodes,start:0,end:15000,textIn:500,textOut:2400,
    handoffStart:10000,handoffEnd:15000}),/ordered plan windows/);
});
