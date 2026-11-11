'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
function setup(version='v3') {
  const node={style:{borderRadius:'24px',border:'2px solid #244739',clipPath:'circle(45%)'}},window={};
  vm.runInNewContext(fs.readFileSync(path.resolve(__dirname,`../../assets/motion_html_renderer/movement-${version}.js`),'utf8'),
    {window,document:{getElementById:()=>node}});
  return {node,m:window.MotionV1};
}
const beat=(to)=>({start_ms:100,end_ms:1000,to,curve:{kind:'linear',parameters:[]}});
test('v3 preserves authored CSS corners when a track only moves the frame',()=>{
  const {node,m}=setup();
  const t=m.timeline([{id:'frame',initial:{scaleX:0.9,scaleY:0.9},beats:[beat({scaleX:1,scaleY:1})]}]);
  for(const ms of [500,1100,0,500,500]){
    t.seek(ms);assert.equal(node.style.borderRadius,'24px');assert.equal(node.style.clipPath,'circle(45%)');
    assert.equal(node.style.border,'2px solid #244739');
  }
  assert.equal(m.version,'motion-movement-v3');
});
test('explicit radius includes zero and stays deterministic before, during and after beats',()=>{
  const {node,m}=setup();
  const t=m.timeline([{id:'frame',initial:{radius:24},beats:[beat({radius:0})]}]);
  t.seek(550);assert.equal(node.style.borderRadius,'12px');
  t.seek(1100);assert.equal(node.style.borderRadius,'0px');
  t.seek(0);assert.equal(node.style.borderRadius,'24px');
  t.seek(550);assert.equal(node.style.borderRadius,'12px');
  const delayed=m.timeline([{id:'frame',beats:[beat({radius:18})]}]);
  delayed.seek(0);assert.equal(node.style.borderRadius,'0px');
  delayed.seek(1000);assert.equal(node.style.borderRadius,'18px');
});
test('mask ownership remains independent of rounded frame styling',()=>{
  const {node,m}=setup();
  const t=m.timeline([{id:'frame',initial:{clipRight:100},beats:[beat({clipRight:0})]}]);
  t.seek(550);assert.equal(node.style.clipPath,'inset(0% 50% 0% 0%)');
  assert.equal(node.style.borderRadius,'24px');
});
test('historical v2 continues resetting unspecified radius to its original default',()=>{
  const {node,m}=setup('v2');m.timeline([{id:'frame',beats:[beat({x:5})]}]).seek(550);
  assert.equal(node.style.borderRadius,'0px');assert.equal(m.version,'motion-movement-v2');
});
