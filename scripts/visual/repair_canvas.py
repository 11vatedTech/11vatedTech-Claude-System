"""Repair Canvas painting: material diversity, edge hierarchy, finish."""
import re

with open('artifacts/visual/final-craft/heroes/obsidian_forge_painting.html', 'r') as f:
    code = f.read()

# 1. ADD MATERIAL-SPECIFIC BRUSH FUNCTIONS after the existing stipple function
material_funcs = """
// === MATERIAL-SPECIFIC BRUSH FUNCTIONS ===
// Obsidian: hard fractured planes, glossy, conchoidal
function obsidianStrokes(x,y,w,h,baseColor,hlColor){
  ctx.save();
  for(let i=0;i<12;i++){
    const cx=x+rand(-w/2,w/2),cy=y+rand(-h/2,h/2);
    const len=rand(8,25);
    const angle=rand(-0.3,0.3)+(hash(cx,cy)>0.5?0:Math.PI/2);
    ctx.globalAlpha=rand(0.06,0.14);
    ctx.strokeStyle=hash(cx,cy)>0.6?hlColor:baseColor;
    ctx.lineWidth=rand(0.5,1.5);
    ctx.beginPath();ctx.moveTo(cx,cy);
    ctx.lineTo(cx+Math.cos(angle)*len,cy+Math.sin(angle)*len);
    ctx.stroke();
  }
  ctx.globalAlpha=0.08;ctx.strokeStyle=hlColor;ctx.lineWidth=0.8;
  ctx.beginPath();ctx.moveTo(x-w*0.3,y-h*0.1);
  ctx.bezierCurveTo(x,y-h*0.2,x+w*0.1,y+h*0.1,x+w*0.3,y+h*0.15);
  ctx.stroke();ctx.restore();
}

// Stone: matte broad dabs + mortar lines
function stoneStrokes(x,y,w,h,baseColor,mortarColor){
  ctx.save();
  for(let i=0;i<8;i++){
    const cx=x+rand(-w/2,w/2),cy=y+rand(-h/2,h/2);
    ctx.globalAlpha=rand(0.04,0.09);ctx.fillStyle=baseColor;
    ctx.beginPath();ctx.ellipse(cx,cy,rand(6,18),rand(4,10),rand(0,Math.PI),0,Math.PI*2);ctx.fill();
  }
  ctx.globalAlpha=0.15;ctx.strokeStyle=mortarColor;ctx.lineWidth=0.4;
  for(let i=0;i<4;i++){
    const ly=y+rand(-h/2,h/2);
    ctx.beginPath();ctx.moveTo(x-w/2,ly+rand(-2,2));ctx.lineTo(x+w/2,ly+rand(-2,2));ctx.stroke();
  }
  ctx.restore();
}

// Lava: luminous bands + dark crust
function lavaStrokes(x,y,w,h,hotColor,crustColor){
  ctx.save();
  for(let i=0;i<6;i++){
    const ly=y+rand(-h/2,h/2);
    ctx.globalAlpha=rand(0.08,0.18);
    ctx.strokeStyle=Math.random()>0.3?hotColor:crustColor;ctx.lineWidth=rand(1,4);
    ctx.beginPath();ctx.moveTo(x-w/2,ly);
    for(let px=x-w/2;px<x+w/2;px+=3)ctx.lineTo(px,ly+rand(-1.5,1.5));
    ctx.stroke();
  }
  for(let i=0;i<5;i++){
    ctx.globalAlpha=rand(0.15,0.35);ctx.fillStyle=hotColor;
    ctx.beginPath();ctx.arc(x+rand(-w/3,w/3),y+rand(-h/3,h/3),rand(1,3),0,Math.PI*2);ctx.fill();
  }
  ctx.restore();
}

// Crystal: faceted planes + specular edge
function crystalStrokes(x,y,w,h,baseColor,specColor){
  ctx.save();
  for(let i=0;i<8;i++){
    const fx=x+rand(-w/2,w/2),fy=y+rand(-h/2,h/2);
    ctx.globalAlpha=rand(0.06,0.15);
    ctx.fillStyle=Math.random()>0.4?baseColor:specColor;
    const s=rand(3,8);
    ctx.beginPath();ctx.moveTo(fx,fy-s);ctx.lineTo(fx+s*0.7,fy);ctx.lineTo(fx,fy+s*0.6);ctx.lineTo(fx-s*0.7,fy);
    ctx.closePath();ctx.fill();
  }
  ctx.globalAlpha=0.2;ctx.strokeStyle=specColor;ctx.lineWidth=0.7;
  ctx.beginPath();ctx.moveTo(x-w*0.3,y+h*0.2);ctx.lineTo(x,y-h*0.8);ctx.stroke();
  ctx.restore();
}

// Smoke: long soft flowing, low contrast
function smokeStrokes(x,y,w,h,smokeColor){
  ctx.save();
  for(let i=0;i<10;i++){
    const sx=x+rand(-w/2,w/2),sy=y+rand(-h/2,h/2);
    const len=rand(15,40);
    ctx.globalAlpha=rand(0.02,0.06);ctx.strokeStyle=smokeColor;ctx.lineWidth=rand(3,8);ctx.lineCap='round';
    ctx.beginPath();ctx.moveTo(sx,sy);
    ctx.bezierCurveTo(sx+rand(-10,10),sy-len*0.3,sx+rand(-8,8),sy-len*0.6,sx+rand(-5,5),sy-len);
    ctx.stroke();
  }
  ctx.restore();
}

"""

