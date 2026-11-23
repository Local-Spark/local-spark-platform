// Synthetic images only, network denied; no provider or MP4 generation.
const fs=require('node:fs'),assert=require('node:assert/strict');
const {test}=require('node:test');
const {chromium}=require(process.env.MOTION_PLAYWRIGHT_PATH||'playwright');
const source=fs.readFileSync('app/assets/motion_photo/photo-polish-v4.js','utf8');
test('v6 full-bleed and continuous motion survive all frames, reverse seeks and overlap',async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.MOTION_CHROMIUM_PATH});
 try{
 const page=await browser.newPage({viewport:{width:720,height:1280}});
 await page.route('**/*',r=>r.abort());
 const src='data:image/svg+xml,'+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="900" height="1600"><rect width="900" height="1600" fill="brown"/></svg>');
 for(const mode of ['valid','contain','window','clipped','blur','hidden','static','endpoint-only','cancel-parent','missing','duplicate','gap']){
  await page.setContent(`<style>body{margin:0;overflow:hidden}.wrap{position:absolute;inset:0;overflow:hidden}img{position:absolute;width:100%;height:100%;object-fit:cover}</style><div id="a" class="wrap"><img id="photo" src="${src}"></div><div id="b" class="wrap"><img id="next" src="${src}"></div>`);
  await page.evaluate(async()=>{await Promise.all([...document.images].map(i=>i.decode()))});
  await page.evaluate(mode=>{
   window.seek=ms=>{
    const a=document.getElementById('a'),b=document.getElementById('b'),photo=document.getElementById('photo'),next=document.getElementById('next');
    if(mode==='missing'){photo?.remove();return}
    a.style.display=ms<5200?'block':'none';b.style.display=ms>=5000?'block':'none';
    a.style.opacity=ms<=5000?'1':String(Math.max(0,1-(ms-5000)/200));
    const scale=1.04+.05*Math.min(ms,5000)/5000;
    photo.style.transform=`scale(${mode==='static'||mode==='endpoint-only'&&ms!==5000?1.04:scale})`;
    next.style.transform=`scale(${1.04+.1*(ms-5000)/10000})`;
    if(mode==='contain')photo.style.objectFit='contain';
    if(mode==='window')photo.style.height='400px';
    if(mode==='clipped')a.style.clipPath='inset(300px 0)';
    if(mode==='blur')a.style.filter='blur(10px)';
    if(mode==='hidden')a.style.visibility='hidden';
    if(mode==='cancel-parent')a.style.transform=`scale(${1/scale})`;
    if(mode==='duplicate')a.append(photo.cloneNode());
   };
  },mode);
  const plan={texts:[],images:['photo','next'],end:15000,
   cover:[{id:'photo',start:0,end:5200},{id:'next',start:mode==='gap'?6000:5000,end:15000}],
   continuity:[{id:'photo',start:0,end:5000,a:[1.04,0,0],z:[1.09,0,0]},{id:'next',start:5000,end:15000,a:[1.04,0,0],z:[1.14,0,0]}]};
  await page.evaluate(`(${source})(${JSON.stringify(plan)})`);
  if(mode==='gap')await assert.rejects(page.evaluate(()=>window.seek(5500)),/FULL_BLEED/);
  else if(mode!=='valid')await assert.rejects(page.evaluate(()=>window.seek(2500)),/FULL_BLEED|CONTINUITY/,mode);
  else{
   for(let i=0;i<=450;i++)await page.evaluate(ms=>window.seek(ms),i*15000/450);
   for(const ms of [15000,5200,5199,5100,5001,5000,4999,2500,0])await page.evaluate(ms=>window.seek(ms),ms);
  }
 }
 }finally{await browser.close()}
});
