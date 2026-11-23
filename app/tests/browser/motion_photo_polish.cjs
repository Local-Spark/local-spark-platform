// Synthetic local Chromium integration. No provider requests or MP4 generation.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {test} = require('node:test');
const {chromium} = require(process.env.MOTION_PLAYWRIGHT_PATH || 'playwright');
const polish = fs.readFileSync(`app/assets/motion_photo/photo-polish-${process.env.PHOTO_POLISH_GUARD_VERSION || 'v1'}.js`,'utf8');
const finish = fs.readFileSync('app/assets/motion_photo/photo-finish-v1.js','utf8');
test('T2/T3 all visible phrases on bright material, reverse seeks and residual graphics',async()=>{
  const browser=await chromium.launch({headless:true,...(process.env.MOTION_CHROMIUM_PATH?{executablePath:process.env.MOTION_CHROMIUM_PATH}:{})});
  try {
    const page=await browser.newPage({viewport:{width:720,height:1280}});
    await page.route('**/*',route=>route.abort());
    for (const [name,css,extra,expected] of [
      ['shadow','','',null],
      ['multi-shadow','#phrase{text-shadow:0 2px 6px black,0 1px 1px black}','',null],
      ['local scrim','#phrase{text-shadow:none;background:rgba(0,0,0,.75)}','',null],
      ['child shadow override','#phrase span{text-shadow:none}','',/TEXT_READABILITY/],
      ['unprotected phrase','#phrase{text-shadow:none}','',/TEXT_READABILITY/],
      ['weak scrim','#phrase{text-shadow:none;background:rgba(0,0,0,.74)}','',/TEXT_READABILITY/],
      ['white shadow','#phrase{text-shadow:0 2px 6px white}','',/TEXT_READABILITY/],
      ['translucent shadow','#phrase{text-shadow:0 2px 6px #0008}','',/TEXT_READABILITY/],
      ['distant shadow','#phrase{text-shadow:30px 2px 6px black}','',/TEXT_READABILITY/],
      ['thin shadow','#phrase{text-shadow:0 1px 1px black}','',/TEXT_READABILITY/],
      ['tiny type','#phrase{font-size:10px}','',/TEXT_READABILITY/],
      ['dim type','#phrase{color:#777}','',/TEXT_READABILITY/],
      ['transparent type','#phrase{color:#fff8}','',/TEXT_READABILITY/],
      ['full band','#phrase{left:0;width:720px;background:black}','',/LOCAL_SCRIM/],
      ['wrapper full band','#wrap{width:720px;background:black}','',/LOCAL_SCRIM/],
      ['corner border','#phrase{border-left:3px solid orange}','',/DECORATION/],
      ['outline','#phrase{outline:2px solid orange}','',/DECORATION/],
      ['pseudo mark','#wrap::before{content:"";position:absolute;width:20px;height:20px;border-top:2px solid orange}','',/DECORATION/],
      ['undeclared accent','.accent{position:absolute;width:30px;height:2px;background:orange}', '<div class="accent"></div>',/DECORATION/],
      ['svg mark','', '<svg width="30" height="30"><path d="M0 30V0H30" stroke="orange"/></svg>',/DECORATION/],
      ['hidden old scene','#old{display:none}', '<div id="old"><span>Invisible unprotected text</span></div>',null],
      ['opacity zero old scene','#old{opacity:0}', '<div id="old">Invisible</div>',null],
      ['offscreen old scene','#old{position:absolute;left:-500px;width:100px}', '<div id="old">Offscreen</div>',null],
    ]) {
      await page.setContent(`<style>
        html,body{margin:0;width:720px;height:1280px;background:#ffe9c8}
        #wrap{position:absolute;top:300px;width:600px;height:150px}
        #phrase{position:absolute;left:50px;color:white;font:32px sans-serif;text-shadow:0 2px 6px black}
        ${css}</style><div id="wrap"><div id="phrase"><span>Uma pausa no dia.</span></div></div>${extra}`);
      await page.evaluate('window.seek=()=>{}');
      await page.evaluate(`(${finish})({scenes:[{start:0,end:5000,texts:['phrase']}],typography:[]})`);
      await page.evaluate(`(${polish})({texts:['phrase'],images:[]})`);
      if(expected) await assert.rejects(page.evaluate(()=>window.seek(2500)),expected,name);
      else for(const ms of [0,2500,5000,2500,0]) await page.evaluate(ms=>window.seek(ms),ms);
    }
  } finally {await browser.close()}
});
