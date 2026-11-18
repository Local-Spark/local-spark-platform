// Local synthetic DOM integration, no provider/network/customer material or MP4.
// Supply MOTION_PLAYWRIGHT_PATH when Playwright is installed outside node_modules.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {test} = require('node:test');
const {chromium} = require(process.env.MOTION_PLAYWRIGHT_PATH || 'playwright');
const source = fs.readFileSync(`app/assets/motion_photo/photo-guard-${process.env.PHOTO_GUARD_VERSION || 'v1'}.js`,'utf8');
const helper = fs.readFileSync('app/assets/motion_repertoire/business-reel-v12/examples/photo-reel.js','utf8');
const svg=Buffer.from('<svg xmlns="http://www.w3.org/2000/svg" width="720" height="1280"><rect width="720" height="1280" fill="#123456"/></svg>');
const beat={id:'photo',start:0,end:5000,a:[1.04,0,0],z:[1.16,0,0]};
const plan={end:5000,handoff_end:0,scenes:[{start_ms:0,end_ms:5000,
  photo_layout:{mode:'cover',primary_element_id:'photo'},
  photo_closing:{brand_element_id:'brand',cta_element_id:'cta'},
  elements:[{id:'photo',asset_id:'assets/photo-one.png'},{id:'brand',asset_id:'assets/logo.png'}],
  energy:[beat],closing_motion:[beat,{...beat,id:'brand',a:[1,0,0],z:[1.025,0,0]}]}]};
test('real Chromium computes cover, motion, ancestors/pseudos and CTA; rejects v8 regressions',async()=>{
  const browser=await chromium.launch({headless:true,...(process.env.MOTION_CHROMIUM_PATH?{executablePath:process.env.MOTION_CHROMIUM_PATH}:{})});
  try {
    const page=await browser.newPage({viewport:{width:720,height:1280}});
    await page.route('**/*',route=>route.fulfill({contentType:'image/svg+xml',body:svg}));
    for (const [name,css,script,expected] of [
      ['valid','','',null],
      ['two black CTA shadows','#cta{text-shadow:0 2px 6px black,0 1px 1px black}','',process.env.PHOTO_GUARD_VERSION==='v3'?null:/CTA_READABILITY_REQUIRED/],
      ['window','#photo {inset:400px 0 auto;height:480px;object-fit:contain}','',/COVER_REQUIRED/],
      ['wrapper plate','#brand-wrapper {background:#f5eddd}','',/BRAND_PLATE_FORBIDDEN/],
      ['pseudo plate','#brand-wrapper::before {content:"";position:absolute;inset:0;background:#eee}','',/BRAND_PLATE_FORBIDDEN/],
      ['static photo','','photoMotion=()=>{}',/ENERGY_NOT_EXECUTED/],
      ['hidden overlay','#brand-wrapper {opacity:0}','',/CLOSING_MOTION_NOT_EXECUTED/],
      ['unreadable CTA','#cta {font-size:10px}','',/CTA_READABILITY_REQUIRED/],
    ]) {
      await page.goto('about:blank');
      await page.setContent(`<base href="https://synthetic.invalid/"><style>
        *{box-sizing:border-box} html,body{margin:0;width:100%;height:100%;overflow:hidden}
        #photo{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
        #brand-wrapper{position:absolute;left:220px;top:800px;width:260px;height:150px}
        #brand{width:260px;height:150px;object-fit:contain}
        #cta{position:absolute;top:1000px;left:150px;color:white;font:32px sans-serif;text-shadow:0 2px 6px black}
        ${css}</style><img id="photo" src="assets/photo-one.png"><div id="brand-wrapper"><img id="brand" src="assets/logo.png"></div><div id="cta">Conheça o cardápio</div>`);
      await page.evaluate(async()=>{await Promise.all([...document.images].map(i=>i.decode()))});
      await page.evaluate(helper);
      await page.evaluate(`let photoMotion=window.makePhotoSceneMotion({photo:document.getElementById('photo'),start:0,end:5000,scaleStart:1.04,scaleEnd:1.16});
        const brandMotion=window.makePhotoSceneMotion({photo:document.getElementById('brand'),start:0,end:5000,scaleStart:1,scaleEnd:1.025,fit:'contain'});
        ${script};window.seek=ms=>{photoMotion(ms);brandMotion(ms)};`);
      await page.evaluate(`(${source})(${JSON.stringify(plan)})`);
      if (expected) await assert.rejects(page.evaluate(()=>window.seek(2500)),expected,name);
      else for (const ms of [0,1000,2500,4999,5000,2500,0]) await page.evaluate(ms=>window.seek(ms),ms);
    }
  } finally {await browser.close()}
});

