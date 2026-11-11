'use strict';
// Authored synthetic fixture for primitive execution, never an AI-quality benchmark.
const html = `<!doctype html><html lang="pt-BR"><meta charset="utf-8">
<style>
*{box-sizing:border-box}body{margin:0;background:#f4eddf;color:#223e32;font-family:Arial,sans-serif;overflow:hidden}
main{position:relative;width:360px;height:640px;padding:32px}
.brand{font-size:12px;letter-spacing:3px;font-weight:bold}
#title{position:absolute;left:32px;top:100px;font-size:48px;font-weight:800;line-height:1.02}
.card{position:absolute;left:32px;top:280px;width:296px;height:68px;padding:18px;background:#223e32;color:#f4eddf;font-size:23px;font-weight:bold}
#card2{top:360px}#card3{top:440px}.num{display:inline-block;width:42px;color:#dfb469;font-size:15px}
#close{position:absolute;left:32px;top:190px;width:296px;font-size:48px;line-height:1.06;font-weight:bold}
#line{position:absolute;left:32px;top:390px;width:296px;height:5px;background:#b86639;transform-origin:left}
.footer{position:absolute;left:32px;bottom:32px;font-size:11px;letter-spacing:1px}
</style><main><div class="brand">CAFÉ PAUSA · FICTÍCIO</div>
<div id="title">Um café.<br>Três tempos.</div>
<div class="card" id="card1"><span class="num">01</span>Moer.</div>
<div class="card" id="card2"><span class="num">02</span>Preparar.</div>
<div class="card" id="card3"><span class="num">03</span>Pausar.</div>
<div id="close">Seu tempo<br>pede uma<br>pausa.</div><div id="line"></div>
<div class="footer">DEMONSTRAÇÃO TÉCNICA · SEM ÁUDIO</div></main></html>`;
const scene = `(() => {
  const ease={kind:'cubic_bezier',parameters:[0.22,1,0.36,1]};
  const spring={kind:'spring',parameters:[150,18,1]};
  const cards=MotionV1.stagger(['card1','card2','card3'].map(id=>({id,
    initial:{x:32,opacity:0,clipRight:100,radius:12},beats:[
      {start_ms:650,end_ms:1150,to:{x:0,opacity:1,clipRight:0},curve:ease},
      {start_ms:2200,end_ms:2550,to:{x:-40,opacity:0,clipRight:100},curve:ease}]})),120);
  const t=MotionV1.timeline([
    {id:'title',initial:{y:36,opacity:0,clipBottom:100},beats:[
      {start_ms:0,end_ms:600,to:{y:0,opacity:1,clipBottom:0},curve:ease},
      {start_ms:2100,end_ms:2500,to:{y:-40,opacity:0},curve:ease}]},
    ...cards,
    {id:'close',initial:{y:45,opacity:0,scaleX:0.94,scaleY:0.94},beats:[
      {start_ms:2600,end_ms:3200,to:{y:0,opacity:1,scaleX:1,scaleY:1},curve:spring}]},
    {id:'line',initial:{scaleX:0,opacity:0},beats:[
      {start_ms:2850,end_ms:3300,to:{scaleX:1,opacity:1},curve:ease}]}
  ]);
  window.seek=async ms=>{t.seek(ms);};
})();`;
module.exports={html,scene};
