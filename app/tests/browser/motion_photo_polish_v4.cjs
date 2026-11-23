// Local DOM regressions for U1. No providers, customer images or rendering.
const fs=require('node:fs'),assert=require('node:assert/strict');
const {test}=require('node:test');
const {chromium}=require(process.env.MOTION_PLAYWRIGHT_PATH||'playwright');
const source=fs.readFileSync('app/assets/motion_photo/photo-polish-v3.js','utf8');
const finish=fs.readFileSync('app/assets/motion_photo/photo-finish-v1.js','utf8');
test('U1 rejects blobs and stacked glow even with valid T2 backing; finish remains strict',async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.MOTION_CHROMIUM_PATH?{executablePath:process.env.MOTION_CHROMIUM_PATH}:{})});
 try{
 const page=await browser.newPage({viewport:{width:720,height:1280}});await page.route('**/*',r=>r.abort());
 for(const [name,css,extra,error] of [
  ['discreet shadow','','',null],
  ['tight backing','#phrase{text-shadow:none;background:rgba(0,0,0,.75)}','',null],
  ['moderate sibling','','<div id="phrase-scrim"></div>',null],
  ['radial sibling','#phrase-scrim{background:radial-gradient(black,transparent)}','<div id="phrase-scrim"></div>',/DECORATION/],
  ['radial text','#phrase{background:radial-gradient(black,transparent)}','',/POLISH_STYLE/],
  ['radial ancestor','#wrap{background:radial-gradient(black,transparent)}','',/POLISH_STYLE/],
  ['wide glow','#phrase{text-shadow:0 0 24px black}','',/POLISH_STYLE/],
  ['glow with backing','#phrase{background:rgba(0,0,0,.75);text-shadow:0 0 24px black}','',/POLISH_STYLE/],
  ['stacked shadows','#phrase{text-shadow:0 0 4px black,0 0 4px black}','',/POLISH_STYLE/],
  ['shadow offset','#phrase{text-shadow:3px 0 3px black}','',/POLISH_STYLE/],
  ['weak backing','#phrase{text-shadow:none;background:rgba(0,0,0,.74)}','',/TEXT_READABILITY/],
  ['opaque backing','#phrase{background:black}','',/POLISH_STYLE/],
  ['rounded backing','#phrase{background:rgba(0,0,0,.75);border-radius:50%}','',/POLISH_STYLE/],
  ['oversized sibling','#phrase-scrim{left:50px;width:500px}','<div id="phrase-scrim"></div>',/DECORATION/],
  ['opaque sibling','#phrase-scrim{background:black}','<div id="phrase-scrim"></div>',/DECORATION/],
  ['sibling cannot replace T2','#phrase{text-shadow:none}','<div id="phrase-scrim"></div>',/TEXT_READABILITY/],
  ['descendant glow','#phrase span{text-shadow:0 0 20px black}','',/POLISH_STYLE/],
  ['box glow','#phrase{box-shadow:0 0 20px black}','',/POLISH_STYLE/],
  ['full band','#phrase{left:0;width:720px;background:rgba(0,0,0,.75)}','',/LOCAL_SCRIM/],
  ['masked text','#phrase{clip-path:inset(0 0 100%)}','',/TYPOGRAPHY/],
  ['hidden text','#phrase{opacity:0}','',/TYPOGRAPHY/],
 ]){
  await page.setContent(`<style>body{margin:0}#wrap{position:absolute;left:100px;top:200px;width:300px;height:40px}#phrase{width:300px;height:40px;color:white;font:32px sans-serif;text-shadow:0 2px 4px black}#phrase-scrim{position:absolute;left:90px;top:190px;width:320px;height:60px;background:rgba(0,0,0,.3)}${css}</style>${extra}<div id="wrap"><div id="phrase"><span>Uma pausa.</span></div></div>`);
  await page.evaluate('window.seek=()=>{}');
  await page.evaluate(`(${finish})({scenes:[{start:0,end:5000,texts:['phrase']}],typography:[{id:'phrase',start:0,end:5000,a:[1,0,0],z:[1,0,0]}]})`);
  await page.evaluate(`(${source})({texts:['phrase'],images:[]})`);
  if(error)await assert.rejects(page.evaluate(()=>window.seek(2500)),error,name);
  else for(const ms of [0,33.333,2500,5000,2500,0])await page.evaluate(ms=>window.seek(ms),ms);
 }
 }finally{await browser.close()}
});
test('U2 verifies primary motion at absolute middle/reverse seeks, not only endpoints',async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.MOTION_CHROMIUM_PATH?{executablePath:process.env.MOTION_CHROMIUM_PATH}:{})});
 try{
 const page=await browser.newPage({viewport:{width:720,height:1280}});await page.route('**/*',r=>r.abort());
 for(const mode of ['linear','static','endpoint-only','cancel-parent','missing','skew']){
  await page.setContent('<div id="wrap"><div id="photo" style="width:720px;height:1280px"></div></div>');
  await page.evaluate(mode=>{window.seek=ms=>{
   const photo=document.getElementById('photo');
   if(mode==='missing'){photo?.remove();return}
   const scale=1.04+.05*ms/5000;
   photo.style.transform=mode==='static'?'scale(1.04)':mode==='endpoint-only'&&ms!==5000?'scale(1.04)':`scale(${scale})`;
   if(mode==='cancel-parent')document.getElementById('wrap').style.transform=`scale(${1/scale})`;
   if(mode==='skew')photo.style.transform+=' skew(4deg)';
  }},mode);
  await page.evaluate(`(${source})({texts:[],images:['photo'],continuity:[{id:'photo',start:0,end:5000,a:[1.04,0,0],z:[1.09,0,0]}]})`);
  if(mode!=='linear')await assert.rejects(page.evaluate(()=>window.seek(2500)),/CONTINUITY_NOT_EXECUTED/,mode);
  else for(const ms of [0,2500,5000,2500,0,5001])await page.evaluate(ms=>window.seek(ms),ms);
 }
 }finally{await browser.close()}
});