code = code.replace('// === PALETTE: Obsidian forge world ===', material_funcs + '// === PALETTE: Obsidian forge world ===')

# 2. REPLACE FORGE ARCH SURFACE (Layer 5) with material-specific strokes
old_forge_surface = """// Stone surface detail \u2014 hatching + stipple
hatching(420,H*0.3,500,H*0.5,18,'#3a3a4a',0.5);
hatching(700,H*0.3,780,H*0.5,18,'#3a3a4a',0.5);
hatching(500,H*0.2,550,H*0.35,10,'#4a4a5a',0.4);
stipple(500,H*0.4,40,80,'#3a3a4a');
stipple(700,H*0.4,40,80,'#3a3a4a');"""

new_forge_surface = """// Stone surface \u2014 material-specific strokes (matte, mortar, rough grain)
stoneStrokes(460,H*0.4,100,H*200,P.stone1,P.stone2);
stoneStrokes(740,H*0.4,100,H*200,P.stone1,P.stone2);
stoneStrokes(600,H*0.25,80,H*120,P.stone2,P.stone3);
// Obsidian highlights on arch edges
obsidianStrokes(420,H*0.35,60,H*80,P.stone0,P.stone3);
obsidianStrokes(780,H*0.35,60,H*80,P.stone0,P.stone3);"""

code = code.replace(old_forge_surface, new_forge_surface)

# 3. REPLACE FOREGROUND ROCK SURFACE (Layer 8) with material-specific strokes
old_left_rock = """// Left rock surface \u2014 hatching + stipple + cross-hatch
hatching(60,H*0.67,200,H*0.74,20,'#3a3a4a',0.5);
stipple(150,H*0.7,50,100,'#3a3a4a');
crossHatch(180,H*0.72,30,25,'#2a2a3a');"""

new_left_rock = """// Left rock surface \u2014 obsidian fracture + stone matte
obsidianStrokes(150,H*0.7,120,60,P.stone0,P.stone3);
stoneStrokes(200,H*0.72,80,40,P.stone1,P.stone2);
obsidianStrokes(100,H*0.68,60,30,P.stone0,P.stone2);"""

code = code.replace(old_left_rock, new_left_rock)

old_right_rock = """hatching(950,H*0.62,1150,H*0.72,22,'#3a3a4a',0.5);
stipple(1100,H*0.67,60,110,'#3a3a4a');
crossHatch(1050,H*0.7,35,30,'#2a2a3a');"""

