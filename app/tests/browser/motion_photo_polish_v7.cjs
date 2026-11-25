// Synthetic images only, network denied; no provider or MP4 generation.
const fs=require('node:fs'),assert=require('node:assert/strict');
const {test}=require('node:test');
const {chromium}=require(process.env.MOTION_PLAYWRIGHT_PATH||'playwright');
const source=fs.readFileSync('app/assets/motion_photo/photo-polish-v5.js','utf8');
test('v7 allowlists declared graphics and still rejects residual decoration',async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.MOTION_CHROMIUM_PATH});
 try{
  const page=await browser.newPage({viewport:{width:720,height:1280}});
  await page.route('**/*',r=>r.abort());
  const src='data:image/svg+xml,'+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="900" height="1600"><rect width="900" height="1600" fill="brown"/></svg>');
  for(const [name,extra,graphics,expect] of [
   ['declared svg','<svg id="accent" width="40" height="40"><path d="M0 40V0H40" stroke="orange" fill="none"/></svg>',['accent'],null],
   ['undeclared svg','<svg width="40" height="40"><path d="M0 40V0H40" stroke="orange" fill="none"/></svg>',[],/DECORATION/],
   ['undeclared accent','<div class="mark" style="position:absolute;width:30px;height:2px;background:orange"></div>',[],/DECORATION/],
  ]){
   await page.setContent(`<style>body{margin:0;overflow:hidden}img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}#phrase{position:absolute;left:40px;top:200px;color:#fff;font:32px sans-serif;text-shadow:0 2px 3px #000}</style><img id="photo" src="${src}"><div id="phrase">Uma pausa.</div>${extra}`);
   await page.evaluate(async()=>{await Promise.all([...document.images].map(i=>i.decode()))});
   await page.evaluate(()=>{window.seek=ms=>{
    document.getElementById('photo').style.transform=`scale(${1.04+.04*Math.min(ms,5000)/5000})`;
   };});
   const plan={texts:['phrase'],images:['photo'],graphics,end:5000,
    cover:[{id:'photo',start:0,end:5000}],
    continuity:[{id:'photo',start:0,end:5000,a:[1.04,0,0],z:[1.08,0,0]}]};
   await page.evaluate(`(${source})(${JSON.stringify(plan)})`);
   if(expect) await assert.rejects(page.evaluate(()=>window.seek(2500)),expect,name);
   else for(const ms of [0,2500,5000,2500,0]) await page.evaluate(ms=>window.seek(ms),ms);
  }
 }finally{await browser.close()}
});
