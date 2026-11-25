'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const filename=path.resolve('app/assets/motion_video/capabilities-v1.js'),source=fs.readFileSync(filename,'utf8');
function fixture(options={}){
 const plan=JSON.parse(fs.readFileSync('app/tests/fixtures/motion_video_capabilities.json')).motion_plan;
 const nodes=[];
 function element(tag){
  const el={tagName:tag.toUpperCase(),id:'',src:'',style:{},children:[],textContent:'',isConnected:false,
   append(child){child.parentElement=this;child.isConnected=true;},decode:async()=>{},
   getBoundingClientRect(){const m=matrix(this.style.transform);return {left:parseFloat(this.style.left)+m.e,top:parseFloat(this.style.top)+m.f,width:parseFloat(this.style.width)+(options.rectWidth||0),height:parseFloat(this.style.height)};}};
  nodes.push(el);return el;
 }
 function matrix(s){const p=/translate\(([-\d.]+)px,([-\d.]+)px\)/.exec(s);const scale=/scale\(([-\d.]+)\)/.exec(s);return {a:scale?Number(scale[1]):1,d:scale?Number(scale[1]):1,b:0,c:0,e:p?Number(p[1]):0,f:p?Number(p[2]):0};}
 let callback;const video=element('video');video.duration=6;video.seeking=false;video._time=0;
 Object.defineProperty(video,'currentTime',{get(){return options.badTime?NaN:this._time;},set(v){this._time=v;queueMicrotask(()=>{if(callback&&!options.timeout)callback();});}});
 video.addEventListener=(_,fn)=>{callback=fn;};video.removeEventListener=()=>{};
 const document={body:{append(el){el.isConnected=true;el.parentElement=this;}},createElement:element,getElementById:id=>(options.collision||options.layerCollision&&id==='scene1-ribbon')?{}:nodes.find(n=>n.id===id&&n.isConnected),
  querySelectorAll:s=>s==='video'?(options.noVideo?[]:[video]):nodes.filter(n=>s===`[id="${n.id}"]`)};
 const window={seek:async()=>{if(options.change)options.change({nodes,plan,video});}};
 const context=vm.createContext({window,document,innerWidth:720,innerHeight:1280,URL:class extends URL{constructor(u){super(u,'https://motion.test/');}},
  DOMMatrixReadOnly:function(s){return {...matrix(s),...options.matrix};},
  getComputedStyle:el=>({visibility:'visible',filter:'none',maskImage:'none',clipPath:'none',backgroundImage:'none',mixBlendMode:'normal',...el.style,...options.style}),
  setTimeout:fn=>{if(options.timeout)queueMicrotask(fn);return 1;},clearTimeout:()=>{}});
 if(options.image){const e=plan.scenes[1].elements.at(-1);e.role='image';e.asset_id='assets/photo.png';plan.scenes[1].video_layout.design.layers.at(-1).shape='ellipse';}
 vm.runInContext(source,context,{filename});context.installVideoCapabilitiesV1(plan);
 return {window,nodes,video,plan};
}
test('runtime owns and executes plan layers and media at boundaries and reverse seeks',async()=>{
 for(const options of [{},{image:true}]){const f=fixture(options);for(const t of [0,1000,2999,3000,4000,6000,0,3000,3000])await f.window.seek(t);}
 assert.throws(()=>fixture({collision:true}),/LAYER_NOT_EXECUTED/);
 assert.throws(()=>fixture({layerCollision:true}),/LAYER_NOT_EXECUTED/);
 const f=fixture();for(const t of [-1,6001,NaN])await assert.rejects(f.window.seek(t),/LAYER_NOT_EXECUTED/);
});
test('rejects missing/altered nodes, ignored styles, invalid media time and timeout',async()=>{
 const changes=[
  {noVideo:true},{change:({video})=>video.duration=NaN},{badTime:true},{timeout:true},{change:({video})=>video.seeking=true},
  {change:({nodes})=>nodes.find(n=>n.id==='scene1-ribbon').isConnected=false},
  {change:({nodes})=>nodes.push(nodes.find(n=>n.id==='scene1-ribbon'))},
  {change:({nodes})=>nodes.find(n=>n.id==='scene1-ribbon').children.push({})},
  {change:({nodes})=>nodes.find(n=>n.id==='scene1-ribbon').textContent='rogue'},
  {change:({plan})=>plan.scenes[1].elements.at(-1).beats=[]},
  {image:true,change:({nodes})=>nodes.find(n=>n.id==='scene1-ribbon').src='assets/other.png'},
  ...Object.entries({display:'none',visibility:'hidden',filter:'blur(2px)',maskImage:'url(x)',clipPath:'inset(20%)',backgroundImage:'url(x)',mixBlendMode:'multiply',opacity:'0'}).map(([k,v])=>({style:{[k]:v}})),
  {matrix:{e:1000}},{matrix:{f:1000}},{rectWidth:100},
  {style:{transform:'translate(0px,200px)'}}
 ];
 for(const [index,options] of changes.entries()){const f=fixture(options);await assert.rejects(f.window.seek(4000),/MOTION_VIDEO_(LAYER_NOT_EXECUTED|EDIT_NOT_EXECUTED)/,String(index));}
});
