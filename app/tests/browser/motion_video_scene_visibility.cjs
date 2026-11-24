// Synthetic two-scene reproduction of inactive scrims, no customer media or MP4.
const fs=require('node:fs'),assert=require('node:assert/strict'),{test}=require('node:test');
const {chromium}=require(process.env.MOTION_PLAYWRIGHT_PATH||'playwright');
const scope=fs.readFileSync('app/assets/motion_video/scene-visibility-v1.js','utf8');
const guard=fs.readFileSync('app/assets/motion_video/video-reel-v1.js','utf8');
const helper=fs.readFileSync('app/assets/motion_repertoire/business-video-reel-v2/examples/action-type.js','utf8');
const scrim=fs.readFileSync('app/assets/motion_skills/instagram-reel-video-v19.md','utf8').split('```javascript\n')[1].split('```')[0];
const template=JSON.parse(fs.readFileSync('app/tests/fixtures/motion_video_reel.json','utf8')).scenes[0].elements[2];
const plan={duration_ms:11200,scenes:[[0,6780,['title','body']],[6780,11200,['cta']]].map(([start,end,ids],i)=>({
 id:'scene'+i,start_ms:start,end_ms:end,video_layout:{video_element_id:'video'+i,brand_element_id:'logo'+i,text_element_ids:ids},
 elements:ids.map(id=>{const e=structuredClone(template);e.id=id;
  const spans=[[start,start+300],[start+300,start+700],[start+700,end-300],[end-300,end]];
  e.beats.forEach((b,j)=>{b.start_ms=spans[j][0];b.end_ms=spans[j][1];});return e;})
}))};
test('scoped execution fixes inactive scrims at boundaries and reverse seeks without weakening the guard',{timeout:60000},async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.MOTION_CHROMIUM_PATH});
 try{
  const page=await browser.newPage({viewport:{width:720,height:1280}});
  const bytes=require('node:child_process').execFileSync(process.env.FFMPEG_PATH||'ffmpeg',[
   '-hide_banner','-loglevel','error','-f','lavfi','-i','color=c=brown:s=180x320:r=30:d=12','-an','-c:v','libvpx','-f','webm','pipe:1']);
  await page.route('**/*',async r=>{
   const p=new URL(r.request().url()).pathname;
   if(p==='/assets/source.mp4')return r.fulfill({contentType:'video/webm',body:bytes});
   if(p==='/assets/logo.png')return r.fulfill({contentType:'image/png',body:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j0XcAAAAASUVORK5CYII=','base64')});
   if(p==='/')return r.fulfill({contentType:'text/html',body:`<style>
body{margin:0}video{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
img{position:absolute;left:30px;top:50px;width:90px;height:50px}
.scrim{position:absolute;padding:12px} .text{font:32px sans-serif;color:white;white-space:nowrap}
</style><video id="video0" src="assets/source.mp4" preload="auto" muted></video><img id="logo0" src="assets/logo.png">
<div class="scrim"><div class="text" id="title">Uma pausa</div></div>
<div class="scrim"><div class="text" id="body">No seu dia</div></div>
<div class="scrim"><div class="text" id="cta">Venha conhecer</div></div>`});
   return r.abort();
  });
  async function setup(enabled){
   await page.goto('https://motion.test/');
   await page.evaluate(async()=>{
    await Promise.all([...document.images].map(i=>i.decode()));
    const v=document.querySelector('video');if(v.readyState<2)await new Promise(r=>v.addEventListener('loadeddata',r,{once:true}));
   });
   await page.evaluate(({plan,helper,scrim,scope,guard,enabled})=>{
    (0,eval)(helper);(0,eval)(scrim);
    const v=document.querySelector('video'),logo=document.querySelector('img');
    window.seek=async ms=>{
     const active=ms<6780?0:1;v.id='video'+active;logo.id='logo'+active;
     for(const s of plan.scenes)for(const e of s.elements){
      const node=document.getElementById(e.id);videoTextSeek(node,e.beats,ms);
      const m=new DOMMatrixReadOnly(getComputedStyle(node).transform);
      videoTextWithScrim(node,{x:m.e,y:m.f,opacity:Number(getComputedStyle(node).opacity)},112,e.id==='body'?562:362);
      // Even a model that exposes every scrim after measuring is contained by the runtime.
      node.parentElement.style.setProperty('display','block','important');
     }
     await Promise.resolve();
    };
    if(enabled)(0,eval)('('+scope+')')(plan);
    (0,eval)('('+guard+')')(plan);
   },{plan,helper,scrim,scope,guard,enabled});
  }
  await setup(false);
  await assert.rejects(page.evaluate(()=>window.seek(0)),/MOTION_VIDEO_UNPLANNED_OVERLAY/);
  await setup(true);
  for(let i=0;i<=336;i++)await page.evaluate(ms=>window.seek(ms),i*1000/30);
  for(const ms of [11200,11199,6781,6780,6779,0,6780,0]){
   await page.evaluate(ms=>window.seek(ms),ms);
   assert.deepEqual(await page.evaluate(()=>['title','body','cta'].map(id=>getComputedStyle(document.getElementById(id).parentElement).display)),ms<6780?['block','block','none']:['none','none','block']);
  }
  await page.evaluate(()=>{const p=document.createElement('div');p.id='unknown';p.style='position:absolute;left:400px;top:400px;width:3px;height:30px;background:orange';document.body.append(p);});
  await assert.rejects(page.evaluate(()=>window.seek(500)),/MOTION_VIDEO_UNPLANNED_OVERLAY/);
  await page.evaluate(()=>document.getElementById('unknown').remove());
  await page.evaluate(()=>document.getElementById('cta').append(document.createElement('br')));
  await assert.rejects(page.evaluate(()=>window.seek(7300)),/MOTION_VIDEO_READABLE_ACTION_OVERLAY_REQUIRED/);
  await setup(true);
  await page.evaluate(()=>document.getElementById('cta').parentElement.append(document.createElement('span')));
  await assert.rejects(page.evaluate(()=>window.seek(0)),/MOTION_VIDEO_SCENE_SCOPE_INVALID/);
 }finally{await browser.close();}
});
