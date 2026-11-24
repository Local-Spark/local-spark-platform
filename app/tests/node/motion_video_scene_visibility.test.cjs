'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const filename=path.resolve('app/assets/motion_video/scene-visibility-v1.js');
const source=fs.readFileSync(filename,'utf8');
function fixture(){
 const plan={duration_ms:200,scenes:[
  {start_ms:0,end_ms:100,video_layout:{text_element_ids:['a']}},
  {start_ms:100,end_ms:200,video_layout:{text_element_ids:['b']}}
 ]};
 const elements={};
 for(const id of ['a','b']){
  const node={textContent:id};
  const parent={children:[node],textContent:id,style:{setProperty(k,v,p){this[k]=v;this.priority=p;}}};
  node.parentElement=parent;elements[id]=node;
 }
 const document={body:{},documentElement:{},querySelectorAll(selector){
  const id=selector.match(/id="(.+)"/)[1];return elements[id]?[elements[id]]:[];
 }};
 const calls=[];
 const window={async seek(ms){assert.equal(this,window);calls.push(ms);}};
 const context=vm.createContext({window,document});
 vm.runInContext(source,context,{filename});
 return {plan,elements,document,window,calls,install:()=>context.installVideoSceneVisibilityV1(plan)};
}
test('absolute active scene before/after awaited model seek, including reverse and final boundary',async()=>{
 const f=fixture();
 f.window.seek=async function(ms){
  assert.equal(this,f.window);
  assert.equal(f.elements[ms<100?'a':'b'].parentElement.style.display,'block');
  assert.equal(f.elements[ms<100?'b':'a'].parentElement.style.display,'none');
  await Promise.resolve();
  for(const node of Object.values(f.elements))node.parentElement.style.display='block';
 };
 f.install();
 for(const ms of [0,1,99,100,101,199,200,100,99,0]){
  await f.window.seek(ms);
  for(const id of ['a','b']){
   const style=f.elements[id].parentElement.style;
   assert.equal(style.display,(id==='a')===(ms<100)?'block':'none');
   assert.equal(style.priority,'important');
  }
 }
});
test('does not hide undeclared DOM or swallow model errors',async()=>{
 const f=fixture(),extra={style:{display:'block'}};
 f.elements.extra=extra;
 f.window.seek=async()=>{throw Error('MODEL_FAILURE');};f.install();
 await assert.rejects(f.window.seek(0),/MODEL_FAILURE/);
 assert.equal(extra.style.display,'block');
});
test('invalid time is rejected before model execution',async()=>{
 const f=fixture();f.install();
 for(const ms of [-1,201,NaN,Infinity])await assert.rejects(f.window.seek(ms),/MOTION_VIDEO_SCENE_SCOPE_INVALID/);
 assert.deepEqual(f.calls,[]);
});
test('missing seek, missing/duplicate nodes, shared or unsafe parents fail closed',async()=>{
 const absent=fixture();absent.window.seek=null;assert.throws(absent.install,/MOTION_VIDEO_SCENE_SCOPE_INVALID/);
 const changes=[
  f=>{delete f.elements.b;},
  f=>{f.document.querySelectorAll=()=>[f.elements.a,f.elements.a];},
  f=>{f.elements.b.parentElement=null;},
  f=>{f.elements.b.parentElement=f.document.body;},
  f=>{f.elements.b.parentElement=f.document.documentElement;},
  f=>{f.elements.b.parentElement.children.push({});},
  f=>{f.elements.b.parentElement.textContent+=' unrelated text';},
  f=>{f.plan.scenes[1].video_layout.text_element_ids=['a'];}
 ];
 for(const change of changes){const f=fixture();change(f);f.install();await assert.rejects(f.window.seek(0),/MOTION_VIDEO_SCENE_SCOPE_INVALID/);}
});
test('re-resolves ownership after model DOM mutation',async()=>{
 const f=fixture();f.window.seek=async()=>{delete f.elements.b;};f.install();
 await assert.rejects(f.window.seek(0),/MOTION_VIDEO_SCENE_SCOPE_INVALID/);
});
