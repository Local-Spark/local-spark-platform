// Browser proof with an in-memory synthetic recording. No MP4 or provider calls.
const fs=require('node:fs'),assert=require('node:assert/strict'),{test}=require('node:test');
const {chromium}=require(process.env.MOTION_PLAYWRIGHT_PATH||'playwright');
const {failureCode}=require('../../assets/motion_html_renderer/runner.cjs');
const guard=fs.readFileSync('app/assets/motion_video/video-reel-v1.js','utf8');
const plan=JSON.parse(fs.readFileSync('app/tests/fixtures/motion_video_reel.json','utf8'));
const skill=fs.readFileSync('app/assets/motion_skills/instagram-reel-video-v19.md','utf8');
const scrimHelper=skill.split('```javascript\n')[1].split('```')[0];
const helper=fs.readFileSync('app/assets/motion_repertoire/business-video-reel-v1/examples/action-type.js','utf8');
test('VR1–VR3 real media: all frames, reverse seeks, layout and execution rejections',{timeout:45000},async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.MOTION_CHROMIUM_PATH});
 try{
 const page=await browser.newPage({viewport:{width:720,height:1280}});
 const bytes=require('node:child_process').execFileSync(process.env.FFMPEG_PATH||'ffmpeg',[
  '-hide_banner','-loglevel','error','-f','lavfi','-i','color=c=brown:s=180x320:r=30:d=3',
  '-an','-c:v','libvpx','-f','webm','pipe:1']);
 await page.route('**/*',async route=>{
  const path=new URL(route.request().url()).pathname;
  if(path==='/assets/source.mp4')return route.fulfill({contentType:'video/webm',body:Buffer.from(bytes)});
  if(path==='/assets/logo.png')return route.fulfill({contentType:'image/png',body:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j0XcAAAAASUVORK5CYII=','base64')});
  if(path==='/')return route.fulfill({contentType:'text/html',body:`<style>
body{margin:0}#sourcewrap{position:absolute;inset:0}video{position:absolute;width:100%;height:100%;object-fit:cover}
#logo{position:absolute;left:30px;top:50px;width:90px;height:50px}
#backing{position:absolute;left:100px;top:550px;padding:12px;background:rgba(0,0,0,.78)}
#cta{font:32px sans-serif;color:white;white-space:nowrap}
</style><div id="sourcewrap"><video id="recording" preload="auto" muted src="/assets/source.mp4"></video></div><img id="logo" src="/assets/logo.png"><div id="backing"><div id="cta">Uma pausa no seu dia.</div></div>`});
  return route.abort();
 });
 const failures={inset:'FULL_BLEED',contain:'FULL_BLEED',clip:'FULL_BLEED',hidden:'FULL_BLEED',blur:'FULL_BLEED',
  border:'FULL_BLEED',textfill:'READABLE',textbackground:'READABLE',textclip:'READABLE',rounded:'FULL_BLEED',rotated:'FULL_BLEED',behind:'KIT_OVERLAY',textbehind:'READABLE',unloaded:'FULL_BLEED',duplicate:'DOM_ID',poster:'KIT_OVERLAY',label:'UNPLANNED',logo:'KIT_OVERLAY',
  hero:'KIT_OVERLAY',footer:'READABLE',contrast:'READABLE',static:'TEXT_NOT',cancel:'TEXT_NOT',small:'READABLE',
  text_br:'READABLE',text_span:'READABLE',fading_scrim:'READABLE',fading_parent:'READABLE',declared_graphic:'UNPLANNED',transparent:'READABLE',pseudo:'UNPLANNED',duplicate_id:'DOM_ID',endpoint:'TEXT_NOT'};
 for(const mode of ['valid','v19','multiline',...Object.keys(failures)]){
  await page.goto('http://motion.test/',{waitUntil:'domcontentloaded'});
  await page.evaluate(async()=>{await Promise.all([...document.images].map(i=>i.decode()));const v=document.querySelector('video');if(v.readyState<2)await Promise.race([new Promise(r=>v.addEventListener('loadeddata',r,{once:true})),new Promise((_,r)=>setTimeout(()=>r(new Error('media readyState='+v.readyState+' error='+v.error?.code)),5000))]);});
  const executionPlan=structuredClone(plan);
  if(mode==='declared_graphic') executionPlan.scenes[0].elements.push({
    ...structuredClone(plan.scenes[0].elements[2]),id:'decorative-stroke',role:'graphic'
  });
  await page.evaluate(({helper,scrimHelper,plan,mode})=>{
   (0,eval)(helper);window.seek=ms=>videoTextSeek(document.getElementById('cta'),plan.scenes[0].elements[2].beats,mode==='static'?700:mode==='endpoint'&&ms!==0&&ms!==3000?700:ms);
   const v=document.getElementById('recording'),b=document.getElementById('backing'),t=document.getElementById('cta'),logo=document.getElementById('logo');
   if(['v19','multiline','text_br','text_span','fading_scrim','fading_parent','declared_graphic'].includes(mode)) {
    (0,eval)(scrimHelper);
    const seek=window.seek;
    window.seek=ms=>{
     seek(ms);
     const matrix=new DOMMatrixReadOnly(getComputedStyle(t).transform);
     const opacity=Number(getComputedStyle(t).opacity);
     videoTextWithScrim(t,{x:matrix.e,y:matrix.f,opacity},112,562);
     if(mode==='multiline')t.style.whiteSpace='pre-line';
     if(mode==='fading_scrim')b.style.backgroundColor='rgba(0,0,0,'+(.76*opacity)+')';
     if(mode==='fading_parent')b.style.opacity=String(opacity);
    };
    if(mode==='declared_graphic') {
     const stroke=document.createElement('div');stroke.id='decorative-stroke';
     stroke.style='position:absolute;left:300px;top:200px;width:3px;height:32px;background:orange';
     document.body.append(stroke);
    }
   }
   if(mode==='multiline')t.textContent='Uma pausa\nno seu dia.';
   if(mode==='text_br')t.replaceChildren('Uma pausa',document.createElement('br'),'no seu dia.');
   if(mode==='text_span'){
    const span=document.createElement('span');span.textContent='Uma pausa';
    t.replaceChildren(span,' no seu dia.');
   }
   if(mode==='border')v.style.border='20px solid beige';
   if(mode==='textfill')t.style.webkitTextFillColor='transparent';
   if(mode==='textbackground')t.style.background='white';if(mode==='textclip')t.style.overflow='hidden';
   if(mode==='rounded'){const w=document.getElementById('sourcewrap');w.style.overflow='hidden';w.style.borderRadius='40px';}
   if(mode==='rotated')v.style.transform='rotate(4deg) scale(1.2)';
   if(mode==='behind')logo.style.zIndex='-1';if(mode==='textbehind')b.style.zIndex='-1';
   if(mode==='inset')v.style.height='80%';if(mode==='contain')v.style.objectFit='contain';
   if(mode==='clip')document.getElementById('sourcewrap').style.clipPath='inset(20%)';
   if(mode==='hidden')v.style.opacity='.2';if(mode==='blur')v.style.filter='blur(2px)';
   if(mode==='unloaded'){v.removeAttribute('src');v.load();}
   if(mode==='duplicate')v.after(v.cloneNode());
   if(mode==='poster'){const p=document.createElement('div');p.style='position:absolute;inset:0;background:cream';p.style.background='beige';document.body.append(p);}
   if(mode==='label'){const p=document.createElement('h1');p.textContent='Café Aurora';document.body.append(p);}
   if(mode==='logo')logo.style.display='none';if(mode==='hero')logo.style.width='500px';
   if(mode==='footer')b.style.top='1100px';if(mode==='contrast')b.style.background='white';
   if(mode==='cancel')b.style.transform='translateX(-4px)';if(mode==='small')t.style.fontSize='10px';
   if(mode==='transparent')b.style.opacity='.3';
   if(mode==='pseudo'){const s=document.createElement('style');s.textContent='#sourcewrap::after{content:"brand";position:absolute;inset:0;background:beige}';document.head.append(s);}
   if(mode==='duplicate_id')t.after(t.cloneNode(true));
  },{helper,scrimHelper,plan:executionPlan,mode});
  await page.evaluate(({guard,plan})=>(0,eval)('('+guard+')')(plan),{guard,plan:executionPlan});
  if(['valid','v19','multiline'].includes(mode)){
   for(let i=0;i<=90;i++)await page.evaluate(ms=>window.seek(ms),i*100/3);
   for(const ms of [3000,2700,1200,700,699,300,299,150,0])await page.evaluate(ms=>window.seek(ms),ms);
  } else if(mode==='text_br'||mode==='text_span') {
   await page.evaluate(()=>window.seek(0));
   await assert.rejects(page.evaluate(()=>window.seek(1000/30)),error=>{
    assert.equal(failureCode(error),'MOTION_VIDEO_READABLE_ACTION_OVERLAY_REQUIRED');
    return true;
   });
  } else await assert.rejects(page.evaluate(ms=>window.seek(ms),mode==='fading_scrim'||mode==='fading_parent'?1000/30:500),new RegExp('MOTION_VIDEO_'+failures[mode]),mode);
 }
 }finally{await browser.close()}
});
