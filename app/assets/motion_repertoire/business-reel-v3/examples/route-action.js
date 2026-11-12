// Adaptação do mecanismo de percurso/estações do Finalizador S16; sem seu motor ou identidade.
window.makeRouteAction = ({canvas, labels, kit}) => {
  const g = canvas.getContext('2d');
  const width = canvas.width, height = canvas.height;
  const points = [[width*.18,height*.64],[width*.48,height*.37],[width*.80,height*.56]];
  const curve = {kind:'ease_in_out', parameters:[]};
  const isoBox = (x,y,h) => {
    const w = width*.10, d = height*.06;
    g.fillStyle = kit.background;
    g.beginPath(); g.moveTo(x-w,y-h); g.lineTo(x,y-d-h); g.lineTo(x+w,y-h);
    g.lineTo(x,y+d-h); g.closePath(); g.fill();
    g.fillStyle = kit.foreground; g.globalAlpha = .20;
    g.beginPath(); g.moveTo(x-w,y-h); g.lineTo(x,y+d-h); g.lineTo(x,y+d);
    g.lineTo(x-w,y); g.closePath(); g.fill();
    g.globalAlpha = .35;
    g.beginPath(); g.moveTo(x+w,y-h); g.lineTo(x,y+d-h); g.lineTo(x,y+d);
    g.lineTo(x+w,y); g.closePath(); g.fill(); g.globalAlpha = 1;
  };
  return ms => {
    g.clearRect(0,0,width,height);
    // A câmera desacelera enquanto a ação local termina; tudo é recalculado por ms.
    const wide = MotionV1.progress(ms, 2200, 3200, curve);
    const scale = 1.14-.14*wide;
    g.save(); g.translate(width/2,height/2); g.scale(scale,scale); g.translate(-width/2,-height/2);
    g.lineWidth = 3; g.strokeStyle = kit.accent;
    for (let i=0; i<2; i++) {
      const p = MotionV1.progress(ms, 450+i*950, 1050+i*950, curve);
      const [x,y] = points[i], [nx,ny] = points[i+1];
      g.beginPath(); g.moveTo(x,y); g.lineTo(x+(nx-x)*p,y+(ny-y)*p); g.stroke();
    }
    points.forEach(([x,y],i) => {
      const arrive = MotionV1.progress(ms, i*950, i*950+450, curve);
      isoBox(x,y,arrive*height*.12);
      g.fillStyle = kit.foreground; g.font = `24px ${kit.font}`; g.textAlign = 'center';
      g.fillText(labels[i],x,y+height*.12);
      // A chegada produz uma mudança de estado legível, não apenas outro ícone.
      g.fillStyle = kit.accent; g.globalAlpha = arrive;
      g.fillRect(x-width*.04,y-height*.16,width*.08,6); g.globalAlpha = 1;
    });
    g.restore();
  };
};
