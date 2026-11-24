'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const filename=path.resolve('app/assets/motion_video/edit-v1.js');
const source=fs.readFileSync(filename,'utf8');
function fixture(){
 const plan=JSON.parse(fs.readFileSync('app/tests/fixtures/motion_video_edit.json','utf8')).motion_plan;
 const style={position:'absolute',left:'0px',top:'0px',width:'720px',height:'1280px',objectPosition:'50% 50%',transformOrigin:'360px 640px'};
 const matrix={is2D:true,a:1,d:1,b:0,c:0,e:0,f:0};
 const parent={style:{transform:'none'},parentElement:null};
 const video={style,currentTime:0,seeking:false,duration:6,parentElement:parent};
 video.rectOffset={left:0,top:0,width:0,height:0};
 video.getBoundingClientRect=()=>({left:720*(1-matrix.a)/2+matrix.e+video.rectOffset.left,
  top:1280*(1-matrix.d)/2+matrix.f+video.rectOffset.top,width:720*matrix.a+video.rectOffset.width,height:1280*matrix.d+video.rectOffset.height});
 const document={querySelectorAll:()=>[video]};
 const window={seek:async ms=>{
  const s=plan.scenes[ms<3000?0:1],e=s.video_layout.edit,p=(ms-s.start_ms)/3000;
  matrix.a=matrix.d=e.crop_from.scale+(e.crop_to.scale-e.crop_from.scale)*p;
  video.currentTime=Math.min(e.source_out_ms-1,e.source_in_ms+ms-s.start_ms)/1000;
 }};
 const context=vm.createContext({window,document,innerWidth:720,innerHeight:1280,getComputedStyle:n=>n.style,DOMMatrixReadOnly:function(){return matrix;}});
 vm.runInContext(source,context,{filename});
 const original=window.seek;context.installVideoEditV1(plan);
 return {window,video,style,matrix,document,parent,original};
}
test('EDL and crop match every synthetic frame, reverse seek and endpoints',async()=>{
 const f=fixture();for(let ms=0;ms<=6000;ms+=1000/30)await f.window.seek(ms);
 for(const ms of [6000,3000,2999,0,5999])await f.window.seek(ms);
});
test('rejects invalid time before model execution',async()=>{
 const f=fixture();for(const ms of [-1,6001,NaN,Infinity])await assert.rejects(f.window.seek(ms),/EDIT_NOT_EXECUTED/);
});
test('rejects missing/duplicate video, time drift, pending seeks, unsafe transforms and cancelled crop',async()=>{
 const changes=[
  f=>f.document.querySelectorAll=()=>[],f=>f.document.querySelectorAll=()=>[f.video,f.video],
  f=>f.video.seeking=true,f=>f.video.currentTime=NaN,f=>f.video.currentTime+=.01,f=>f.video.duration=2,f=>f.video.duration=NaN,
  f=>f.matrix.is2D=false,f=>f.matrix.a+=.02,f=>f.matrix.d+=.02,f=>f.matrix.b=.01,f=>f.matrix.c=.01,
  f=>f.matrix.e=3,f=>f.matrix.f=3,f=>f.style.position='relative',f=>f.style.left='1px',f=>f.style.top='1px',
  f=>f.style.width='719px',f=>f.style.height='1279px',f=>f.style.objectPosition='0% 0%',
  f=>f.style.transformOrigin='0px 0px',f=>f.video.rectOffset.left=1,f=>f.video.rectOffset.top=1,
  f=>f.video.rectOffset.width=1,f=>f.video.rectOffset.height=1,f=>f.parent.style.transform='scale(0.5)'
 ];
 for(const change of changes){
  const f=fixture();const old=f.original;
  // Install anew so the altered model result is checked, not repaired by guard.
  const context=vm.createContext({window:{seek:async ms=>{await old(ms);change(f);}},document:f.document,
   innerWidth:720,innerHeight:1280,getComputedStyle:n=>n.style,DOMMatrixReadOnly:function(){return f.matrix;}});
  vm.runInContext(source,context,{filename});
  context.installVideoEditV1(JSON.parse(fs.readFileSync('app/tests/fixtures/motion_video_edit.json','utf8')).motion_plan);
  await assert.rejects(context.window.seek(1000),/EDIT_NOT_EXECUTED/);
 }
});
test('accepts only bounded output-frame padding and clamps the final source seek',async()=>{
 const f=fixture();f.video.duration=5.98;
 const context=vm.createContext({window:{seek:async ms=>{await f.original(ms);f.video.currentTime=5.979;}},document:f.document,
  innerWidth:720,innerHeight:1280,getComputedStyle:n=>n.style,DOMMatrixReadOnly:function(){return f.matrix;}});
 vm.runInContext(source,context,{filename});
 context.installVideoEditV1(JSON.parse(fs.readFileSync('app/tests/fixtures/motion_video_edit.json','utf8')).motion_plan);
 await context.window.seek(6000);
 f.video.duration=5.965;
 await assert.rejects(context.window.seek(6000),/EDIT_NOT_EXECUTED/);
});
