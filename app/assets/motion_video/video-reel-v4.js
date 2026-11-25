function installVideoReelV4(plan) {
  const original = window.seek;
  const fail = code => { throw new Error('MOTION_VIDEO_' + code); };
  const node = id => {
    const nodes = document.querySelectorAll(`[id="${id}"]`);
    if (nodes.length !== 1) fail('DOM_ID_INVALID');
    return nodes[0];
  };
  const fills = r => r.left <= .01 && r.top <= .01 && r.right >= innerWidth-.01 && r.bottom >= innerHeight-.01;
  const color = s => (s.match(/[\d.]+/g) || []).map(Number);
  const present = el => {
    for(let n=el;n;n=n.parentElement) {
      const s=getComputedStyle(n);
      if(s.display==='none'||s.visibility!=='visible'||Number(s.opacity)===0) return false;
    }
    return true;
  };
  const visible = (el, soft=false) => {
    for (let n=el;n;n=n.parentElement) {
      const s=getComputedStyle(n);
      const floor = soft && n===el ? .02 : .99;
      if (s.display==='none' || s.visibility!=='visible' || Number(s.opacity)<floor || s.filter!=='none' || s.maskImage!=='none' || s.clipPath!=='none' || s.mixBlendMode!=='normal') return false;
    }
    return true;
  };
  const onTop = (el, video) => {
    const old=el.style.pointerEvents, vOld=video.style.pointerEvents;
    el.style.pointerEvents='auto';video.style.pointerEvents='auto';
    const r=el.getBoundingClientRect(), top=document.elementFromPoint((r.left+r.right)/2,(r.top+r.bottom)/2);
    el.style.pointerEvents=old;video.style.pointerEvents=vOld;
    return top===el;
  };
  window.seek = async function(ms) {
    await original.call(window, ms);
    const scene = [...plan.scenes].reverse().find(s=>s.start_ms<=ms && (ms<s.end_ms || ms===plan.duration_ms && s.end_ms===ms));
    if (!scene || Math.abs(innerWidth/innerHeight-9/16)>.001) fail('FULL_BLEED_REQUIRED');
    const layout=scene.video_layout, video=node(layout.video_element_id), vs=getComputedStyle(video);
    const edit=layout.edit, span=scene.end_ms-scene.start_ms, local=ms-scene.start_ms, edge=Math.min(500,span/4);
    const soft=!!edit&&(edit.transition==='dissolve'||edit.transition==='fade')&&(local<edge||local>span-edge)&&layout.design.layers.some(layer=>{
      if(Math.abs(layer.box.x)>1e-9||Math.abs(layer.box.y)>1e-9||Math.abs(layer.box.width-1)>1e-9||Math.abs(layer.box.height-1)>1e-9||layer.z_index>=10) return false;
      const el=document.getElementById(layer.element_id); if(!el) return false;
      const s=getComputedStyle(el), r=el.getBoundingClientRect();
      return present(el)&&Number(s.opacity)>=.95&&fills(r);
    });
    if (document.querySelectorAll('video').length!==1 || video.tagName!=='VIDEO' || video.readyState<2 || !video.videoWidth ||
        !new URL(video.currentSrc || video.src).pathname.endsWith('/assets/source.mp4') || vs.objectFit!=='cover' ||
        vs.borderRadius!=='0px' || (layout.mode==='cover'&&!fills(video.getBoundingClientRect())&&!soft) || !visible(video, soft)) fail('FULL_BLEED_REQUIRED');
    for(let n=video;n;n=n.parentElement) {
      const s=getComputedStyle(n),m=new DOMMatrixReadOnly(s.transform);
      if(['borderTopWidth','borderRightWidth','borderBottomWidth','borderLeftWidth'].some(k=>parseFloat(s[k])>0)||!m.is2D||m.a<=0||Math.abs(m.a-m.d)>.0001||Math.abs(m.b)>.0001||Math.abs(m.c)>.0001||
         ((s.overflowX!=='visible'||s.overflowY!=='visible')&&s.borderRadius!=='0px')) fail('FULL_BLEED_REQUIRED');
      if(layout.mode==='cover'&&(s.overflowX!=='visible'||s.overflowY!=='visible')&&!fills(n.getBoundingClientRect())) fail('FULL_BLEED_REQUIRED');
    }
    const logo=node(layout.brand_element_id), lr=logo.getBoundingClientRect();
    if(logo.tagName!=='IMG'||!logo.complete||!logo.naturalWidth||!new URL(logo.currentSrc||logo.src).pathname.endsWith('/assets/logo.png')||
       !visible(logo)||lr.width<12||lr.height<12||lr.width>innerWidth*.25||lr.height>innerHeight*.12||
       lr.left<0||lr.top<0||lr.right>innerWidth||lr.bottom>innerHeight||!onTop(logo,video)) fail('KIT_OVERLAY_REQUIRED');
    const allowed=new Set([video,logo]);
    for(const layer of layout.design.layers) {
      const el=node(layer.element_id),e=scene.elements.find(e=>e.id===layer.element_id);
      if((e.role==='image'&&(el.tagName!=='IMG'||!el.complete||!el.naturalWidth||!new URL(el.currentSrc||el.src).pathname.endsWith('/'+e.asset_id)))||
        (e.role==='graphic'&&(el.tagName.toLowerCase()!=='svg'||!el.children.length||el.textContent.trim()))) fail('LAYER_NOT_EXECUTED');
      allowed.add(el);
      for(const child of el.querySelectorAll('*')) allowed.add(child);
    }
    let overlayArea=0;
    for(const id of layout.text_element_ids) {
      const el=node(id), e=scene.elements.find(e=>e.id===id), s=getComputedStyle(el);
      const b=e.beats.find(b=>b.start_ms<=ms&&ms<=b.end_ms);
      if(!b) fail('TEXT_NOT_EXECUTED');
      const a=JSON.parse(b.start_state),z=JSON.parse(b.end_state),p=(ms-b.start_ms)/(b.end_ms-b.start_ms);
      const expected=k=>a[k]+(z[k]-a[k])*p,m=new DOMMatrixReadOnly(s.transform);
      if(!m.is2D||Math.abs(m.a-1)>.0001||Math.abs(m.d-1)>.0001||Math.abs(m.b)>.0001||Math.abs(m.c)>.0001||
         Math.abs(m.e-expected('x'))>.01||Math.abs(m.f-expected('y'))>.01||Math.abs(Number(s.opacity)-expected('opacity'))>.001) fail('TEXT_NOT_EXECUTED');
      const backing=el.parentElement, r=el.getBoundingClientRect(), br=backing.getBoundingClientRect(),bs=getComputedStyle(backing);
      allowed.add(el);allowed.add(backing);
      // Weight by planned opacity so idle/fading plates do not burn the readable budget.
      overlayArea+=br.width*br.height*expected('opacity');
      // Geometry/contrast gates apply to sustained copy, not enter/exit fades.
      if(expected('opacity')<0.95) continue;
      const c=color(s.color),bg=color(bs.backgroundColor);
      // Declared text may use inline spans; reject only empty or oversized copy.
      if(!onTop(el,video)||!el.textContent.trim()||el.textContent.trim().length>120||!visible(backing)||
         s.display==='none'||s.visibility!=='visible'||s.filter!=='none'||s.clipPath!=='none'||s.maskImage!=='none'||s.mixBlendMode!=='normal'||
         s.backgroundImage!=='none'||(color(s.backgroundColor)[3]??1)!==0||
         s.overflowX!=='visible'||s.overflowY!=='visible'||
         parseFloat(s.fontSize)<innerWidth*28/720||c.length<3||c.slice(0,3).some(v=>v<240)||(c[3]??1)!==1||
         bg.length!==4||bg.slice(0,3).some(v=>v!==0)||bg[3]<.75||bg[3]>.8||bs.backgroundImage!=='none'||
         bs.boxShadow!=='none'||br.width>=innerWidth*.9||br.height>=innerHeight*.25||
         r.left<innerWidth*.04||r.right>innerWidth*.96||r.top<innerHeight*.12||r.bottom>innerHeight*.78||
         // Scrim inset is enforced when copy is settled; kinetic enter/exit may shift within the plate.
         (Math.hypot(expected('x'),expected('y'))<.5&&
          [r.left-br.left,r.top-br.top,br.right-r.right,br.bottom-r.bottom].some(v=>v<-.01||v>16.01))) fail('READABLE_ACTION_OVERLAY_REQUIRED');
      // Parent transforms must not cancel the declared text movement or clip its glyphs.
      for(let n=backing;n;n=n.parentElement) {
        const ns=getComputedStyle(n);
        if(ns.transform!=='none'||ns.overflowX!=='visible'||ns.overflowY!=='visible') fail('TEXT_NOT_EXECUTED');
      }
    }
    if(overlayArea>innerWidth*innerHeight*.35) fail('READABLE_ACTION_OVERLAY_REQUIRED');
    // Reject unplanned text/painted panels over the source, including pseudo-element posters.
    for(const el of [document.documentElement,document.body,...document.body.querySelectorAll('*')]) {
      if(['SCRIPT','STYLE'].includes(el.tagName)) continue;
      const s=getComputedStyle(el),r=el.getBoundingClientRect();
      if(!present(el)||!r.width||!r.height) continue;
      for(const pseudo of ['::before','::after']) {
        const ps=getComputedStyle(el,pseudo);
        if(!['none','normal'].includes(ps.content)) fail('UNPLANNED_OVERLAY');
      }
      if(allowed.has(el)||[...allowed].some(a=>a.contains&&a.contains(el))||el.contains(video)) continue;
      const bg=color(s.backgroundColor);
      if(el.textContent.trim()&&!layout.text_element_ids.some(id=>el.contains(node(id)))||
         s.backgroundImage!=='none'||(bg.length>=3&&(bg[3]??1)>0)||['IMG','SVG','CANVAS','VIDEO'].includes(el.tagName)||['borderTopWidth','borderRightWidth','borderBottomWidth','borderLeftWidth'].some(k=>parseFloat(s[k])>0)||s.boxShadow!=='none') fail('UNPLANNED_OVERLAY');
    }
  };
}
