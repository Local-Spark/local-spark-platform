// Real browser, synthetic moving source, no client media or MP4 output.
const fs=require('node:fs'),assert=require('node:assert/strict'),{test}=require('node:test');
const {chromium}=require(process.env.MOTION_PLAYWRIGHT_PATH||'playwright');
const sources={
 scope:fs.readFileSync('app/assets/motion_video/scene-visibility-v1.js','utf8'),
 guard:fs.readFileSync('app/assets/motion_video/video-reel-v2.js','utf8'),
 runtime:fs.readFileSync('app/assets/motion_video/capabilities-v1.js','utf8'),
 edit:fs.readFileSync('app/assets/motion_video/edit-v1.js','utf8'),
 helper:fs.readFileSync('app/assets/motion_repertoire/business-video-reel-v3/examples/action-type.js','utf8'),
 editHelper:fs.readFileSync('app/assets/motion_repertoire/business-video-reel-v3/examples/edit.js','utf8'),
 scrim:fs.readFileSync('app/assets/motion_skills/instagram-reel-video-v20.md','utf8').split('```javascript\n')[1].split('```')[0]
};
const plan=JSON.parse(fs.readFileSync('app/tests/fixtures/motion_video_capabilities.json','utf8')).motion_plan;
test('C executes declared PIP/layers, source EDL, reverse seeks and rejects undeclared paint',{timeout:180000},async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.MOTION_CHROMIUM_PATH});
 try{
  const page=await browser.newPage({viewport:{width:720,height:1280}});
  const temp=fs.mkdtempSync(require('node:path').join(require('node:os').tmpdir(),'video-edit-test-'));
  let bytes;
  try {
   const file=require('node:path').join(temp,'synthetic.webm');
   require('node:child_process').execFileSync(process.env.FFMPEG_PATH||'ffmpeg',[
    '-hide_banner','-loglevel','error','-f','lavfi','-i','testsrc2=s=180x320:r=30:d=7','-an','-c:v','libvpx',file]);
   bytes=fs.readFileSync(file);
  } finally {fs.rmSync(temp,{recursive:true,force:true});}
  await page.route('**/*',async r=>{
   const p=new URL(r.request().url()).pathname;
   if(p==='/assets/source.mp4'){
    const range=r.request().headers().range;
    if(range){
     const m=/^bytes=(\d+)-(\d*)$/.exec(range),start=Number(m[1]),end=m[2]?Number(m[2]):bytes.length-1;
     return r.fulfill({status:206,contentType:'video/webm',headers:{'accept-ranges':'bytes','content-range':`bytes ${start}-${end}/${bytes.length}`},body:bytes.subarray(start,end+1)});
    }
    return r.fulfill({contentType:'video/webm',headers:{'accept-ranges':'bytes'},body:bytes});
   }
   if(p==='/assets/logo.png'||p==='/assets/support.png')return r.fulfill({contentType:'image/png',body:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j0XcAAAAASUVORK5CYII=','base64')});
   if(p==='/')return r.fulfill({contentType:'text/html',body:`<style>
body{margin:0}video{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
img{z-index:20;position:absolute;left:30px;top:50px;width:90px;height:50px}
.scrim{z-index:20;position:absolute;padding:12px} .text{font:32px sans-serif;color:white;white-space:nowrap}
</style><video id="recording0" src="assets/source.mp4" preload="auto" muted></video><img id="logo0" src="assets/logo.png">
<div class="scrim"><div class="text" id="cta0">Uma pausa</div></div>
<div class="scrim"><div class="text" id="cta1">Venha conhecer</div></div>`});
   return r.abort();
  });
  async function setup(temporal=false,foreground=false){
   const candidate=structuredClone(plan);
   if(foreground){
    const scene=candidate.scenes[1],layout=scene.video_layout;
    layout.mode='cover';layout.design.viewport={x:0,y:0,width:1,height:1};
    layout.design.layers[0].z_index=11;layout.design.layers[1].z_index=12;
    scene.elements.at(-2).role='image';scene.elements.at(-2).asset_id='assets/support.png';
   }
   await page.goto('https://motion.test/');
   await page.evaluate(async()=>{
    await Promise.all([...document.images].map(i=>i.decode()));
    const v=document.querySelector('video');if(v.readyState<2)await new Promise(r=>v.addEventListener('loadeddata',r,{once:true}));
   });
   await page.evaluate(({plan,sources})=>{
    for(const key of ['helper','editHelper','scrim'])(0,eval)(sources[key]);
    const v=document.querySelector('video'),logo=document.querySelector('img');
    window.seek=async ms=>{
     const s=plan.scenes[ms<3000?0:1];logo.id=s.video_layout.brand_element_id;
     await videoEditSeek(v,s,ms,720,1280);
     if(window.ignoreCrop)v.style.transform='none';
     if(window.wrongTime)await new Promise(resolve=>{v.addEventListener('seeked',resolve,{once:true});v.currentTime=0;});
     const e=s.elements.find(e=>e.role==='text'),node=document.getElementById(e.id);
     videoTextSeek(node,e.beats,ms);
     const m=new DOMMatrixReadOnly(getComputedStyle(node).transform);
     videoTextWithScrim(node,{x:m.e,y:m.f,opacity:Number(getComputedStyle(node).opacity)},112,362);
    };
    for(const key of ['scope','runtime','guard'])(0,eval)('('+sources[key]+')')(plan);
   },{plan:temporal ? {...plan,scenes:plan.scenes.map(s=>({...s,video_layout:{...s.video_layout,edit:{...s.video_layout.edit,source_in_ms:3000-s.start_ms,source_out_ms:6000-s.start_ms}}}))} : candidate,sources});
  }
  await setup();
  for(let i=0;i<=180;i++){
   try{await page.evaluate(ms=>window.seek(ms),i*1000/30);}catch(error){
    console.log('synthetic frame',i,await page.evaluate(()=>{const v=document.querySelector('video'),s=getComputedStyle(v);return {time:v.currentTime,seeking:v.seeking,duration:v.duration,width:s.width,height:s.height,left:s.left,top:s.top,position:s.position,origin:s.transformOrigin,object:s.objectPosition,matrix:s.transform};}));throw error;
   }
  }
  for(const ms of [6000,5999,3001,3000,2999,0,3000,0])await page.evaluate(ms=>window.seek(ms),ms);
  await page.evaluate(()=>window.seek(4000));
  const layer=await page.locator('#scene1-ribbon').boundingBox();
  assert.ok(layer.width>=288&&layer.y>=1024);
  await setup(true);
  for(const ms of [0,1000,2999,3000,4000,5999,6000,0])await page.evaluate(ms=>window.seek(ms),ms);
  await setup();
  await page.evaluate(()=>{const el=document.createElement('div');el.id='scene1-ribbon';document.body.append(el);});
  await assert.rejects(page.evaluate(()=>window.seek(3500)),/MOTION_VIDEO_LAYER_NOT_EXECUTED/);
  await setup();
  await page.evaluate(()=>{const st=document.createElement('style');st.textContent='#scene1-ribbon{opacity:0 !important}';document.head.append(st);});
  await assert.rejects(page.evaluate(()=>window.seek(3500)),/MOTION_VIDEO_LAYER_NOT_EXECUTED/);
  await setup();await page.evaluate(()=>document.getElementById('cta1').append(document.createElement('br')));
  await assert.rejects(page.evaluate(()=>window.seek(3500)),/MOTION_VIDEO_READABLE_ACTION_OVERLAY_REQUIRED/);
  await setup(false,true);
  for(const ms of [0,3000,4000,5999,0])await page.evaluate(ms=>window.seek(ms),ms);
  await setup();await page.evaluate(()=>{
   const p=document.createElement('div');p.style='position:absolute;left:400px;top:400px;width:3px;height:30px;background:orange';document.body.append(p);
  });
  await assert.rejects(page.evaluate(()=>window.seek(500)),/MOTION_VIDEO_UNPLANNED_OVERLAY/);
 }finally{await browser.close();}
});
