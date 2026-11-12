// Adaptar à mensagem e ao kit. Função a incluir em scene_init, não runtime instalado.
window.makeLayeredEvidence = ({host, imageAssetId, label, kit}) => {
  const panel = document.createElement('div');
  Object.assign(panel.style, {position:'relative', width:'100%', height:'100%', overflow:'hidden',
    background:kit.background, color:kit.foreground, fontFamily:kit.font});
  const photo = document.createElement('img');
  photo.src = imageAssetId; // Apenas ID da lista assets autorizada, nunca imagem de referência.
  Object.assign(photo.style, {width:'100%', height:'76%', objectFit:'contain'});
  const caption = document.createElement('div');
  caption.textContent = label; // Conteúdo confirmado, não uma alegação do exemplo.
  Object.assign(caption.style, {position:'absolute', bottom:'4%', left:'6%', right:'6%',
    fontSize:'28px', lineHeight:'1.15'});
  const annotation = document.createElement('div');
  Object.assign(annotation.style, {position:'absolute', left:'6%', top:'72%', width:'88%', height:'4%'});
  panel.appendChild(photo); panel.appendChild(caption); panel.appendChild(annotation);
  host.appendChild(panel);
  const line = MotionElementsV1.connector(annotation, [[0,8],[120,8],[135,0]], {color:kit.accent}).parts.line;
  const curve = {kind:'ease_out', parameters:[]};
  return ms => {
    const enter = MotionV1.progress(ms, 0, 480, curve);
    const focus = MotionV1.progress(ms, 650, 1050, curve);
    panel.style.transform = `translateY(${(1-enter)*32}px)`;
    panel.style.opacity = String(enter);
    photo.style.transform = `scale(${1+focus*0.025})`;
    caption.style.transform = `translateY(${(1-focus)*18}px)`;
    caption.style.opacity = String(focus);
    MotionElementsV1.reveal(line, focus);
  };
};
