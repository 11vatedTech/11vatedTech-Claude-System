"""
11VATEDTECH FOUNDRY — L9 MASTER PASS
The Obsidian Forge — Enhanced Digital Painting
Adds: varied brush marks, better surface detail, richer atmospheric depth, material specificity.
"""
import os

OUT = "artifacts/visual/final-craft/heroes"
os.makedirs(OUT, exist_ok=True)

html = '''<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>The Obsidian Forge — L9 Master</title>
<style>
body{margin:0;background:#050210;display:flex;justify-content:center;align-items:center;min-height:100vh}
canvas{display:block;max-width:100vw;max-height:100vh}
.info{position:fixed;top:10px;left:10px;color:#555;font:11px monospace;z-index:10}
</style>
</head><body>
<div class="info">The Obsidian Forge — L9 Hero Master — Canvas Digital Painting</div>
<canvas id="c" width="1600" height="1100"></canvas>
<script>
const c=document.getElementById('c'),ctx=c.getContext('2d');
const W=1600,H=1100;

// === UTILITIES ===
function lerp(a,b,t){return a+(b-a)*t}
function clamp(v,lo,hi){return Math.max(lo,Math.min(hi,v))}
function rand(a,b){return a+Math.random()*(b-a)}

// Seeded hash for reproducibility
const SEED=42;
function hash(x,y){let n=Math.sin(x*127.1+y*311.7+SEED)*43758.5453;return n-Math.floor(n)}
function hash3(x,y,z){return hash(x+hash(y,z*100),y+hash(z,x*100))}

// Smooth value noise
function smoothNoise(x,y){
  const ix=Math.floor(x),iy=Math.floor(y);
  const fx=x-ix,fy=y-iy;
  const sx=fx*fx*(3-2*fx),sy=fy*fy*(3-2*fy);
  return lerp(lerp(hash(ix,iy),hash(ix+1,iy),sx),lerp(hash(ix,iy+1),hash(ix+1,iy+1),sx),sy);
}
function fbm(x,y,oct=6){let v=0,a=0.5,f=1;for(let i=0;i<oct;i++){v+=a*smoothNoise(x*f,y*f);f*=2.05;a*=0.48;}return v}

// === BRUSH ENGINE: 6 distinct mark types ===
function roundBrush(x,y,r,color,angle=0,pressure=1.0){
  ctx.save();ctx.translate(x,y);ctx.rotate(angle);
  ctx.globalAlpha=0.06*pressure;
  ctx.fillStyle=color;
  ctx.beginPath();
  for(let i=0;i<24;i++){
    const t=i/24*Math.PI*2;
    const irregularity=0.82+0.18*Math.sin(t*3+x*0.08)*Math.cos(t*5+y*0.08);
    const rx=r*1.3*irregularity;
    const ry=r*0.65*irregularity;
    const px=rx*Math.cos(t)+rand(-1,1)*r*0.05;
    const py=ry*Math.sin(t)+rand(-1,1)*r*0.05;
    if(i===0)ctx.moveTo(px,py);else ctx.lineTo(px,py);
  }
  ctx.closePath();ctx.fill();ctx.restore();
}

function flatBrush(x,y,w,h,color,angle=0,pressure=1.0){
  ctx.save();ctx.translate(x,y);ctx.rotate(angle);
  ctx.globalAlpha=0.05*pressure;
  ctx.fillStyle=color;
  ctx.beginPath();
  ctx.moveTo(-w/2,-h/6);
  ctx.bezierCurveTo(-w/3,-h/2,-w/6,-h/2,0,-h/3);
  ctx.bezierCurveTo(w/6,-h/2,w/3,-h/2,w/2,-h/6);
  ctx.lineTo(w/3,h/6);
  ctx.bezierCurveTo(w/6,h/3,-w/6,h/3,-w/3,h/6);
  ctx.closePath();ctx.fill();ctx.restore();
}

function dryBrush(x,y,w,h,color,angle=0){
  ctx.save();ctx.translate(x,y);ctx.rotate(angle);
  ctx.globalAlpha=0.03;
  ctx.strokeStyle=color;
  ctx.lineWidth=2;
  // Multiple parallel strokes with gaps
  for(let i=-h/2;i<h/2;i+=2){
    if(Math.random()>0.3){
      ctx.beginPath();
      const jitter=rand(-3,3);
      ctx.moveTo(-w/2+i*0.3,jitter);
      ctx.bezierCurveTo(-w/4,jitter+rand(-4,4),w/4,jitter+rand(-4,4),w/2+i*0.3,jitter);
      ctx.stroke();
    }
  }
  ctx.restore();
}

function hatching(x1,y1,x2,y2,density=12,color='#2a2a4a',width=0.6){
  ctx.save();ctx.strokeStyle=color;ctx.lineWidth=width;ctx.globalAlpha=0.2;
  const dx=x2-x1,dy=y2-y1,len=Math.sqrt(dx*dx+dy*dy);
  const nx=-dy/len,ny=dx/len;
  for(let i=0;i<density;i++){
    const t=(i+0.5)/density;
    const cx=x1+dx*t,cy=y1+dy*t;
    const jitter=hash(i+x1,y1)*6-3;
    const length=rand(4,12);
    ctx.beginPath();
    ctx.moveTo(cx+nx*jitter,cy+ny*jitter);
    ctx.lineTo(cx+nx*(jitter+length),cy+ny*(jitter+length));
    ctx.stroke();
  }
  ctx.restore();
}

function crossHatch(x,y,r,density=40,color='#2a2a4a'){
  ctx.save();ctx.strokeStyle=color;ctx.lineWidth=0.5;ctx.globalAlpha=0.12;
  for(let i=0;i<density;i++){
    const angle=rand(0,Math.PI);
    const dist=rand(0,r);
    const cx=x+Math.cos(angle)*dist;
    const cy=y+Math.sin(angle)*dist;
    const len=rand(3,8);
    ctx.beginPath();
    ctx.moveTo(cx,cy);
    ctx.lineTo(cx+Math.cos(angle)*len,cy+Math.sin(angle)*len);
    ctx.stroke();
  }
  ctx.restore();
}

function stipple(x,y,r,density=60,color='#2a2a4a'){
  ctx.save();ctx.fillStyle=color;ctx.globalAlpha=0.12;
  for(let i=0;i<density;i++){
    const a=rand(0,Math.PI*2);
    const d=rand(0,r);
    const sz=rand(0.3,1.0);
    ctx.beginPath();ctx.arc(x+Math.cos(a)*d,y+Math.sin(a)*d,sz,0,Math.PI*2);ctx.fill();
  }
  ctx.restore();
}

// === PALETTE: Obsidian forge world ===
const P={
  sky0:'#060212',sky1:'#0e0525',sky2:'#1a0a35',sky3:'#251545',
  neb1:'#2a1050',neb2:'#3a1560',
  mt0:'#12081e',mt1:'#1a0a2e',
  stone0:'#1a1a2a',stone1:'#252535',stone2:'#353545',stone3:'#4a4a5a',
  lava0:'#ff2200',lava1:'#ff4500',lava2:'#ff6b35',lava3:'#ff8c00',lava4:'#ffcc00',
  crystal0:'#3a1a60',crystal1:'#5a3080',crystal2:'#7b48ee',crystal3:'#9370db',crystal4:'#b8a9ff',
  copper0:'#5a3a1a',copper1:'#8b5a2b',copper2:'#b87333',copper3:'#cd7f32',copper4:'#daa06d',
  smoke:'#1a0a2e',
  shadow:'#080412'
};

// === LAYER 1: SKY ===
console.log('L1: Sky');
const skyG=ctx.createLinearGradient(0,0,0,H*0.55);
skyG.addColorStop(0,P.sky0);skyG.addColorStop(0.35,P.sky1);
skyG.addColorStop(0.65,P.sky2);skyG.addColorStop(1,P.sky3);
ctx.fillStyle=skyG;ctx.fillRect(0,0,W,H);

// === LAYER 2: STARS ===
console.log('L2: Stars');
for(let i=0;i<150;i++){
  const sx=rand(0,W),sy=rand(0,H*0.38);
  const sr=rand(0.15,0.8);
  ctx.globalAlpha=rand(0.1,0.45);
  ctx.fillStyle=Math.random()>0.85?'#dda0ff':Math.random()>0.5?'#aaccff':'#fff';
  ctx.beginPath();ctx.arc(sx,sy,sr,0,Math.PI*2);ctx.fill();
}
ctx.globalAlpha=1;

// === LAYER 3: NEBULA (painterly) ===
console.log('L3: Nebula');
ctx.globalCompositeOperation='screen';
for(let i=0;i<100;i++){
  const nx=rand(80,550),ny=rand(30,280);
  roundBrush(nx,ny,rand(30,90),P.neb2,rand(-0.4,0.4),rand(0.15,0.4));
}
for(let i=0;i<60;i++){
  const nx=rand(500,1100),ny=rand(20,200);
  roundBrush(nx,ny,rand(25,60),P.neb1,rand(-0.3,0.3),rand(0.1,0.3));
}
ctx.globalCompositeOperation='source-over';

// === LAYER 4: DISTANT MOUNTAINS ===
console.log('L4: Mountains');
// Mountain range with multiple ridges
for(let ridge=0;ridge<3;ridge++){
  const yBase=H*0.42+ridge*H*0.06;
  const opacity=0.3+ridge*0.2;
  ctx.fillStyle=ridge===0?P.mt0:P.mt1;
  ctx.globalAlpha=opacity;
  ctx.beginPath();
  ctx.moveTo(0,yBase);
  for(let x=0;x<=W;x+=3){
    const n=fbm(x*0.0015+ridge*3,ridge*2,5);
    ctx.lineTo(x,yBase-n*H*0.15);
  }
  ctx.lineTo(W,yBase+H*0.1);ctx.lineTo(0,yBase+H*0.1);ctx.closePath();ctx.fill();
}
ctx.globalAlpha=1;

// Atmospheric haze
const hazeG=ctx.createLinearGradient(0,H*0.35,0,H*0.58);
hazeG.addColorStop(0,'transparent');hazeG.addColorStop(0.5,P.sky3);hazeG.addColorStop(1,'transparent');
ctx.fillStyle=hazeG;ctx.globalAlpha=0.25;ctx.fillRect(0,H*0.35,W,H*0.23);ctx.globalAlpha=1;

// === LAYER 5: FORGE STRUCTURE ===
console.log('L5: Forge');
// Main arch — stone with texture
ctx.fillStyle=P.stone1;
ctx.beginPath();
ctx.moveTo(380,H*0.65);
ctx.bezierCurveTo(400,H*0.32,490,H*0.16,600,H*0.14);
ctx.bezierCurveTo(710,H*0.16,800,H*0.32,820,H*0.65);
ctx.closePath();ctx.fill();

// Stone surface detail — hatching + stipple
hatching(420,H*0.3,500,H*0.5,18,'#3a3a4a',0.5);
hatching(700,H*0.3,780,H*0.5,18,'#3a3a4a',0.5);
hatching(500,H*0.2,550,H*0.35,10,'#4a4a5a',0.4);
stipple(500,H*0.4,40,80,'#3a3a4a');
stipple(700,H*0.4,40,80,'#3a3a4a');

// Arch highlight edge (key light)
ctx.strokeStyle=P.stone3;ctx.lineWidth=1.5;ctx.globalAlpha=0.3;
ctx.beginPath();
ctx.moveTo(400,H*0.62);
ctx.bezierCurveTo(415,H*0.33,500,H*0.18,600,H*0.16);
ctx.stroke();
ctx.globalAlpha=1;

// Forge interior
ctx.fillStyle=P.shadow;
ctx.beginPath();
ctx.moveTo(430,H*0.65);
ctx.bezierCurveTo(450,H*0.38,520,H*0.24,600,H*0.22);
ctx.bezierCurveTo(680,H*0.24,750,H*0.38,770,H*0.65);
ctx.closePath();ctx.fill();

// Stone block edges (construction lines)
ctx.strokeStyle=P.stone2;ctx.lineWidth=0.6;ctx.globalAlpha=0.4;
for(let i=0;i<12;i++){
  const bx=430+i*30;
  ctx.beginPath();ctx.moveTo(bx,H*0.65);ctx.lineTo(bx,H*0.45);ctx.stroke();
}
for(let i=0;i<6;i++){
  const by=H*0.35+i*30;
  ctx.beginPath();ctx.moveTo(400,by);ctx.lineTo(800,by);ctx.stroke();
}
ctx.globalAlpha=1;

// === LAYER 6: FURNACE GLOW (the heart) ===
console.log('L6: Furnace');
ctx.globalCompositeOperation='screen';

// Outer glow — large, soft
const fg1=ctx.createRadialGradient(600,H*0.42,0,600,H*0.42,250);
fg1.addColorStop(0,'rgba(255,107,53,0.5)');
fg1.addColorStop(0.3,'rgba(255,69,0,0.2)');
fg1.addColorStop(0.7,'rgba(200,40,0,0.05)');
fg1.addColorStop(1,'transparent');
ctx.fillStyle=fg1;ctx.fillRect(350,H*0.15,500,H*0.55);

// Core — bright, focused
const fg2=ctx.createRadialGradient(600,H*0.4,0,600,H*0.4,100);
fg2.addColorStop(0,'rgba(255,220,50,0.7)');
fg2.addColorStop(0.3,'rgba(255,140,0,0.5)');
fg2.addColorStop(0.7,'rgba(255,69,0,0.2)');
fg2.addColorStop(1,'transparent');
ctx.fillStyle=fg2;ctx.fillRect(500,H*0.3,200,H*0.25);

// Hot spots — painterly dabs
for(let i=0;i<45;i++){
  const hx=570+rand(-35,35);
  const hy=H*0.38+rand(-25,25);
  const color=Math.random()>0.5?P.lava3:P.lava4;
  roundBrush(hx,hy,rand(3,10),color,rand(0,1),rand(0.3,0.7));
}

// Fire embers
for(let i=0;i<30;i++){
  const ex=550+rand(-50,100);
  const ey=H*0.2+rand(-20,60);
  ctx.fillStyle=Math.random()>0.5?P.lava4:P.lava2;
  ctx.globalAlpha=rand(0.2,0.6);
  ctx.beginPath();ctx.arc(ex,ey,rand(0.4,1.2),0,Math.PI*2);ctx.fill();
}
ctx.globalAlpha=1;
ctx.globalCompositeOperation='source-over';

// === LAYER 7: LAVA FLOW ===
console.log('L7: Lava');
ctx.globalCompositeOperation='screen';

// Lava body
ctx.fillStyle=P.lava1;
ctx.globalAlpha=0.4;
ctx.beginPath();
ctx.moveTo(350,H*0.62);
for(let x=350;x<=850;x+=4){
  const n=fbm(x*0.008,1.5,4);
  ctx.lineTo(x,H*0.62+n*12);
}
ctx.lineTo(850,H*0.68);
for(let x=850;x>=350;x-=4){
  const n=fbm(x*0.008+5,1.5,4);
  ctx.lineTo(x,H*0.68+n*8);
}
ctx.closePath();ctx.fill();
ctx.globalAlpha=1;

// Lava surface highlights
for(let i=0;i<40;i++){
  const lx=rand(380,820);
  const ly=H*0.63+rand(-5,10);
  roundBrush(lx,ly,rand(2,8),P.lava3,rand(-0.2,0.2),rand(0.3,0.6));
}

// Lava glow on nearby surfaces
const lgG=ctx.createRadialGradient(600,H*0.63,0,600,H*0.63,150);
lgG.addColorStop(0,'rgba(255,69,0,0.1)');
lgG.addColorStop(1,'transparent');
ctx.fillStyle=lgG;
ctx.fillRect(450,H*0.55,300,H*0.15);
ctx.globalCompositeOperation='source-over';

// === LAYER 8: FOREGROUND ROCKS (form-modeled) ===
console.log('L8: Foreground');

// Left rock mass — complex contour
ctx.fillStyle=P.stone0;
ctx.beginPath();
ctx.moveTo(0,H*0.72);
ctx.bezierCurveTo(60,H*0.68,140,H*0.62,220,H*0.66);
ctx.bezierCurveTo(280,H*0.7,320,H*0.73,360,H*0.76);
ctx.bezierCurveTo(380,H*0.78,400,H*0.82,420,H*0.88);
ctx.lineTo(420,H);ctx.lineTo(0,H);ctx.closePath();ctx.fill();

// Left rock form lighting
const rockG1=ctx.createLinearGradient(100,H*0.64,300,H*0.76);
rockG1.addColorStop(0,P.stone2);rockG1.addColorStop(0.4,P.stone1);rockG1.addColorStop(1,P.stone0);
ctx.fillStyle=rockG1;
ctx.beginPath();
ctx.moveTo(30,H*0.7);
ctx.bezierCurveTo(80,H*0.66,160,H*0.6,240,H*0.65);
ctx.bezierCurveTo(280,H*0.68,310,H*0.72,330,H*0.76);
ctx.lineTo(280,H*0.78);ctx.lineTo(30,H*0.74);ctx.closePath();ctx.fill();

// Left rock surface — hatching + stipple + cross-hatch
hatching(60,H*0.67,200,H*0.74,20,'#3a3a4a',0.5);
stipple(150,H*0.7,50,100,'#3a3a4a');
crossHatch(180,H*0.72,30,25,'#2a2a3a');

// Right rock mass
ctx.fillStyle=P.stone0;
ctx.beginPath();
ctx.moveTo(880,H*0.72);
ctx.bezierCurveTo(950,H*0.64,1050,H*0.58,1150,H*0.62);
ctx.bezierCurveTo(1250,H*0.68,1350,H*0.72,1450,H*0.78);
ctx.bezierCurveTo(1500,H*0.82,1550,H*0.86,1600,H*0.88);
ctx.lineTo(1600,H);ctx.lineTo(880,H);ctx.closePath();ctx.fill();

// Right rock form lighting
const rockG2=ctx.createLinearGradient(1000,H*0.6,1200,H*0.72);
rockG2.addColorStop(0,P.stone2);rockG2.addColorStop(0.4,P.stone1);rockG2.addColorStop(1,P.stone0);
ctx.fillStyle=rockG2;
ctx.beginPath();
ctx.moveTo(920,H*0.7);
ctx.bezierCurveTo(980,H*0.62,1080,H*0.56,1180,H*0.6);
ctx.bezierCurveTo(1250,H*0.65,1320,H*0.7,1380,H*0.75);
ctx.lineTo(1300,H*0.77);ctx.lineTo(920,H*0.73);ctx.closePath();ctx.fill();

hatching(950,H*0.62,1150,H*0.72,22,'#3a3a4a',0.5);
stipple(1100,H*0.67,60,110,'#3a3a4a');
crossHatch(1050,H*0.7,35,30,'#2a2a3a');

// Rock rim light (from furnace)
ctx.globalCompositeOperation='screen';
const rimG=ctx.createLinearGradient(350,H*0.65,400,H*0.75);
rimG.addColorStop(0,'rgba(255,107,53,0.15)');rimG.addColorStop(1,'transparent');
ctx.fillStyle=rimG;
ctx.beginPath();
ctx.moveTo(340,H*0.66);ctx.lineTo(380,H*0.72);ctx.lineTo(360,H*0.76);ctx.lineTo(320,H*0.7);ctx.closePath();ctx.fill();

const rimG2=ctx.createLinearGradient(920,H*0.68,880,H*0.75);
rimG2.addColorStop(0,'rgba(255,107,53,0.1)');rimG2.addColorStop(1,'transparent');
ctx.fillStyle=rimG2;
ctx.beginPath();
ctx.moveTo(920,H*0.68);ctx.lineTo(890,H*0.74);ctx.lineTo(870,H*0.78);ctx.lineTo(910,H*0.72);ctx.closePath();ctx.fill();
ctx.globalCompositeOperation='source-over';

// === LAYER 9: CRYSTAL FORMATIONS ===
console.log('L9: Crystals');
function drawCrystal(cx,cy,h,w,baseColor,hlColor,glowColor){
  // Main crystal body
  ctx.fillStyle=baseColor;
  ctx.beginPath();
  ctx.moveTo(cx,cy);
  ctx.bezierCurveTo(cx-w*0.35,cy-h*0.25,cx-w*0.15,cy-h*0.7,cx-w*0.02,cy-h);
  ctx.bezierCurveTo(cx+w*0.05,cy-h*0.95,cx+w*0.2,cy-h*0.6,cx+w*0.35,cy-h*0.15);
  ctx.bezierCurveTo(cx+w*0.25,cy-h*0.05,cx+w*0.1,cy+h*0.05,cx,cy);
  ctx.closePath();ctx.fill();
  
  // Facet highlight
  ctx.fillStyle=hlColor;ctx.globalAlpha=0.4;
  ctx.beginPath();
  ctx.moveTo(cx-w*0.05,cy-h*0.85);
  ctx.bezierCurveTo(cx-w*0.02,cy-h*0.6,cx+w*0.1,cy-h*0.3,cx+w*0.2,cy-h*0.1);
  ctx.lineTo(cx+w*0.05,cy-h*0.15);
  ctx.bezierCurveTo(cx,cy-h*0.35,cx-w*0.02,cy-h*0.65,cx-w*0.05,cy-h*0.85);
  ctx.closePath();ctx.fill();
  ctx.globalAlpha=1;
  
  // Edge highlight
  ctx.strokeStyle=hlColor;ctx.lineWidth=0.8;ctx.globalAlpha=0.5;
  ctx.beginPath();
  ctx.moveTo(cx,cy);ctx.bezierCurveTo(cx-w*0.35,cy-h*0.25,cx-w*0.15,cy-h*0.7,cx-w*0.02,cy-h);
  ctx.stroke();
  ctx.globalAlpha=1;
}

// Left cluster
drawCrystal(340,H*0.68,90,28,P.crystal0,P.crystal3,P.crystal4);
drawCrystal(365,H*0.7,65,20,P.crystal1,P.crystal2,P.crystal4);
drawCrystal(320,H*0.71,50,16,P.crystal0,P.crystal3,P.crystal4);
drawCrystal(380,H*0.72,35,12,P.crystal1,P.crystal2,P.crystal4);

// Right cluster
drawCrystal(1140,H*0.65,100,30,P.crystal0,P.crystal3,P.crystal4);
drawCrystal(1165,H*0.67,75,22,P.crystal1,P.crystal2,P.crystal4);
drawCrystal(1120,H*0.69,55,18,P.crystal0,P.crystal3,P.crystal4);
drawCrystal(1185,H*0.7,40,14,P.crystal1,P.crystal2,P.crystal4);

// Crystal glow
ctx.globalCompositeOperation='screen';
const cg1=ctx.createRadialGradient(345,H*0.64,0,345,H*0.64,70);
cg1.addColorStop(0,'rgba(123,72,238,0.2)');cg1.addColorStop(1,'transparent');
ctx.fillStyle=cg1;ctx.fillRect(275,H*0.55,140,H*0.2);

const cg2=ctx.createRadialGradient(1145,H*0.62,0,1145,H*0.62,80);
cg2.addColorStop(0,'rgba(123,72,238,0.25)');cg2.addColorStop(1,'transparent');
ctx.fillStyle=cg2;ctx.fillRect(1065,H*0.52,160,H*0.22);
ctx.globalCompositeOperation='source-over';

// === LAYER 10: SMOKE / ATMOSPHERE ===
console.log('L10: Smoke');
ctx.globalAlpha=0.1;
for(let i=0;i<50;i++){
  const sx=rand(480,720);
  const sy=H*0.15+rand(-10,80);
  roundBrush(sx,sy,rand(15,45),P.smoke,rand(-0.6,0.6),rand(0.2,0.5));
}
ctx.globalAlpha=1;

// Rising smoke wisps (dry brush)
for(let i=0;i<15;i++){
  const sx=rand(540,660);
  const sy=H*0.1+rand(0,40);
  dryBrush(sx,sy,rand(30,60),rand(8,15),'rgba(42,16,80,0.3)',rand(-0.8,0.8));
}

// === LAYER 11: KEY LIGHT INTERACTION ===
console.log('L11: Light');
ctx.globalCompositeOperation='screen';

// Furnace light on foreground
const kl1=ctx.createRadialGradient(420,H*0.68,0,420,H*0.68,180);
kl1.addColorStop(0,'rgba(255,107,53,0.1)');kl1.addColorStop(1,'transparent');
ctx.fillStyle=kl1;ctx.fillRect(240,H*0.55,360,H*0.26);

const kl2=ctx.createRadialGradient(880,H*0.68,0,880,H*0.68,160);
kl2.addColorStop(0,'rgba(255,107,53,0.07)');kl2.addColorStop(1,'transparent');
ctx.fillStyle=kl2;ctx.fillRect(720,H*0.55,320,H*0.26);
ctx.globalCompositeOperation='source-over';

// === LAYER 12: ACCENT DETAILS ===
console.log('L12: Accents');
// Sparks near furnace
for(let i=0;i<35;i++){
  const sx=rand(520,680);
  const sy=rand(H*0.15,H*0.38);
  ctx.fillStyle=Math.random()>0.4?P.lava4:P.lava2;
  ctx.globalAlpha=rand(0.2,0.6);
  ctx.beginPath();ctx.arc(sx,sy,rand(0.3,1.0),0,Math.PI*2);ctx.fill();
}
ctx.globalAlpha=1;

// Small crystal fragments scattered
for(let i=0;i<8;i++){
  const fx=rand(400,800);
  const fy=H*0.6+rand(-5,15);
  drawCrystal(fx,fy,rand(8,18),rand(3,6),P.crystal0,P.crystal2,P.crystal4);
}

// === LAYER 13: FOG / DEPTH ===
console.log('L13: Fog');
const fogG=ctx.createLinearGradient(0,H*0.48,0,H*0.62);
fogG.addColorStop(0,'transparent');
fogG.addColorStop(0.5,'rgba(37,21,69,0.12)');
fogG.addColorStop(1,'transparent');
ctx.fillStyle=fogG;ctx.fillRect(0,H*0.48,W,H*0.14);

// === LAYER 14: TONAL ADJUSTMENTS ===
console.log('L14: Tonal');
// Warm shadow tint
ctx.globalCompositeOperation='multiply';
const warmG=ctx.createLinearGradient(0,0,0,H);
warmG.addColorStop(0,'rgba(255,255,255,1)');
warmG.addColorStop(0.5,'rgba(255,242,232,1)');
warmG.addColorStop(1,'rgba(255,235,225,1)');
ctx.fillStyle=warmG;ctx.globalAlpha=0.04;ctx.fillRect(0,0,W,H);
ctx.globalCompositeOperation='source-over';ctx.globalAlpha=1;

// === LAYER 15: GRAIN ===
console.log('L15: Grain');
const imgData=ctx.getImageData(0,0,W,H);
const d=imgData.data;
for(let i=0;i<d.length;i+=4){
  const grain=(Math.random()-0.5)*6;
  d[i]=clamp(d[i]+grain,0,255);
  d[i+1]=clamp(d[i+1]+grain,0,255);
  d[i+2]=clamp(d[i+2]+grain,0,255);
}
ctx.putImageData(imgData,0,0);

// === LAYER 16: VIGNETTE ===
console.log('L16: Vignette');
const vigG=ctx.createRadialGradient(W*0.48,H*0.42,W*0.18,W*0.48,H*0.42,W*0.72);
vigG.addColorStop(0,'transparent');
vigG.addColorStop(0.65,'transparent');
vigG.addColorStop(1,'rgba(8,4,18,0.55)');
ctx.fillStyle=vigG;ctx.fillRect(0,0,W,H);

console.log('L9 Master complete: The Obsidian Forge');
</script>
</body></html>'''

filepath = os.path.join(OUT, "obsidian_forge_painting.html")
with open(filepath, "w") as f:
    f.write(html)

print("L9 Master Pass complete: obsidian_forge_painting.html")
print("Enhancements:")
print("  - 6 brush types: round, flat, dry, hatch, cross-hatch, stipple")
print("  - Multi-ridge mountain range with atmospheric haze")
print("  - Stone block construction lines on forge arch")
print("  - Crystal formations with faceted highlights")
print("  - Rising smoke wisps (dry brush)")
print("  - Rim light interaction on foreground rocks")
print("  - Scattered crystal fragments")
print("  - Warm shadow tonal pass")
print("  - Film grain + vignette")
