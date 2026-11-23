// Synthetic Chromium checks: sibling scrims are not a free decoration bypass.
const fs=require('node:fs'),assert=require('node:assert/strict');
const {test}=require('node:test');
const {chromium}=require(process.env.MOTION_PLAYWRIGHT_PATH||'playwright');
const guards=['v1','v2'].map(v=>fs.readFileSync(`app/assets/motion_photo/photo-polish-${v}.js`,'utf8'));
test('versioned sibling scrim admission preserves decoration and readability gates',async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.MOTION_CHROMIUM_PATH?{executablePath:process.env.MOTION_CHROMIUM_PATH}:{})});
 try{
 const page=await browser.newPage({viewport:{width:720,height:1280}});await page.route('**/*',r=>r.abort());
 const variants=[
  ['radial','','',null],
  ['solid','#phrase-scrim{background:rgba(0,0,0,.75)}','',null],
  ['unknown id','', 'unknown',/DECORATION/],
  ['colored','#phrase-scrim{background:orange}','',/DECORATION/],
  ['colored gradient','#phrase-scrim{background:radial-gradient(ellipse,orange,transparent)}','',/DECORATION/],
  ['full width','#phrase-scrim{left:0;width:720px}','',/DECORATION/],
  ['tall','#phrase-scrim{height:600px}','',/DECORATION/],
  ['not covering','#phrase-scrim{left:300px}','',/DECORATION/],
  ['border','#phrase-scrim{border-left:2px solid orange}','',/DECORATION/],
  ['outline','#phrase-scrim{outline:2px solid orange}','',/DECORATION/],
  ['shadow','#phrase-scrim{box-shadow:0 0 5px orange}','',/DECORATION/],
  ['filter','#phrase-scrim{filter:blur(2px)}','',/DECORATION/],
  ['mask','#phrase-scrim{clip-path:inset(5px)}','',/DECORATION/],
  ['pseudo','#phrase-scrim::after{content:"";width:10px;height:10px;background:orange}','',/DECORATION/],
  ['hidden text','#phrase{visibility:hidden}','',/DECORATION/],
  ['text content','','text',/DECORATION/],
  ['child node','','child',/DECORATION/],
  ['no text protection','#phrase{text-shadow:none}','',/TEXT_READABILITY/],
 ];
 for(const [name,css,change,error] of variants){
  for(const [i,source] of guards.entries()){
   await page.setContent(`<style>body{margin:0}#phrase{position:absolute;left:100px;top:200px;width:400px;color:white;font:32px sans-serif;text-shadow:0 2px 6px black}.scrim{position:absolute;left:80px;top:150px;width:450px;height:200px;background:radial-gradient(ellipse,rgba(0,0,0,.78) 0%,rgba(0,0,0,.5) 44%,rgba(0,0,0,0) 74%)}${css}</style><div id="phrase-scrim" class="scrim"></div><div id="phrase">Uma pausa.</div>`);
   await page.evaluate(change=>{const s=document.getElementById('phrase-scrim');if(change==='unknown')s.id='random-scrim';if(change==='text')s.textContent='x';if(change==='child')s.append(document.createElement('span'));window.seek=()=>{}},change);
   await page.evaluate(`(${source})({texts:['phrase'],images:[]})`);
   const expected=i===0?(name==='no text protection'?/TEXT_READABILITY/:/DECORATION/):error;
   if(expected)await assert.rejects(page.evaluate(()=>window.seek(2500)),expected,`${name} v${i+1}`);
   else for(const ms of [0,33.333,2500,5000,0]) {try{await page.evaluate(ms=>window.seek(ms),ms)}catch(e){console.log(name,await page.evaluate(()=>{const s=document.getElementById('phrase-scrim'),t=document.getElementById('phrase');return {s:s.getBoundingClientRect().toJSON(),t:t.getBoundingClientRect().toJSON(),bg:getComputedStyle(s).backgroundImage}}));throw e;}}
  }
 }
 }finally{await browser.close()}
});
