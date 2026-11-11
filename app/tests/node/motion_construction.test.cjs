'use strict';
// Execute exactly the examples transmitted in the skill. No browser, media or render.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '../../assets');
const skill = fs.readFileSync(path.join(root, 'motion_skills/instagram-reel-v11.md'), 'utf8');
const examples = [...skill.matchAll(/```javascript\n([\s\S]*?)\n```/g)].map(match => match[1]);
function setup(ids) {
  const element=()=>({style:{},children:[],appendChild(node){this.children.push(node);}});
  const nodes = Object.fromEntries(ids.map(id => [id, element()]));
  const context = {document:{getElementById:id => nodes[id],createElement:element}};
  context.window = context;
  vm.runInNewContext(fs.readFileSync(path.join(root,'motion_html_renderer/movement-v3.js'),'utf8'),context);
  assert.equal(examples.length,5);
  for (const example of examples) vm.runInNewContext(example,context);
  return {context,nodes};
}
const ids = {back:'back',front:'front',video:'video',title:'title',nextTitle:'next-title'};
const timing = {openStart:0,openEnd:700,titleStart:800,titleEnd:1250,transferStart:3000,transferEnd:4100};
const travel = {x:80,y:30,videoScale:0.9};
test('passage coordinates layers, a stable reading interval and a continuous visible video', () => {
  const {context,nodes} = setup(Object.values(ids));
  const video = {src:'assets/authorized.mp4',currentTime:2.5};
  nodes.video.children.push(video);
  const seek = context.makeCompositionPassage({ids,timing,travel});
  const state = ms => {seek(ms);return JSON.stringify(nodes);};
  state(0);
  assert.equal(nodes.video.style.opacity,'1');
  assert.equal(nodes.title.style.opacity,'0');
  assert.equal(nodes['next-title'].style.opacity,'0');
  const read = state(1500);
  assert.equal(nodes.title.style.opacity,'1');
  assert.equal(nodes.title.style.clipPath,'inset(0% 0% 0% 0%)');
  assert.equal(state(2500),read);
  const middle = state(3500);
  assert.ok(Number(nodes.title.style.opacity)>0 && Number(nodes.title.style.opacity)<1);
  assert.ok(Number(nodes['next-title'].style.opacity)>0 && Number(nodes['next-title'].style.opacity)<1);
  assert.notEqual(nodes.back.style.transform,nodes.front.style.transform);
  assert.equal(nodes.video.style.opacity,'1');
  assert.equal(nodes.video.style.clipPath,undefined);
  const final = state(4100);
  assert.equal(nodes.title.style.opacity,'0');
  assert.equal(nodes['next-title'].style.opacity,'1');
  assert.match(nodes.video.style.transform,/scale\(0.9, 0.9\)/);
  assert.equal(state(9000),final);
  state(0);
  assert.equal(state(3500),middle);
  assert.equal(state(3500),middle);
  assert.equal(state(1500),read);
  // Wrappers move without replacing/restarting the media; media seeking is the caller's job.
  assert.equal(nodes.video.children[0],video);
  assert.deepEqual(video,{src:'assets/authorized.mp4',currentTime:2.5});
  const direct=setup(Object.values(ids));
  direct.nodes.video.children.push({...video});
  direct.context.makeCompositionPassage({ids,timing,travel})(3500);
  assert.equal(JSON.stringify(direct.nodes),middle);
});
test('stagger exposes final plan times and holds readable units across reverse seeks', () => {
  const {context,nodes}=setup(['primary','support','cta']);
  const result=context.makeReadingReveal({ids:['primary','support','cta'],start_ms:1000,duration_ms:450,step_ms:120});
  assert.deepEqual(JSON.parse(JSON.stringify(result.tracks.map(t=>[t.beats[0].start_ms,t.beats[0].end_ms]))),
    [[1000,1450],[1120,1570],[1240,1690]]);
  const state=ms=>{result.seek(ms);return JSON.stringify(nodes);};
  state(1100);
  assert.ok(Number(nodes.primary.style.opacity)>0);
  assert.equal(nodes.support.style.opacity,'0');
  assert.equal(nodes.cta.style.opacity,'0');
  const reading=state(1690);
  assert.ok(Object.values(nodes).every(node=>node.style.opacity==='1'));
  assert.equal(state(5000),reading);
  const middle=state(1300);
  state(0);
  assert.ok(Object.values(nodes).every(node=>node.style.opacity==='0'));
  assert.equal(state(1300),middle);
  assert.equal(state(1300),middle);
});


