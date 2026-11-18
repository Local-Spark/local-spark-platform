const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('app/assets/motion_repertoire/business-reel-v10/examples/photo-reel.js', 'utf8');
for (const offset of [0, 7000]) {
  test(`v10 energy during reading, closing and reverse seek at ${offset}`, () => {
    const context = {window:{}};
    vm.runInNewContext(source,context);
    const node = () => ({style:{}});
    const nodes = {photo:node(),outgoing:node(),brand:node(),lines:[node()],closingPhotos:[node()],cta:node()};
    const seek = context.window.makePhotoReelMotion({...nodes,start:offset,end:offset+6000,
      textIn:offset+100,textOut:offset+2300,handoffStart:offset+3200,handoffEnd:offset+4000});
    const scale = n => Number(n.style.transform.match(/scale\(([^)]+)\)/)[1]);
    seek(offset+700); const early = scale(nodes.photo);
    seek(offset+2700); assert.ok(scale(nodes.photo)-early >= .07);
    assert.equal(nodes.photo.style.objectFit,'cover');
    assert.equal(nodes.brand.style.width,'36%');
    seek(offset+4100); const photo = scale(nodes.closingPhotos[0]), logo = scale(nodes.brand);
    seek(offset+5900); assert.ok(scale(nodes.closingPhotos[0])-photo >= .07);
    assert.ok(scale(nodes.brand)>logo);
    const late = JSON.stringify(nodes);
    seek(offset+6000); seek(offset); seek(offset+5900);
    assert.equal(JSON.stringify(nodes),late);
    seek(offset+6000); const last=JSON.stringify(nodes);
    seek(offset+9000); assert.equal(JSON.stringify(nodes),last);
    assert.equal(nodes.brand.style.opacity,'1');
    assert.equal(nodes.cta.style.opacity,'1');
  });
}
test('v10 refuses to stretch a micro drift over the whole reel', () => {
  const context = {window:{}};
  vm.runInNewContext(source,context);
  const node = () => ({style:{}});
  const args = {photo:node(),outgoing:node(),brand:node(),lines:[node()],start:0,end:15000,
    textIn:100,textOut:2300,handoffStart:11000,handoffEnd:13000};
  assert.throws(()=>context.window.makePhotoReelMotion(args),/perceptible plan motion/);
  assert.throws(()=>context.window.makePhotoReelMotion({...args,scaleEnd:NaN}),/perceptible plan motion/);
});
