const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {test} = require('node:test');
const source = fs.readFileSync(`app/assets/motion_photo/photo-guard-${process.env.PHOTO_GUARD_VERSION || 'v1'}.js`,'utf8');
const guardV2 = fs.readFileSync('app/assets/motion_photo/photo-guard-v2.js','utf8');
const helper = fs.readFileSync('app/assets/motion_repertoire/business-reel-v12/examples/photo-reel.js','utf8');
const box = (left=0,top=0,width=720,height=1280) => ({left,top,width,height,right:left+width,bottom:top+height});
const style = () => ({display:'block',visibility:'visible',opacity:'1',filter:'none',clipPath:'none',maskImage:'none',
  objectFit:'cover',overflowX:'visible',overflowY:'visible',backgroundColor:'rgba(0, 0, 0, 0)',backgroundImage:'none',
  boxShadow:'none',transform:'none',fontSize:'32px',color:'rgb(255, 255, 255)',textShadow:'rgb(0, 0, 0) 0px 2px 6px',
  ...Object.fromEntries(['Top','Right','Bottom','Left'].flatMap(s=>[[`border${s}Width`,'0px'],[`padding${s}`,'0px']]))});
class Matrix {
  constructor(value) {
    const nums = value === 'none' ? [1,0,0,1,0,0] : value.match(/-?[\d.]+/g).map(Number);
    [this.a,this.b,this.c,this.d,this.e,this.f] = nums;
    this.is2D = !value.startsWith('matrix3d');
    this.isIdentity = nums.join(',') === '1,0,0,1,0,0';
  }
}
function setup({ending=true, cover=true, guardSource=source}={}) {
  const root = {style:style(),parentElement:null,getBoundingClientRect:()=>box()};
  const nodes = {};
  const add = (id,tag,asset,r=box()) => nodes[id] = {tagName:tag,style:style(),parentElement:root,
    getBoundingClientRect:()=>r,getAttribute:()=>asset,complete:true,naturalWidth:100,textContent:'Veja o cardápio'};
  add('photo','IMG','assets/photo-one.png');
  add('brand','IMG','assets/logo.png',box(200,600,260,100)).style.objectFit='contain';
  add('cta','DIV',null,box(150,750,400,80));
  const beat = {id:'photo',start:0,end:5000,a:[1.04,0,0],z:[1.16,0,0]};
  const brandBeat = {...beat,id:'brand',a:[1,0,0],z:[1.025,0,0]};
  const plan = {end:5000,handoff_end:0,scenes:[{start_ms:0,end_ms:5000,
    photo_layout:{mode:cover?'cover':'contain_blur',primary_element_id:'photo'},
    elements:[{id:'photo',asset_id:'assets/photo-one.png'},{id:'brand',asset_id:'assets/logo.png'}],
    energy:[beat],closing_motion:[beat,brandBeat],
    ...(ending?{photo_closing:{brand_element_id:'brand',cta_element_id:'cta'}}:{})}]};
  if (!cover) nodes.photo.style.objectFit='contain';
  const original = ms => {
    if (nodes.photo) nodes.photo.style.transform=`matrix(${1.04+.12*ms/5000},0,0,${1.04+.12*ms/5000},0,0)`;
    nodes.brand.style.transform=`matrix(${1+.025*ms/5000},0,0,${1+.025*ms/5000},0,0)`;
  };
  const context = vm.createContext({window:{seek:original},innerWidth:720,innerHeight:1280,DOMMatrixReadOnly:Matrix,
    getComputedStyle:(n,pseudo)=>pseudo ? {...style(),content:n.pseudo??'none'} : n.style,
    document:{querySelectorAll:selector=> nodes[selector.slice(5,-2)] ? [nodes[selector.slice(5,-2)]] : []}});
  return {root,nodes,plan,context,original,install:()=>vm.runInContext(`(${guardSource})(${JSON.stringify(plan)})`,context)};
}
test('guard accepts cover, numeric motion, transparent logo and readable CTA across forward/reverse/end seeks', async()=>{
  const s=setup();
  s.context.window.seek=function(ms) { assert.equal(this,s.context.window);s.original(ms) };
  s.install();
  for(const ms of [0,2500,4999,5000,2500,0]) await s.context.window.seek(ms);
  assert.throws(()=>Object.defineProperty(s.context.window,'seek',{value:()=>{}}));
});
test('structured contain is honored; nonphoto scenes and no-brand closing are supported', async()=>{
  const s=setup({cover:false});s.plan.scenes[0].photo_closing.brand_element_id=null;s.install();
  await s.context.window.seek(2500);
  const other=setup({ending:false});delete other.plan.scenes[0].photo_layout;other.plan.scenes[0].energy=[];other.install();
  await other.context.window.seek(2000);
});
const mutations = [
  ['window layout',s=>s.nodes.photo.getBoundingClientRect=()=>box(0,400,720,480),'COVER_REQUIRED'],
  ['contain pretending cover',s=>s.nodes.photo.style.objectFit='contain','COVER_REQUIRED'],
  ['clipped ancestor',s=>{s.root.style.overflowY='hidden';s.root.getBoundingClientRect=()=>box(0,400,720,480)},'COVER_REQUIRED'],
  ['hidden photo',s=>s.nodes.photo.style.opacity='0','VISIBLE_REQUIRED'],
  ['blurred photo',s=>s.nodes.photo.style.filter='blur(4px)','VISIBLE_REQUIRED'],
  ['masked photo',s=>s.nodes.photo.style.maskImage='url(x)','VISIBLE_REQUIRED'],
  ['display none',s=>s.nodes.photo.style.display='none','VISIBLE_REQUIRED'],
  ['visibility hidden',s=>s.nodes.photo.style.visibility='hidden','VISIBLE_REQUIRED'],
  ['offscreen photo',s=>s.nodes.photo.getBoundingClientRect=()=>box(721,0),'VISIBLE_REQUIRED'],
  ['zero size photo',s=>s.nodes.photo.getBoundingClientRect=()=>box(0,0,0,0),'VISIBLE_REQUIRED'],
  ['missing id',s=>delete s.nodes.photo,'DOM_BINDING_REQUIRED'],
  ['wrong logo src',s=>s.nodes.brand.getAttribute=()=> 'assets/fake.png','DOM_ASSET_REQUIRED'],
  ['wrong image tag',s=>s.nodes.photo.tagName='DIV','DOM_ASSET_REQUIRED'],
  ['undecoded image',s=>s.nodes.photo.complete=false,'DOM_ASSET_REQUIRED'],
  ['broken image',s=>s.nodes.photo.naturalWidth=0,'DOM_ASSET_REQUIRED'],
  ['background cream',s=>s.nodes.brand.style.backgroundColor='rgb(255, 244, 220)','BRAND_PLATE_FORBIDDEN'],
  ['ancestral plate',s=>s.root.style.backgroundColor='rgb(255, 244, 220)','BRAND_PLATE_FORBIDDEN'],
  ['CSS image plate',s=>s.nodes.brand.style.backgroundImage='linear-gradient(white,white)','BRAND_PLATE_FORBIDDEN'],
  ['border',s=>s.nodes.brand.style.borderTopWidth='2px','BRAND_PLATE_FORBIDDEN'],
  ['padding',s=>s.nodes.brand.style.paddingLeft='20px','BRAND_PLATE_FORBIDDEN'],
  ['shadow',s=>s.nodes.brand.style.boxShadow='0 0 4px white','BRAND_PLATE_FORBIDDEN'],
  ['pseudo card',s=>s.root.pseudo='""','BRAND_PLATE_FORBIDDEN'],
  ['cropped logo',s=>s.nodes.brand.style.objectFit='cover','BRAND_LAYOUT_REQUIRED'],
  ['offscreen logo',s=>s.nodes.brand.getBoundingClientRect=()=>box(-1,0,260,100),'BRAND_LAYOUT_REQUIRED'],
  ['small CTA',s=>s.nodes.cta.style.fontSize='12px','CTA_READABILITY_REQUIRED'],
  ['hidden CTA',s=>s.nodes.cta.style.opacity='0','CTA_READABILITY_REQUIRED'],
  ['offscreen CTA',s=>s.nodes.cta.getBoundingClientRect=()=>box(-1,0,400,100),'CTA_READABILITY_REQUIRED'],
  ['empty CTA',s=>s.nodes.cta.textContent='  ','CTA_READABILITY_REQUIRED'],
  ['low contrast CTA',s=>s.nodes.cta.style.color='rgb(250, 240, 230)','CTA_READABILITY_REQUIRED'],
  ['no CTA shadow',s=>s.nodes.cta.style.textShadow='none','CTA_READABILITY_REQUIRED'],
  ['invisible CTA shadow',s=>s.nodes.cta.style.textShadow='rgb(0, 0, 0) 0px 0px 0px','CTA_READABILITY_REQUIRED'],
];
for (const [name,mutate,code] of mutations) test(`DOM rejects ${name}`,async()=>{
  const s=setup();mutate(s);s.install();await assert.rejects(s.context.window.seek(2500),new RegExp(code));
});
for(const [name,patch] of [
  ['no-op',s=>s.context.window.seek=()=>{}],
  ['parent cancellation',s=>s.root.style.transform='matrix(.9,0,0,.9,0,0)'],
  ['wrong pan',s=>s.context.window.seek=ms=>{s.original(ms);s.nodes.photo.style.transform='matrix(1.1,0,0,1.1,5,0)'}],
  ['wrong scale',s=>s.context.window.seek=ms=>{s.original(ms);s.nodes.photo.style.transform='matrix(1.001,0,0,1.001,0,0)'}],
  ['skew',s=>s.context.window.seek=ms=>{s.original(ms);s.nodes.photo.style.transform='matrix(1.1,1,0,1.1,0,0)'}],
]) test(`energy rejects ${name}`,async()=>{const s=setup();patch(s);s.install();await assert.rejects(s.context.window.seek(2500),/ENERGY_NOT_EXECUTED/)});
test('closing motion cannot stop early or hide behind the photo energy', async()=>{
  const s=setup();s.context.window.seek=ms=>{s.original(ms);s.nodes.brand.style.transform='none'};s.install();
  await assert.rejects(s.context.window.seek(4900),/CLOSING_MOTION_NOT_EXECUTED/);
});
test('related crop-safe overlay can execute energy without moving unsafe photo', async()=>{
  const s=setup({ending:false});s.plan.scenes[0].energy[0].id='cta';
  s.context.window.seek=ms=>{s.original(ms);s.nodes.cta.style.transform=s.nodes.photo.style.transform};s.install();
  await s.context.window.seek(2500);
});
test('end validates only final scene, and skips later scenes before they start', async()=>{
  const s=setup();const early=structuredClone(s.plan.scenes[0]);early.end_ms=1000;early.photo_layout.primary_element_id='missing';
  s.plan.scenes.unshift(early);s.plan.scenes.push({...early,start_ms:6000,end_ms:7000});s.install();await s.context.window.seek(5000);
});
test('invalid time, wrong frame and missing seek are rejected',async()=>{
  const s=setup();s.install();for(const ms of [-1,5001,NaN]) await assert.rejects(s.context.window.seek(ms),/TIME_INVALID/);
  s.context.innerWidth=1280;await assert.rejects(s.context.window.seek(0),/FRAME_REQUIRED/);
  const other=setup();delete other.context.window.seek;assert.throws(()=>other.install(),/SEEK_REQUIRED/);
});
test('layout cannot switch exception to cover; duplicate DOM ids fail closed',async()=>{
  const s=setup({cover:false});s.nodes.photo.style.objectFit='cover';s.install();await assert.rejects(s.context.window.seek(0),/LAYOUT_CHANGED/);
  const other=setup();other.context.document.querySelectorAll=()=>[other.nodes.photo,other.nodes.photo];other.install();
  await assert.rejects(other.context.window.seek(0),/DOM_BINDING_REQUIRED/);
});
test('v12 helper follows absolute endpoints and viewport pan on every scene',()=>{
  const ctx=vm.createContext({window:{},innerWidth:720,innerHeight:1280});vm.runInContext(helper,ctx);
  for(const start of [0,5000,10000]) {
    const photo={style:{}};const seek=ctx.window.makePhotoSceneMotion({photo,start,end:start+5000,scaleStart:1.04,scaleEnd:1.16,xStart:-1,xEnd:1});
    seek(start+2500);assert.equal(photo.style.transform,'translate(0px, 0px) scale(1.1)');
    seek(start+5000);assert.equal(photo.style.transform,'translate(7.2px, 0px) scale(1.16)');
    seek(start);assert.equal(photo.style.transform,'translate(-7.2px, 0px) scale(1.04)');
  }
  assert.throws(()=>ctx.window.makePhotoSceneMotion({photo:{style:{}},start:1,end:0,scaleStart:1,scaleEnd:1.1}),/ordered times/);
});