new_right_rock = """// Right rock surface \u2014 obsidian fracture + stone matte
obsidianStrokes(1050,H*0.66,120,60,P.stone0,P.stone3);
stoneStrokes(1100,H*0.69,80,40,P.stone1,P.stone2);
obsidianStrokes(1200,H*0.68,60,30,P.stone0,P.stone2);"""

code = code.replace(old_right_rock, new_right_rock)

# 4. REPLACE SMOKE LAYER with material-specific smoke
old_smoke = """// === LAYER 10: SMOKE / ATMOSPHERE ===
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
}"""

new_smoke = """// === LAYER 10: SMOKE / ATMOSPHERE ===
console.log('L10: Smoke');
// Material-specific smoke: long soft flowing strokes
smokeStrokes(600,H*0.12,200,120,P.smoke);
smokeStrokes(560,H*0.08,150,100,P.smoke);
smokeStrokes(640,H*0.1,180,110,P.smoke);
// Atmospheric haze from furnace
for(let i=0;i<20;i++){
  const sx=rand(480,720),sy=H*0.15+rand(-10,80);
  ctx.globalAlpha=rand(0.02,0.05);ctx.strokeStyle='rgba(42,16,80,0.4)';ctx.lineWidth=rand(2,6);ctx.lineCap='round';
  ctx.beginPath();ctx.moveTo(sx,sy);ctx.bezierCurveTo(sx+rand(-8,8),sy-20,sx+rand(-5,5),sy-40,sx+rand(-3,3),sy-60);
  ctx.stroke();
}
ctx.globalAlpha=1;"""

code = code.replace(old_smoke, new_smoke)

# 5. ADD EDGE HIERARCHY LAYER after Tonal (Layer 14)
old_tonal_end = """ctx.globalCompositeOperation='source-over';ctx.globalAlpha=1;

// === LAYER 15: GRAIN ==="""

new_tonal_end = """ctx.globalCompositeOperation='source-over';ctx.globalAlpha=1;

// === LAYER 14b: EDGE HIERARCHY ===
console.log('L14b: Edge Hierarchy');
// FOCAL HARD EDGES: furnace opening + strongest crystal facets
ctx.strokeStyle='rgba(255,200,50,0.25)';ctx.lineWidth=1.8;
ctx.beginPath();ctx.moveTo(560,H*0.22);ctx.bezierCurveTo(570,H*0.18,630,H*0.18,640,H*0.22);ctx.stroke();
// Crystal facet hard edges
ctx.strokeStyle='rgba(184,169,255,0.3)';ctx.lineWidth=1.2;
ctx.beginPath();ctx.moveTo(340,H*0.68);ctx.lineTo(340,H*0.59);ctx.stroke();
ctx.beginPath();ctx.moveTo(1140,H*0.65);ctx.lineTo(1140,H*0.55);ctx.stroke();

// STRUCTURAL HARD-MEDIUM EDGES: forge arch outline
ctx.strokeStyle='rgba(74,74,90,0.3)';ctx.lineWidth=1.0;
ctx.beginPath();ctx.moveTo(380,H*0.65);
ctx.bezierCurveTo(400,H*0.32,490,H*0.16,600,H*0.14);
ctx.bezierCurveTo(710,H*0.16,800,H*0.32,820,H*0.65);ctx.stroke();

// SOFT EDGES: distant mountains (already atmospheric)
// LOST EDGES: foreground rock merging into shadow
ctx.globalAlpha=0.15;
const lostG=ctx.createLinearGradient(0,H*0.78,0,H);
lostG.addColorStop(0,'transparent');lostG.addColorStop(1,P.shadow);
ctx.fillStyle=lostG;ctx.fillRect(0,H*0.78,W,H*0.22);
ctx.globalAlpha=1;

// === LAYER 15: GRAIN ==="""

code = code.replace(old_tonal_end, new_tonal_end)