test('video treatment keeps the CSS frame and original media through entry, focus, exit and reverse seek', () => {
  const {context,nodes}=setup(['frame']);
  const media={src:'assets/source.mp4',currentTime:2.5};
  nodes.frame.children.push(media);
  Object.assign(nodes.frame.style,{borderRadius:'24px',border:'2px solid #244739',padding:'12px'});
  const timing={enterStart:100,enterEnd:600,focusStart:1200,focusEnd:2000,exitStart:3000,exitEnd:3600};
  const pose={x:0,y:0,enterOffset:24,startScale:0.94,restScale:1,focusScale:1.025,exitScale:0.97};
  const treatment=context.makeVideoFrameTreatment({id:'frame',timing,pose});
  const state=ms=>{treatment.seek(ms);return JSON.stringify(nodes);};
  state(0);assert.equal(nodes.frame.style.opacity,'0');
  const hold=state(700);assert.equal(state(1100),hold);
  const middle=state(1500);assert.notEqual(middle,hold);
  state(2200);assert.match(nodes.frame.style.transform,/scale\(1.025, 1.025\)/);
  state(3600);assert.equal(nodes.frame.style.opacity,'0');
  state(0);assert.equal(state(1500),middle);assert.equal(state(1500),middle);
  assert.equal(nodes.frame.style.borderRadius,'24px');
  assert.equal(nodes.frame.style.border,'2px solid #244739');
  assert.equal(nodes.frame.style.padding,'12px');
  assert.equal(nodes.frame.style.clipPath,undefined);
  assert.equal(nodes.frame.children[0],media);
  assert.deepEqual(media,{src:'assets/source.mp4',currentTime:2.5});
  assert.deepEqual(JSON.parse(JSON.stringify(treatment.tracks[0].beats.map(b=>[b.start_ms,b.end_ms]))),
    [[100,600],[1200,2000],[3000,3600]]);
});

const backdropSpec = {
  id:'background', colors:{base:'#f5f0e7',field:'#244739',accent:'#bb7a48'},
  timing:{openStart:100,openEnd:900,releaseStart:2300,releaseEnd:3100},
  geometry:{enterX:720,exitX:-720,bandWidth:90,accentFrom:720,accentTo:420,accentExit:-640,accentOpacity:0.14}
};
test('background uses kit planes, keeps its opaque base and rests while the focus is read', () => {
  const {context,nodes}=setup(['background','frame','title']);
  const media={src:'assets/source.mp4',currentTime:3.5};
  nodes.frame.children.push(media);
  Object.assign(nodes.frame.style,{borderRadius:'24px',border:'2px solid #244739'});
  const untouched=JSON.stringify([nodes.frame,nodes.title]);
  const result=context.makeNarrativeBackdrop(backdropSpec);
  assert.equal(nodes.background.children.length,3);
  assert.equal(nodes.background.style.overflow,'hidden');
  assert.equal(nodes.background.style.pointerEvents,'none');
  const {base,field,accent}=result.parts;
  assert.equal(base.style.background,backdropSpec.colors.base);
  assert.equal(field.style.background,backdropSpec.colors.field);
  assert.equal(accent.style.background,backdropSpec.colors.accent);
  const state=ms=>{result.seek(ms);return JSON.stringify(nodes.background);};
  state(0);assert.equal(field.style.transform,'translateX(720px)');
  assert.equal(accent.style.opacity,'0');
  const middle=state(500);
  assert.equal(field.style.transform,'translateX(360px)');
  assert.equal(accent.style.transform,'translateX(570px)');
  const hold=state(900);assert.equal(state(1500),hold);assert.equal(state(2300),hold);
  state(3100);assert.equal(field.style.transform,'translateX(-720px)');
  assert.equal(accent.style.opacity,'0');
  const final=state(4000);assert.equal(state(8000),final);
  for (const ms of [0,3100,500,500]) {state(ms);assert.equal(base.style.opacity,'1');}
  assert.equal(state(500),middle);
  assert.equal(JSON.stringify([nodes.frame,nodes.title]),untouched);
  assert.equal(nodes.frame.children[0],media);
  const direct=setup(['background']);
  direct.context.makeNarrativeBackdrop(backdropSpec).seek(500);
  assert.equal(JSON.stringify(direct.nodes.background),middle);
});
test('background preserves custom kit and rejects overlapping passage intervals before touching the host', () => {
  const {context,nodes}=setup(['background']);
  const spec={...backdropSpec, colors:{base:'#fafafa',field:'#112244',accent:'#ccaa88'}};
  const result=context.makeNarrativeBackdrop(spec);
  assert.equal(result.parts.base.style.background,'#fafafa');
  assert.equal(result.parts.field.style.background,'#112244');
  assert.equal(result.parts.accent.style.background,'#ccaa88');
  const before=JSON.stringify(nodes);
  assert.throws(()=>context.makeNarrativeBackdrop({...spec,timing:{...spec.timing,releaseStart:800}}),/BACKDROP_INVALID/);
  assert.equal(JSON.stringify(nodes),before);
  assert.throws(()=>context.makeNarrativeBackdrop({...spec,id:'missing'}),/BACKDROP_INVALID/);
});

