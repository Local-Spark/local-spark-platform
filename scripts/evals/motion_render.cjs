'use strict';
// Synthetic fixture evaluation only; scene JS executes in Chromium, never Node. Not production isolation.
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const {spawnSync}=require('node:child_process');
const {buildAudioArgs}=require('./motion_audio.cjs');
const digest=b=>crypto.createHash('sha256').update(b).digest('hex');
const origin='https://motion-fixture.invalid';
const fail=s=>{throw Error(s)};
function readBounded(file,max) {const stat=fs.lstatSync(file);if(!stat.isFile()||stat.size>max)fail('invalid file or size');return fs.readFileSync(file);}
function readPinned(item,max) {if(!item||typeof item.path!=='string'||!/^[a-f0-9]{64}$/.test(item.sha256))fail('missing file identity');const b=readBounded(path.resolve(item.path),max);if(digest(b)!==item.sha256)fail('file hash mismatch');return b;}
function safeRange(header,size) {const m=/^bytes=(\d+)-(\d*)$/.exec(header);if(!m)return null;const a=Number(m[1]),z=m[2]?Math.min(Number(m[2]),size-1):size-1;return Number.isSafeInteger(a)&&Number.isSafeInteger(z)&&a<=z&&a<size?{a,z}:null;}
function run(bin,args,env,timeout) {const r=spawnSync(bin,args,{env,timeout,killSignal:'SIGKILL',maxBuffer:2*1024*1024,stdio:['ignore','pipe','pipe']});if(r.error||r.status!==0)fail('local tool failed: '+path.basename(bin));return r.stdout;}
function deadline(p,ms=10000) {let timer;return Promise.race([p,new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error('browser operation timed out')),ms);})]).finally(()=>clearTimeout(timer));}
function executablePaths(cfg) {
 if(!cfg || cfg.synthetic_fixture!==true || !cfg.executable_paths)fail('synthetic fixture declaration required');
 const p=cfg.executable_paths;
 for(const k of ['playwright','chromium','ffmpeg','ffprobe']) if(typeof p[k]!=='string'||!path.isAbsolute(p[k])||!fs.existsSync(p[k]))fail('tool missing: '+k);
 for(const k of ['chromium','ffmpeg','ffprobe'])fs.accessSync(p[k],fs.constants.X_OK);
 return p;
}
async function disableBrowserSurfaces(context){
 await context.addInitScript(()=>{
  for(const key of ['RTCPeerConnection','webkitRTCPeerConnection','RTCIceCandidate','RTCSessionDescription','WebTransport']){
   Object.defineProperty(window,key,{value:undefined,writable:false,configurable:false});
  }
  Object.defineProperty(window,'open',{value:()=>null,writable:false,configurable:false});
 });
 if(typeof context.routeWebSocket!=='function')fail('WebSocket interception unavailable');
 await context.routeWebSocket('**/*',ws=>ws.close({code:1008,reason:'blocked'}));
}
async function preflight(cfg){
 const p=executablePaths(cfg),env={PATH:'/usr/bin:/bin',TMPDIR:'/private/tmp',LANG:'C.UTF-8'};
 for(const name of ['ffmpeg','ffprobe'])run(p[name],['-version'],env,10000);
 const {chromium}=require(path.resolve(p.playwright));let browser;
 try{
  browser=await chromium.launch({executablePath:p.chromium,headless:true,chromiumSandbox:true,env,timeout:15000});
  const context=await browser.newContext({serviceWorkers:'block',acceptDownloads:false});await disableBrowserSurfaces(context);let denied=0;
  await context.route('**/*',route=>{if(route.request().url()===origin+'/')return route.fulfill({status:200,contentType:'text/html',headers:{'content-security-policy':"default-src 'none'; script-src 'none'; connect-src 'none'; frame-src 'none'; object-src 'none'; worker-src 'none'"},body:'<!doctype html><title>synthetic preflight</title>'});denied++;return route.abort();});
  const probe=await context.newPage();let routeBlocked=false;try{await probe.goto('https://outbound-probe.invalid/',{timeout:5000});}catch{routeBlocked=true;}await probe.close();if(!routeBlocked||denied!==1)fail('route preflight failed');
  const page=await context.newPage();await page.goto(origin+'/',{waitUntil:'load',timeout:15000});
  const state=await page.evaluate(async()=>({webrtc:typeof RTCPeerConnection,webkit:typeof webkitRTCPeerConnection,webtransport:typeof WebTransport,popup:window.open('about:blank'),csp:await fetch('https://outbound-probe.invalid/').then(()=>false,()=>true)}));
  if(state.webrtc!=='undefined'||state.webkit!=='undefined'||state.webtransport!=='undefined'||state.popup!==null||state.csp!==true)fail('browser safety preflight failed');
  await context.close();console.log('Synthetic preflight passed; CSP/routes are not OS network isolation.');
 } finally {if(browser)await browser.close();}
}
async function main() {
 if(process.argv.length!==4)fail('usage: node motion_render.cjs CONFIG.json EMPTY_PRIVATE_OUTPUT');
 const [configPath,out]=process.argv.slice(2),configBytes=readBounded(path.resolve(configPath),1024*1024),cfg=JSON.parse(configBytes);
 const {playwright,chromium:browserExe,ffmpeg,ffprobe}=executablePaths(cfg);
 if(!Number.isSafeInteger(cfg.width)||!Number.isSafeInteger(cfg.height)||cfg.width<1||cfg.height<1||cfg.width*cfg.height>1920*1920||cfg.fps!==30||!Number.isSafeInteger(cfg.duration_ms)||cfg.duration_ms<1||cfg.duration_ms>60000||!Array.isArray(cfg.assets)||cfg.assets.length>32)fail('profile bounds');
 const html=readPinned(cfg.html,2*1024*1024),scene=readPinned(cfg.scene_init,1024*1024),assets=new Map(),paths=new Map();let total=html.length+scene.length;
 for(const a of cfg.assets){if(!/^assets\/[a-zA-Z0-9_.-]{1,80}$/.test(a.id)||assets.has(a.id)||!['video/mp4','image/png','image/jpeg','font/ttf','font/woff2','audio/wav','audio/ogg','audio/mpeg'].includes(a.mime))fail('asset identity');const body=readPinned(a,256*1024*1024);total+=body.length;assets.set(a.id,{body,contentType:a.mime});if(a.audio_id!==undefined){if(!/^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$/.test(a.audio_id)||paths.has(a.audio_id)||!a.mime.startsWith('audio/'))fail('audio identity');paths.set(a.audio_id,path.resolve(a.path));}}
 if(total>256*1024*1024)fail('input size budget');
 const audio=buildAudioArgs(cfg.audio,paths,cfg.duration_ms);
 const st=fs.statSync(out);if(!st.isDirectory()||(st.mode&0o777)!==0o700||fs.readdirSync(out).length)fail('output must be empty private directory');
 const env={PATH:'/usr/bin:/bin',TMPDIR:path.resolve(out),LANG:'C.UTF-8'};
 const audioInputs=[];for(const [id,p] of paths){const m=JSON.parse(run(ffprobe,['-v','error','-protocol_whitelist','file,pipe','-show_entries','format=duration:stream=codec_type','-of','json',p],env,10000));if(!m.streams.some(s=>s.codec_type==='audio')||!Number.isFinite(Number(m.format.duration)))fail('audio source invalid');audioInputs.push({id,duration_seconds:Number(m.format.duration)});}
 const {chromium}=require(path.resolve(playwright));
 const frames=path.join(out,'frames');fs.mkdirSync(frames,{mode:0o700});let browser;
 try {
  browser=await chromium.launch({executablePath:path.resolve(browserExe),headless:true,chromiumSandbox:true,env,timeout:15000});
  const context=await browser.newContext({viewport:{width:cfg.width,height:cfg.height},deviceScaleFactor:1,serviceWorkers:'block',acceptDownloads:false});await disableBrowserSurfaces(context);let denied=0;const served=new Set();
  const csp="default-src 'none'; script-src 'none'; style-src 'unsafe-inline'; img-src https://motion-fixture.invalid; media-src https://motion-fixture.invalid; font-src https://motion-fixture.invalid; connect-src 'none'; worker-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
  await context.route('**/*',async route=>{const req=route.request(),u=req.url(),id=u.startsWith(origin+'/')?u.slice(origin.length+1):'';const a=id?assets.get(id):null;if(req.method()!=='GET'||(u!==origin+'/'&&!a)){denied++;return route.abort();}if(!id)return route.fulfill({status:200,contentType:'text/html',headers:{'content-security-policy':csp},body:html});served.add(id);const range=req.headers().range;if(range&&a.contentType==='video/mp4'){const r=safeRange(range,a.body.length);if(!r){denied++;return route.abort();}return route.fulfill({status:206,contentType:a.contentType,headers:{'accept-ranges':'bytes','content-range':`bytes ${r.a}-${r.z}/${a.body.length}`},body:a.body.subarray(r.a,r.z+1)});}if(range){denied++;return route.abort();}return route.fulfill({status:200,headers:{'accept-ranges':'bytes'},...a});});
  const probe=await context.newPage();let routeBlocked=false;try{await probe.goto('https://outbound-probe.invalid/',{timeout:5000});}catch{routeBlocked=true;}await probe.close();if(!routeBlocked||denied!==1)fail('route isolation probe failed');denied=0;
  const page=await context.newPage();let popups=0;context.on('page',other=>{if(other!==page){popups++;void other.close();}});page.setDefaultTimeout(10000);let pageErrors=0;page.on('pageerror',()=>pageErrors++);
  await page.goto(origin+'/',{waitUntil:'load',timeout:15000});const controls=await page.evaluate(async()=>({csp:await fetch('https://outbound-probe.invalid/').then(()=>false,()=>true),webrtc:typeof RTCPeerConnection,webkit:typeof webkitRTCPeerConnection,webtransport:typeof WebTransport,popup:window.open('about:blank')}));const cspBlocked=controls.csp;if(!cspBlocked||controls.webrtc!=='undefined'||controls.webkit!=='undefined'||controls.webtransport!=='undefined'||controls.popup!==null)fail('browser controls failed');await deadline(page.evaluate(async()=>{await document.fonts.ready;for(const v of document.querySelectorAll('video')){v.pause();if(v.readyState<2)await new Promise((resolve,reject)=>{v.addEventListener('loadeddata',resolve,{once:true});v.addEventListener('error',reject,{once:true});});}}));
  // The synthetic fixture scene is evaluated inside Chromium only, never in Node.
  await deadline(page.evaluate(scene.toString('utf8')));if(!await page.evaluate(()=>typeof window.seek==='function'))fail('scene does not expose window.seek');
  const count=Math.ceil(cfg.duration_ms*30/1000),snapshots=[],picks=new Set([0,60,120,180,240,300,count-1]),ends=Date.now()+600000;let stored=0;
  for(let i=0;i<count;i++){if(Date.now()>ends)fail('render deadline');const state=await deadline(page.evaluate(ms=>window.seek(ms),i*1000/30));const b=await page.screenshot({type:'jpeg',quality:95,animations:'allow',timeout:10000});stored+=b.length;if(stored>2*1024*1024*1024)fail('frame budget');fs.writeFileSync(path.join(frames,`frame-${String(i).padStart(4,'0')}.jpg`),b,{mode:0o600});if(picks.has(i)){const file=`quadro-${String(i).padStart(4,'0')}.jpg`;fs.writeFileSync(path.join(out,file),b,{mode:0o600});snapshots.push({frame:i,file,sha256:digest(b),state});}if(i%60===0)console.log(`Frames ${i}/${count}`);}
  if(denied||pageErrors||popups)fail('browser blocked request, popup or script failed');await context.close();await browser.close();browser=null;
  for(const a of cfg.assets)readPinned(a,256*1024*1024);
  const output=path.join(out,'render.mp4');const args=['-nostdin','-v','error','-protocol_whitelist','file,pipe','-framerate','30','-i',path.join(frames,'frame-%04d.jpg'),...audio.inputs,...(audio.filter?['-filter_complex',audio.filter]:[]),...audio.mapArgs,'-c:v','libx264','-pix_fmt','yuv420p','-crf','20',...(audio.filter?['-c:a','aac','-b:a','192k']:[]),'-t',(count/30).toFixed(6),'-movflags','+faststart',output];run(ffmpeg,args,env,300000);
  const meta=JSON.parse(run(ffprobe,['-v','error','-show_entries','format=duration,size:stream=codec_name,codec_type,width,height,avg_frame_rate,duration','-of','json',output],env,10000));run(ffmpeg,['-nostdin','-v','error','-protocol_whitelist','file,pipe','-i',output,'-f','null','-'],env,30000);
  fs.writeFileSync(path.join(out,'trace.json'),JSON.stringify({description:'Synthetic fixture local evaluation only; browser controls are not production isolation.',synthetic_fixture:true,config_sha256:digest(configBytes),html_sha256:digest(html),scene_sha256:digest(scene),executor_sha256:digest(fs.readFileSync(__filename)),audio_module_sha256:digest(fs.readFileSync(require.resolve('./motion_audio.cjs'))),route_probe_blocked:routeBlocked,csp_probe_blocked:cspBlocked,assets:cfg.assets.map(a=>({id:a.id,sha256:a.sha256})),browser_sandbox:true,denied_requests:denied,audio_inputs:audioInputs,served_assets:[...served],frame_count:count,snapshots,output:{sha256:digest(fs.readFileSync(output)),metadata:meta},limitations:['Browser CSP and routing are not OS-level network isolation.','No automated rights, content, creative, speech or audio-quality review.','Model JavaScript is executable code; this is only for the declared synthetic fixture, not customers or production.']},null,2)+'\n',{mode:0o600});
 } finally {if(browser)await browser.close();fs.rmSync(frames,{recursive:true,force:true});}
 console.log('Private reproduction complete.');
}
if(require.main===module){const task=process.argv[2]==='--preflight'&&process.argv.length===4?preflight(JSON.parse(readBounded(path.resolve(process.argv[3]),1024*1024))):main();task.catch(e=>{console.error('Stopped:',e.message);process.exitCode=1;});}
