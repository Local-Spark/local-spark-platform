const fs=require('node:fs'),assert=require('node:assert/strict');
const {test}=require('node:test');
const {chromium}=require(process.env.MOTION_PLAYWRIGHT_PATH||'playwright');
const timing=fs.readFileSync('app/assets/motion_photo/photo-timing-v1.js','utf8');
const finish=fs.readFileSync('app/assets/motion_photo/photo-finish-v1.js','utf8');
test('production timing preserves text endpoint and photo handoff through reverse seeks',async()=>{
 const browser=await chromium.launch({headless:true});
 try{
  const p=await browser.newPage({viewport:{width:720,height:1280}});await p.route('**/*',r=>r.abort());
  await p.setContent('<div id="wrap"><div id="phrase" style="font:32px sans-serif">Uma pausa.</div></div>');
  await p.evaluate(timing);
  await p.evaluate(()=>{window.seek=ms=>{
   document.getElementById('wrap').style.display=PhotoTimingV1.textVisible(ms,13200,13400)?'block':'none';
   document.getElementById('phrase').style.transform=`scale(${1+.04*Math.max(0,Math.min(1,(ms-13200)/200))})`;
  }});
  await p.evaluate(`(${finish})({scenes:[],typography:[{id:'phrase',start:13200,end:13400,a:[1,0,0],z:[1.04,0,0]}]})`);
  for(const ms of [13199,13200,13399,13400,13401,13400,13200]){
   await p.evaluate(ms=>window.seek(ms),ms);
   assert.equal(await p.locator('#wrap').evaluate(e=>getComputedStyle(e).display),ms>=13200&&ms<=13400?'block':'none');
  }
  const results=await p.evaluate(()=>[4999,5000,5033,5200,5201,5033,5000].map(ms=>({
   ms,opacity:PhotoTimingV1.outgoingOpacity(ms,5000,5200),
   outgoing:PhotoTimingV1.photoVisible(ms,0,5200,15000),
   incoming:PhotoTimingV1.photoVisible(ms,5000,11200,15000),
  })));
  for(const r of results){assert.equal(r.opacity,1-Math.max(0,Math.min(1,(r.ms-5000)/200)));assert.equal(r.outgoing,r.ms<5200);assert.equal(r.incoming,r.ms>=5000)}
  assert.equal(await p.evaluate(()=>PhotoTimingV1.photoVisible(15000,11000,15000,15000)),true);
 }finally{await browser.close()}
});
