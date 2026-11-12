// Transposição de camadas e carimbo de claude-video para MotionV1; sem GSAP ou paleta de origem.
window.makeLayeredType = ({host, lines, kit}) => {
  const entries = lines.map((text,index) => {
    const mask = document.createElement('div'), word = document.createElement('div');
    Object.assign(mask.style, {overflow:'hidden', position:'relative'});
    word.textContent = text;
    Object.assign(word.style, {fontFamily:kit.font, fontSize:'56px', lineHeight:'1.05',
      color:index===0?kit.accent:kit.foreground, transformOrigin:'left bottom'});
    mask.appendChild(word); host.appendChild(mask);
    return word;
  });
  const curve = {kind:'ease_out', parameters:[]};
  return ms => entries.forEach((word,i) => {
    const p = MotionV1.progress(ms, i*90, i*90+450, curve);
    word.style.transform = `translateY(${(1-p)*105}%) scale(${1.04-.04*p}) rotate(${(1-p)*-1.5}deg)`;
    // O estado final permanece para leitura; tempos são exemplo, não regra de marca.
  });
};