function handoff(guardSource=guardV2) {
  const s=setup({ending:false,guardSource});
  s.nodes.next={...s.nodes.photo,style:style(),parentElement:{...s.root,style:style()}};
  const first=s.plan.scenes[0];first.id='first';
  first.exit_handoff={start:1800,end:2200,next_scene_id:'second'};
  s.plan.scenes.push({...structuredClone(first),id:'second',start_ms:1800,exit_handoff:null,
    photo_layout:{mode:'cover',primary_element_id:'next'},elements:[{id:'next',asset_id:'assets/photo-one.png'}],
    energy:[{...first.energy[0],id:'next'}]});
  s.context.window.seek=ms=>{s.original(ms);s.nodes.next.style.transform=s.nodes.photo.style.transform};
  s.nodes.photo.style.opacity='.5';
  return s;
}
test('v2 accepts approved outgoing dissolve only while incoming photo carries layout and motion',async()=>{
  const s=handoff();s.install();await s.context.window.seek(2000);
  await assert.rejects(s.context.window.seek(2300),/VISIBLE_REQUIRED/);
  const old=handoff(fs.readFileSync('app/assets/motion_photo/photo-guard-v1.js','utf8'));old.install();
  await assert.rejects(old.context.window.seek(2000),/VISIBLE_REQUIRED/);
});
for (const [name,mutate,code] of [
  ['undeclared',s=>delete s.plan.scenes[0].exit_handoff,'VISIBLE_REQUIRED'],
  ['long',s=>s.plan.scenes[0].exit_handoff.end=2400,'VISIBLE_REQUIRED'],
  ['both faded',s=>s.nodes.next.style.opacity='.5','VISIBLE_REQUIRED'],
  ['next absent',s=>s.plan.scenes[0].exit_handoff.next_scene_id='missing','VISIBLE_REQUIRED'],
  ['next not photo',s=>delete s.plan.scenes[1].photo_layout,'VISIBLE_REQUIRED'],
  ['incoming window',s=>s.nodes.next.getBoundingClientRect=()=>box(0,400,720,480),'COVER_REQUIRED'],
  ['incoming static',s=>s.context.window.seek=ms=>s.original(ms),'ENERGY_NOT_EXECUTED'],
  ['masked outgoing',s=>s.nodes.photo.style.maskImage='url(x)','VISIBLE_REQUIRED'],
  ['no temporal overlap',s=>s.plan.scenes[1].start_ms=2100,'VISIBLE_REQUIRED'],
]) test(`v2 handoff rejects ${name}`,async()=>{const s=handoff();mutate(s);s.install();await assert.rejects(s.context.window.seek(2000),new RegExp(code))});
test('v2 waits for declared CTA entrance but enforces full readability through end',async()=>{
  const s=setup({guardSource:guardV2});s.plan.scenes[0].cta_read_start=3000;
  s.nodes.cta.style.clipPath='inset(100% 0% 0% 0%)';s.install();
  await s.context.window.seek(2500);
  await assert.rejects(s.context.window.seek(3000),/CTA_READABILITY_REQUIRED/);
  s.nodes.cta.style.clipPath='inset(0% 0% 0% 0%)';await s.context.window.seek(3000);await s.context.window.seek(5000);
  s.nodes.cta.style.opacity='0';await assert.rejects(s.context.window.seek(5000),/CTA_READABILITY_REQUIRED/);
});
test('v2 recognizes only geometrically empty inset as an open mask',async()=>{
  const s=setup({guardSource:guardV2});s.install();
  for(const value of ['inset(0px)','inset(0% 0%)','inset(0 0 0 0)']) {s.nodes.photo.style.clipPath=value;await s.context.window.seek(2000)}
  for(const value of ['inset(1px)','inset(0px 2px)','circle(50%)']) {
    s.nodes.photo.style.clipPath=value;await assert.rejects(s.context.window.seek(2000),/VISIBLE_REQUIRED/);
  }
});