const cutoutSpec={ids:{image:'cup',shadow:'shadow'},
  timing:{enterStart:100,enterEnd:900,exitStart:2500,exitEnd:3300},
  pose:{x:10,y:20,enterX:-80,exitX:80,lift:40,startScale:0.9,restScale:1,exitScale:0.95,
    angle:4,shadowOpacity:0.24,shadowBlur:8}};
function cutoutSetup() {
  const value=setup(['cup','shadow','frame','background']);
  Object.assign(value.nodes.cup,{tagName:'IMG',src:'assets/illustration-cup.png',naturalWidth:1024,naturalHeight:1024});
  value.nodes.shadow.style.background='#244739';
  value.nodes.frame.style.borderRadius='24px';
  return value;
}
test('cutout settles with its ground shadow and preserves image, frame and background through reverse seeking',()=>{
  const {context,nodes}=cutoutSetup();
  const before=JSON.stringify([nodes.frame,nodes.background]);
  const result=context.makeCutoutObject(cutoutSpec);
  const state=ms=>{result.seek(ms);return JSON.stringify(nodes);};
  state(0);assert.equal(nodes.cup.style.opacity,'0');assert.equal(nodes.shadow.style.opacity,'0');
  const middle=state(500);
  assert.equal(nodes.cup.style.transform,'translate(-30px,0px) rotate(2deg) scale(0.95)');
  assert.equal(nodes.shadow.style.transform,'translate(-30px,20px) scale(0.875)');
  assert.equal(nodes.shadow.style.filter,'blur(12px)');
  assert.equal(nodes.shadow.style.opacity,'0.09');
  const hold=state(900);assert.equal(state(1700),hold);assert.equal(state(2500),hold);
  assert.equal(nodes.shadow.style.filter,'blur(8px)');
  assert.equal(nodes.shadow.style.opacity,'0.24');
  assert.equal(nodes.cup.style.transform,'translate(10px,20px) rotate(0deg) scale(1)');
  const end=state(3300);assert.equal(state(6000),end);
  assert.equal(nodes.cup.style.opacity,'0');assert.equal(nodes.shadow.style.opacity,'0');
  assert.equal(state(500),middle);assert.equal(state(500),middle);
  assert.equal(nodes.cup.src,'assets/illustration-cup.png');
  assert.equal(nodes.cup.naturalWidth,nodes.cup.naturalHeight);
  assert.equal(nodes.cup.style.objectFit,'contain');
  assert.equal(nodes.shadow.style.background,'#244739');
  assert.equal(JSON.stringify([nodes.frame,nodes.background]),before);
  const direct=cutoutSetup();direct.context.makeCutoutObject(cutoutSpec).seek(500);
  assert.equal(JSON.stringify(direct.nodes),middle);
});
test('cutout rejects missing images, nonfinite values, invalid scales and overlapping beats before mutations',()=>{
  const {context,nodes}=cutoutSetup();
  const before=JSON.stringify(nodes);
  const invalid=[
    {...cutoutSpec,ids:{image:'missing',shadow:'shadow'}},
    {...cutoutSpec,ids:{image:'frame',shadow:'shadow'}},
    {...cutoutSpec,ids:{image:'cup',shadow:'missing'}},
    {...cutoutSpec,ids:{image:'cup',shadow:'cup'}},
    ...['enterStart','enterEnd','exitStart','exitEnd'].map(key=>({...cutoutSpec,timing:{...cutoutSpec.timing,[key]:NaN}})),
    ...[{enterStart:-1},{enterEnd:100},{exitStart:800},{exitEnd:2500}].map(change=>({...cutoutSpec,timing:{...cutoutSpec.timing,...change}})),
    ...[{startScale:0},{restScale:-1},{exitScale:0},{lift:-1},{angle:Infinity},{shadowBlur:-1},{shadowOpacity:-0.1},{shadowOpacity:1.1}]
      .map(change=>({...cutoutSpec,pose:{...cutoutSpec.pose,...change}}))
  ];
  for(const spec of invalid){
    assert.throws(()=>context.makeCutoutObject(spec),/MOTION_CUTOUT_INVALID/);
    assert.equal(JSON.stringify(nodes),before);
  }
});
