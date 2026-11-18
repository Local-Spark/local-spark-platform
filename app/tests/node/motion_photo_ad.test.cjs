const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('app/assets/motion_repertoire/business-reel-v8/examples/photo-reel.js', 'utf8');
function setup(start=0,end=6000) {
  const context = {window:{}};
  vm.runInNewContext(source,context);
  const node = () => ({style:{}});
  const nodes = {photo:node(),outgoing:node(),brand:node(),lines:[node(),node()],closingPhotos:[node(),node()]};
  const timing = {start,end,textIn:start+100,textOut:start+2200,handoffStart:end-2500,handoffEnd:end-2000};
  return {make:context.window.makePhotoReelMotion,nodes,timing};
}
for (const [start,end] of [[0,6000],[2700,12100],[0,15000]]) {
  test(`v8 uses plan closing ${end-2000}..${end}, full-frame cover and an anchored logo`, () => {
    const {make,nodes,timing} = setup(start,end);
    const seek = make({...nodes,...timing});
    assert.equal(nodes.brand.style.width,'36%');
    assert.equal(nodes.brand.style.objectFit,'contain');
    assert.equal(nodes.photo.style.width,'100%');
    assert.equal(nodes.photo.style.height,'100%');
    assert.equal(nodes.photo.style.objectFit,'cover');
    let previous;
    for(let t=timing.handoffEnd;t<=end;t+=100) {
      seek(t);
      const state=[nodes.brand,...nodes.closingPhotos].map(n=>n.style.transform);
      if(previous) state.forEach((s,i)=>assert.notEqual(s,previous[i]));
      previous=state;
      assert.equal(nodes.brand.style.opacity,'1');
      assert.equal(nodes.outgoing.style.opacity,'0');
      nodes.closingPhotos.forEach(n=>assert.equal(n.style.objectFit,'cover'));
    }
    seek(end-900); const middle=JSON.stringify(nodes);
    seek(end); const last=JSON.stringify(nodes);
    seek(end+1000); assert.equal(JSON.stringify(nodes),last);
    seek(start); seek(end-900); assert.equal(JSON.stringify(nodes),middle);
    seek(start-1000); const first=JSON.stringify(nodes);
    seek(start); assert.equal(JSON.stringify(nodes),first);
    seek(start+800); const hold=nodes.photo.style.transform;
    seek(start+1500); assert.notEqual(nodes.photo.style.transform,hold);
  });
}
test('v8 rejects overlong reading and empty closing windows', () => {
  const {make,nodes,timing} = setup(0,10000);
  for(const update of [{textOut:3000},{handoffEnd:10000}]) {
    assert.throws(()=>make({...nodes,...timing,...update}),/ordered plan windows/);
  }
  assert.doesNotThrow(()=>make({...nodes,...timing,textOut:2950,handoffStart:7000,handoffEnd:7500}));
});

test('v8 permits a longer closing when it continues moving to end', () => {
  const {make,nodes,timing} = setup(0,15000);
  const seek=make({...nodes,...timing,handoffStart:9000,handoffEnd:10000});
  seek(10000); const first=nodes.brand.style.transform;
  seek(14000); const late=nodes.brand.style.transform;
  seek(15000); assert.notEqual(first,late); assert.notEqual(nodes.brand.style.transform,late);
});