test('S1–S2 supplement executes with v2 in Chromium, including reverse/end and local scrim',async()=>{
  const v2=fs.readFileSync('app/assets/motion_photo/photo-guard-v2.js','utf8');
  const finish=fs.readFileSync('app/assets/motion_photo/photo-finish-v1.js','utf8');
  const browser=await chromium.launch({headless:true,...(process.env.MOTION_CHROMIUM_PATH?{executablePath:process.env.MOTION_CHROMIUM_PATH}:{})});
  try {
    const page=await browser.newPage({viewport:{width:720,height:1280}});
    await page.route('**/*',route=>route.fulfill({contentType:'image/svg+xml',body:svg}));
    for (const [name,css,script,expected] of [
      ['valid local scrim','#cta{background:rgba(0,0,0,.4)}','',null],
      ['full-width band','#cta{left:0;width:720px;background:black}','',/LOCAL_SCRIM_REQUIRED/],
      ['static typography','','textMotion=()=>{}',/TYPOGRAPHY_NOT_EXECUTED/],
      ['frozen closing photo','','photoMotion=()=>{}',/ENERGY_NOT_EXECUTED/],
      ['frozen closing logo','','brandMotion=()=>{}',/CLOSING_MOTION_NOT_EXECUTED/],
    ]) {
      await page.goto('about:blank');
      await page.setContent(`<base href="https://synthetic.invalid/"><style>
        *{box-sizing:border-box} html,body{margin:0;width:100%;height:100%;overflow:hidden}
        #photo{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
        #brand{position:absolute;left:220px;top:800px;width:260px;height:150px;object-fit:contain}
        #cta{position:absolute;top:1000px;left:150px;color:white;font:32px sans-serif;text-shadow:0 2px 6px black}
        ${css}</style><img id="photo" src="assets/photo-one.png"><img id="brand" src="assets/logo.png"><div id="cta">Conheça o cardápio</div>`);
      await page.evaluate(async()=>{await Promise.all([...document.images].map(i=>i.decode()))});
      await page.evaluate(helper);
      await page.evaluate(`let photoMotion=window.makePhotoSceneMotion({photo:document.getElementById('photo'),start:0,end:5000,scaleStart:1.04,scaleEnd:1.16});
        let brandMotion=window.makePhotoSceneMotion({photo:document.getElementById('brand'),start:0,end:5000,scaleStart:1,scaleEnd:1.025,fit:'contain'});
        let textMotion=ms=>document.getElementById('cta').style.transform='translateY('+Math.max(0,1-ms/1000)*25.6+'px)';
        ${script};window.seek=ms=>{photoMotion(ms);brandMotion(ms);textMotion(ms)};`);
      await page.evaluate(`(${finish})(${JSON.stringify({scenes:[{start:0,end:5000,texts:['cta']}],typography:[{id:'cta',start:0,end:1000,a:[1,0,2],z:[1,0,0]}]})})`);
      const current=JSON.parse(JSON.stringify(plan));current.scenes[0].cta_read_start=1000;
      await page.evaluate(`(${v2})(${JSON.stringify(current)})`);
      if(expected) await assert.rejects(page.evaluate(()=>window.seek(500)),expected,name);
      else for(const ms of [0,500,1000,3500,4999,5000,500,0]) await page.evaluate(ms=>window.seek(ms),ms);
    }
  } finally {await browser.close()}
});