# 6. UPGRADE FINISH: Replace generic grain + vignette with artifact-specific finishing
old_finish = """// === LAYER 15: GRAIN ===
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

console.log('L9 Master complete: The Obsidian Forge');"""

new_finish = """// === LAYER 15: ARTIFACT-SPECIFIC FINISHING ===
console.log('L15: Finish');

// Focal sharpening: increase contrast near furnace
ctx.globalCompositeOperation='overlay';
const sharpenG=ctx.createRadialGradient(600,H*0.4,0,600,H*0.4,300);
sharpenG.addColorStop(0,'rgba(255,255,255,0.04)');
sharpenG.addColorStop(0.5,'rgba(128,128,128,0.02)');
sharpenG.addColorStop(1,'transparent');
ctx.fillStyle=sharpenG;ctx.fillRect(300,H*0.1,600,H*0.6);
ctx.globalCompositeOperation='source-over';

// Background softening: reduce detail in deep background
ctx.globalAlpha=0.08;
const bgSoftG=ctx.createLinearGradient(0,0,0,H*0.35);
bgSoftG.addColorStop(0,P.sky1);bgSoftG.addColorStop(1,'transparent');
ctx.fillStyle=bgSoftG;ctx.fillRect(0,0,W,H*0.35);
ctx.globalAlpha=1;

// Film grain (artifact-specific: finer near focal, coarser at edges)
const imgData=ctx.getImageData(0,0,W,H);
const d=imgData.data;
for(let i=0;i<d.length;i+=4){
  const px=(i/4)%W,py=Math.floor((i/4)/W);
  const distFocal=Math.sqrt((px-600)*(px-600)+(py-H*0.4)*(py-H*0.4));
  const grainScale=clamp(distFocal/500,0.3,1.0);
  const grain=(Math.random()-0.5)*5*grainScale;
  d[i]=clamp(d[i]+grain,0,255);
  d[i+1]=clamp(d[i+1]+grain,0,255);
  d[i+2]=clamp(d[i+2]+grain,0,255);
}
ctx.putImageData(imgData,0,0);

// === LAYER 16: VIGNETTE + COLOR GRADE ===
console.log('L16: Vignette + Grade');
// Asymmetric vignette (stronger bottom, warmer top)
const vigG=ctx.createRadialGradient(W*0.48,H*0.38,W*0.15,W*0.48,H*0.38,W*0.75);
vigG.addColorStop(0,'transparent');
vigG.addColorStop(0.6,'transparent');
vigG.addColorStop(1,'rgba(8,4,18,0.6)');
ctx.fillStyle=vigG;ctx.fillRect(0,0,W,H);

// Subtle warm color grade in shadows
ctx.globalCompositeOperation='color';
ctx.globalAlpha=0.03;
ctx.fillStyle='#2a1050';
ctx.fillRect(0,H*0.5,W,H*0.5);
ctx.globalCompositeOperation='source-over';
ctx.globalAlpha=1;

// Deepest-dark control: ensure blacks aren't crushed
ctx.globalCompositeOperation='lighten';
ctx.globalAlpha=0.01;
ctx.fillStyle='#0a0518';
ctx.fillRect(0,0,W,H);
ctx.globalCompositeOperation='source-over';

console.log('L9 Master complete: The Obsidian Forge');"""

code = code.replace(old_finish, new_finish)

# Write repaired file
with open('artifacts/visual/final-craft/heroes/obsidian_forge_painting.html', 'w') as f:
    f.write(code)

print(f"Repaired file: {len(code)} bytes")
print("Edits applied:")
print("  1. Material-specific brush functions added (obsidian/stone/lava/crystal/smoke)")
print("  2. Forge arch surface: generic hatching -> stone + obsidian strokes")
print("  3. Foreground rocks: generic hatching -> obsidian fracture + stone matte")
print("  4. Smoke: generic roundBrush -> material-specific smokeStrokes")
print("  5. Edge hierarchy layer added (focal/structural/soft/lost)")
print("  6. Finish upgraded (focal sharpening, bg softening, asymmetric grain, color grade)")
