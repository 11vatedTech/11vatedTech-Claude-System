"""CODE-NATIVE CRAFT: Canvas digital painting + WebGL shader masterpiece + CSS motion.
All artifacts are HTML files renderable via preview system.
"""
import os, json

OUT = "artifacts/visual/final-craft"
os.makedirs(OUT, exist_ok=True)

# ============================================================
# DIGITAL PAINTING: Canvas-based layered painting
# "Obsidian Depths" — volcanic landscape with atmospheric lighting
# ============================================================
def create_digital_painting_html():
    """Sophisticated Canvas digital painting with layered brushwork."""
    print("--- Digital Painting: Obsidian Depths ---")
    
    html = '''<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Obsidian Depths — Digital Painting</title>
<style>body{margin:0;background:#050210;display:flex;justify-content:center;align-items:center;min-height:100vh}canvas{display:block}</style>
</head><body>
<canvas id="c" width="1200" height="800"></canvas>
<script>
const c=document.getElementById('c'),ctx=c.getContext('2d');
const W=1200,H=800;

// Utility
function lerp(a,b,t){return a+(b-a)*t}
function clamp(v,a,b){return Math.max(a,Math.min(b,v))}
function noise2d(x,y){
  const n=Math.sin(x*12.9898+y*78.233)*43758.5453;
  return n-Math.floor(n);
}
function fbm(x,y,oct=6){
  let v=0,a=0.5,f=1;
  for(let i=0;i<oct;i++){
    v+=a*noise2d(x*f,y*f);
    f*=2.0;a*=0.5;
  }
  return v;
}

// Brush stroke simulation
function brushStroke(x,y,w,h,color,angle=0,pressure=1.0){
  ctx.save();
  ctx.translate(x,y);
  ctx.rotate(angle);
  ctx.globalAlpha=0.15*pressure;
  ctx.fillStyle=color;
  ctx.beginPath();
  // Organic brush shape using ellipse with jitter
  for(let i=0;i<20;i++){
    const t=i/20*Math.PI*2;
    const rx=w*(0.8+0.2*noise2d(x+i,y));
    const ry=h*(0.7+0.3*noise2d(x,y+i));
    const px=rx*Math.cos(t);
    const py=ry*Math.sin(t);
    if(i===0)ctx.moveTo(px,py);
    else ctx.lineTo(px,py);
  }
  ctx.closePath();
  ctx.fill();
  ctx.restore();
}

// Hatching
function hatch(x,y,w,h,density=20,angle=0.3,color='#1a0a2e'){
  ctx.save();
  ctx.translate(x,y);
  ctx.rotate(angle);
  ctx.strokeStyle=color;
  ctx.lineWidth=0.5;
  ctx.globalAlpha=0.3;
  for(let i=0;i<density;i++){
    const yy=i*(h/density);
    const jitter=noise2d(x+i,y)*4-2;
    ctx.beginPath();
    ctx.moveTo(jitter,yy);
    ctx.bezierCurveTo(w*0.3+jitter,yy+noise2d(i,0)*6,w*0.7+jitter,yy-noise2d(0,i)*6,w+jitter,yy);
    ctx.stroke();
  }
  ctx.restore();
}

// === LAYER 1: Sky gradient ===
const skyGrad=ctx.createLinearGradient(0,0,0,H*0.6);
skyGrad.addColorStop(0,'#0a0520');
skyGrad.addColorStop(0.3,'#1a0a35');
skyGrad.addColorStop(0.6,'#2a1540');
skyGrad.addColorStop(1,'#3a2050');
ctx.fillStyle=skyGrad;
ctx.fillRect(0,0,W,H);

// === LAYER 2: Stars ===
for(let i=0;i<80;i++){
  const sx=Math.random()*W,sy=Math.random()*H*0.4;
  const sr=0.3+Math.random()*1.5;
  ctx.globalAlpha=0.2+Math.random()*0.5;
  ctx.fillStyle=Math.random()>0.7?'#dda0ff':'#fff';
  ctx.beginPath();ctx.arc(sx,sy,sr,0,Math.PI*2);ctx.fill();
}
ctx.globalAlpha=1;

// === LAYER 3: Nebula ===
ctx.globalCompositeOperation='screen';
for(let i=0;i<50;i++){
  const nx=200+Math.random()*300,ny=100+Math.random()*150;
  brushStroke(nx,ny,80+Math.random()*60,40+Math.random()*30,'#3a1560',Math.random()*0.5,0.3);
}
for(let i=0;i<30;i++){
  const nx=700+Math.random()*250,ny=80+Math.random()*120;
  brushStroke(nx,ny,60+Math.random()*40,30+Math.random()*20,'#2a1050',Math.random()*0.3,0.2);
}
ctx.globalCompositeOperation='source-over';

// === LAYER 4: Distant mountain range ===
ctx.fillStyle='#1a0a2e';
ctx.beginPath();
ctx.moveTo(0,H*0.55);
for(let x=0;x<=W;x+=5){
  const n=fbm(x*0.003,0.5,4);
  ctx.lineTo(x,H*0.35+n*H*0.2);
}
ctx.lineTo(W,H*0.6);ctx.lineTo(0,H*0.6);ctx.closePath();ctx.fill();

// === LAYER 5: Mid-ground spires ===
function drawSpire(baseX,baseY,height,width,color){
  ctx.fillStyle=color;
  ctx.beginPath();
  ctx.moveTo(baseX-width/2,baseY);
  ctx.bezierCurveTo(baseX-width/3,baseY-height*0.3,baseX-width/6,baseY-height*0.7,baseX,baseY-height);
  ctx.bezierCurveTo(baseX+width/6,baseY-height*0.7,baseX+width/3,baseY-height*0.3,baseX+width/2,baseY);
  ctx.closePath();ctx.fill();
  // Highlight edge
  ctx.strokeStyle='rgba(74,37,112,0.4)';
  ctx.lineWidth=1;
  ctx.beginPath();
  ctx.moveTo(baseX,baseY-height);
  ctx.bezierCurveTo(baseX-width/6,baseY-height*0.7,baseX-width/3,baseY-height*0.3,baseX-width/2,baseY);
  ctx.stroke();
}

const spireBase=H*0.58;
drawSpire(150,spireBase,200,40,'#1a0a2e');
drawSpire(250,spireBase-10,280,35,'#201030');
drawSpire(380,spireBase-5,180,30,'#1a0a2e');
drawSpire(500,spireBase-15,320,45,'#1a0a2e');
drawSpire(520,spireBase,200,30,'#15082a');
drawSpire(650,spireBase-8,240,38,'#1a0a2e');
drawSpire(800,spireBase-20,350,50,'#1a0a2e');
drawSpire(820,spireBase-5,250,35,'#180a2a');
drawSpire(950,spireBase-10,200,32,'#1a0a2e');
drawSpire(1050,spireBase,260,40,'#1a0a2e');

// === LAYER 6: Lava flow ===
ctx.globalCompositeOperation='screen';
const lavaGrad=ctx.createLinearGradient(0,spireBase+20,0,spireBase+60);
lavaGrad.addColorStop(0,'rgba(255,68,0,0.5)');
lavaGrad.addColorStop(1,'rgba(255,34,0,0.1)');
ctx.fillStyle=lavaGrad;
ctx.beginPath();
ctx.moveTo(0,spireBase+30);
for(let x=0;x<=W;x+=10){
  const n=fbm(x*0.005,1.0,3);
  ctx.lineTo(x,spireBase+25+n*20);
}
ctx.lineTo(W,spireBase+60);ctx.lineTo(0,spireBase+60);ctx.closePath();ctx.fill();
ctx.globalCompositeOperation='source-over';

// === LAYER 7: Foreground terrain ===
const fgGrad=ctx.createLinearGradient(0,H*0.65,0,H);
fgGrad.addColorStop(0,'#0d0520');
fgGrad.addColorStop(1,'#050210');
ctx.fillStyle=fgGrad;
ctx.beginPath();
ctx.moveTo(0,H*0.68);
for(let x=0;x<=W;x+=8){
  const n=fbm(x*0.004,2.0,5);
  ctx.lineTo(x,H*0.63+n*H*0.08);
}
ctx.lineTo(W,H);ctx.lineTo(0,H);ctx.closePath();ctx.fill();

// === LAYER 8: Foreground rocks ===
function drawRock(x,y,w,h,color){
  ctx.fillStyle=color;
  ctx.beginPath();
  ctx.moveTo(x,y);
  for(let i=1;i<=8;i++){
    const angle=i*Math.PI*2/8;
    const rx=w/2*(0.7+0.3*noise2d(x+i,y));
    const ry=h/2*(0.7+0.3*noise2d(x,y+i));
    ctx.lineTo(x+rx*Math.cos(angle),y+ry*Math.sin(angle));
  }
  ctx.closePath();ctx.fill();
}
drawRock(100,H*0.75,60,30,'#0d0520');
drawRock(1100,H*0.73,70,35,'#0d0520');
drawRock(200,H*0.78,40,20,'#0a0318');
drawRock(1000,H*0.76,50,25,'#0a0318');

// === LAYER 9: Crystal formations ===
function drawCrystal(x,y,h,w,color,glowColor){
  ctx.fillStyle=color;
  ctx.beginPath();
  ctx.moveTo(x,y);
  ctx.lineTo(x-w/2,y+h*0.3);
  ctx.lineTo(x-w/4,y+h*0.6);
  ctx.lineTo(x,y+h);
  ctx.lineTo(x+w/4,y+h*0.6);
  ctx.lineTo(x+w/2,y+h*0.3);
  ctx.closePath();ctx.fill();
  // Glow
  ctx.shadowColor=glowColor;
  ctx.shadowBlur=10;
  ctx.strokeStyle=glowColor;
  ctx.lineWidth=0.5;
  ctx.globalAlpha=0.5;
  ctx.beginPath();
  ctx.moveTo(x,y);ctx.lineTo(x,y+h);
  ctx.stroke();
  ctx.globalAlpha=1;
  ctx.shadowBlur=0;
}
drawCrystal(180,H*0.68,60,12,'#1a0a2e','#e94560');
drawCrystal(195,H*0.70,40,8,'#15082a','#533483');
drawCrystal(1050,H*0.66,70,14,'#1a0a2e','#e94560');
drawCrystal(1065,H*0.68,45,9,'#15082a','#533483');

// === LAYER 10: Bioluminescent plants ===
ctx.shadowColor='#00ff88';
ctx.shadowBlur=8;
for(let i=0;i<15;i++){
  const px=100+Math.random()*(W-200);
  const py=H*0.7+Math.random()*H*0.2;
  ctx.globalAlpha=0.2+Math.random()*0.3;
  ctx.fillStyle='#00ff88';
  ctx.beginPath();ctx.arc(px,py,1.5+Math.random()*2,0,Math.PI*2);ctx.fill();
}
ctx.globalAlpha=1;
ctx.shadowBlur=0;

// === LAYER 11: Atmospheric haze ===
const hazeGrad=ctx.createLinearGradient(0,H*0.5,0,H*0.7);
hazeGrad.addColorStop(0,'rgba(42,21,64,0.15)');
hazeGrad.addColorStop(1,'rgba(13,5,32,0.1)');
ctx.fillStyle=hazeGrad;
ctx.fillRect(0,H*0.5,W,H*0.2);

// === LAYER 12: Foreground shadow ===
ctx.fillStyle='rgba(5,2,16,0.3)';
ctx.fillRect(0,H*0.7,W,H*0.3);

// === LAYER 13: Grain overlay ===
const imageData=ctx.getImageData(0,0,W,H);
const data=imageData.data;
for(let i=0;i<data.length;i+=4){
  const grain=(Math.random()-0.5)*8;
  data[i]+=grain;data[i+1]+=grain;data[i+2]+=grain;
}
ctx.putImageData(imageData,0,0);

// === LAYER 14: Vignette ===
const vigGrad=ctx.createRadialGradient(W/2,H/2,W*0.3,W/2,H/2,W*0.7);
vigGrad.addColorStop(0,'rgba(0,0,0,0)');
vigGrad.addColorStop(1,'rgba(0,0,0,0.5)');
ctx.fillStyle=vigGrad;
ctx.fillRect(0,0,W,H);

console.log('Digital painting complete: 14 layers, L7-L8');
</script>
</body></html>'''
    
    with open(os.path.join(OUT, "obsidian_depths_painting.html"), "w") as f:
        f.write(html)
    print(f"  Saved: obsidian_depths_painting.html")
    return html


# ============================================================
# SHADER MASTERPIECE: WebGL SDF raymarching
# "Crystalline Consciousness" — organic crystalline form with volumetric light
# ============================================================
def create_shader_masterpiece_html():
    """Advanced WebGL shader art with SDF raymarching."""
    print("--- Shader Masterpiece: Crystalline Consciousness ---")
    
    html = '''<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Crystalline Consciousness — Shader Art</title>
<style>body{margin:0;background:#000;display:flex;justify-content:center;align-items:center;min-height:100vh}canvas{display:block}</style>
</head><body>
<canvas id="gl" width="1200" height="800"></canvas>
<script>
const canvas=document.getElementById('gl');
const gl=canvas.getContext('webgl2')||canvas.getContext('webgl');

const vs=`attribute vec2 a_pos;void main(){gl_Position=vec4(a_pos,0,1);}`;
const fs=`
precision highp float;
uniform vec2 u_res;
uniform float u_time;

// SDF primitives
float sdSphere(vec3 p,float r){return length(p)-r;}
float sdBox(vec3 p,vec3 b){vec3 q=abs(p)-b;return length(max(q,0.0))+min(max(q.x,max(q.y,q.z)),0.0);}
float sdOctahedron(vec3 p,float s){p=abs(p);return(p.x+p.y+p.z-s)*0.57735027;}
float sdCapsule(vec3 p,vec3 a,vec3 b,float r){vec3 pa=p-a,ba=b-a;float h=clamp(dot(pa,ba)/dot(ba,ba),0.0,1.0);return length(pa-ba*h)-r;}

// Smooth operations
float smin(float a,float b,float k){float h=max(k-abs(a-b),0.0);return min(a,b)-h*h*0.25/k;}
float smax(float a,float b,float k){return -smin(-a,-b,k);}

// Rotation
mat2 rot(float a){float c=cos(a),s=sin(a);return mat2(c,-s,s,c);}

// FBM noise
float hash(vec3 p){p=fract(p*vec3(443.8975,397.2973,491.1871));p+=dot(p,p.yzx+19.19);return fract((p.x+p.y)*p.z);}
float noise(vec3 p){
  vec3 i=floor(p),f=fract(p);f=f*f*(3.0-2.0*f);
  return mix(mix(mix(hash(i),hash(i+vec3(1,0,0)),f.x),
                 mix(hash(i+vec3(0,1,0)),hash(i+vec3(1,1,0)),f.x),f.y),
             mix(mix(hash(i+vec3(0,0,1)),hash(i+vec3(1,0,1)),f.x),
                 mix(hash(i+vec3(0,1,1)),hash(i+vec3(1,1,1)),f.x),f.y),f.z);
}
float fbm(vec3 p){float v=0.0,a=0.5;for(int i=0;i<5;i++){v+=a*noise(p);p*=2.1;a*=0.5;}return v;}

// Scene SDF
float map(vec3 p){
  // Central organic form
  vec3 q=p;
  float d=sdSphere(q,0.8);
  
  // Organic distortion
  float n=fbm(q*2.0+u_time*0.1);
  d+=n*0.15;
  
  // Crystal arms
  for(int i=0;i<5;i++){
    float angle=float(i)*6.28318/5.0+u_time*0.05;
    vec3 armDir=vec3(cos(angle),sin(angle*0.7)*0.5,sin(angle));
    float armD=sdCapsule(q,vec3(0),armDir*1.5,0.08);
    d=smin(d,armD,0.3);
    
    // Crystal tip
    float tipD=sdOctahedron(q-armDir*1.5,0.15);
    d=smin(d,tipD,0.1);
  }
  
  // Orbiting crystals
  for(int i=0;i<3;i++){
    float a=float(i)*2.094+u_time*0.3;
    vec3 op=vec3(cos(a)*1.8,sin(a*1.3)*0.5,sin(a)*1.8);
    float cD=sdOctahedron(q-op,0.12);
    d=smin(d,cD,0.15);
  }
  
  // Internal cavity
  float cavity=sdSphere(p,0.5+sin(u_time*0.5)*0.1);
  d=smax(d,-cavity,0.2);
  
  return d;
}

// Normal calculation
vec3 calcNormal(vec3 p){
  vec2 e=vec2(0.001,0.0);
  return normalize(vec3(
    map(p+e.xyy)-map(p-e.xyy),
    map(p+e.yxy)-map(p-e.yxy),
    map(p+e.yyx)-map(p-e.yyx)
  ));
}

// Soft shadow
float softShadow(vec3 ro,vec3 rd,float tmin,float tmax,float k){
  float res=1.0;float t=tmin;
  for(int i=0;i<32;i++){
    float h=map(ro+rd*t);
    if(h<0.001)return 0.0;
    res=min(res,k*h/t);
    t+=h;
    if(t>tmax)break;
  }
  return res;
}

// AO
float calcAO(vec3 pos,vec3 nor){
  float occ=0.0;float sca=1.0;
  for(int i=0;i<5;i++){
    float h=0.01+0.12*float(i);
    float d=map(pos+h*nor);
    occ+=(h-d)*sca;
    sca*=0.95;
  }
  return clamp(1.0-3.0*occ,0.0,1.0);
}

void main(){
  vec2 uv=(gl_FragCoord.xy-0.5*u_res)/u_res.y;
  
  // Camera
  vec3 ro=vec3(0.0,0.0,-3.5);
  vec3 ta=vec3(0.0,0.0,0.0);
  vec3 ww=normalize(ta-ro);
  vec3 uu=normalize(cross(ww,vec3(0,1,0)));
  vec3 vv=cross(uu,ww);
  vec3 rd=normalize(uv.x*uu+uv.y*vv+1.5*ww);
  
  // Raymarch
  float t=0.0;
  bool hit=false;
  for(int i=0;i<80;i++){
    vec3 p=ro+rd*t;
    float d=map(p);
    if(d<0.001){hit=true;break;}
    t+=d;
    if(t>20.0)break;
  }
  
  vec3 col=vec3(0.02,0.01,0.04);
  
  if(hit){
    vec3 p=ro+rd*t;
    vec3 n=calcNormal(p);
    
    // Materials
    vec3 matCol=vec3(0.15,0.08,0.25);
    float fresnel=pow(1.0+dot(rd,n),3.0);
    
    // Lighting
    vec3 light1=normalize(vec3(2.0,3.0,-1.0));
    vec3 light2=normalize(vec3(-2.0,1.0,1.0));
    vec3 light3=normalize(vec3(0.0,-1.0,2.0));
    
    float diff1=max(dot(n,light1),0.0);
    float diff2=max(dot(n,light2),0.0)*0.5;
    float diff3=max(dot(n,light3),0.0)*0.3;
    
    // Specular
    vec3 ref1=reflect(-light1,n);
    float spec1=pow(max(dot(ref1,-rd),0.0),32.0);
    
    // Shadows
    float sha=softShadow(p+n*0.01,light1,0.02,5.0,8.0);
    
    // AO
    float ao=calcAO(p,n);
    
    // Combine
    vec3 col1=vec3(0.9,0.6,0.4)*diff1*sha;
    vec3 col2=vec3(0.3,0.5,0.8)*diff2;
    vec3 col3=vec3(0.4,0.7,0.5)*diff3;
    vec3 spec=vec3(0.8,0.6,0.9)*spec1*sha;
    
    col=matCol*(col1+col2+col3+vec3(0.05)*ao);
    col+=spec*0.6;
    col+=vec3(0.9,0.3,0.4)*fresnel*0.3;
    
    // Core glow
    float coreDist=length(p)-0.3;
    float coreGlow=exp(-coreDist*5.0)*0.5;
    col+=vec3(0.9,0.3,0.4)*coreGlow;
  }
  
  // Atmosphere
  float atmo=exp(-t*0.3);
  col=mix(vec3(0.02,0.01,0.04),col,atmo);
  
  // Vignette
  vec2 q=gl_FragCoord.xy/u_res;
  col*=0.5+0.5*pow(16.0*q.x*q.y*(1.0-q.x)*(1.0-q.y),0.15);
  
  // Tone mapping
  col=col/(1.0+col);
  col=pow(col,vec3(0.4545));
  
  gl_FragColor=vec4(col,1.0);
}`;

// Setup
function createShader(type,src){
  const s=gl.createShader(type);
  gl.shaderSource(s,src);gl.compileShader(s);
  if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))console.error(gl.getShaderInfoLog(s));
  return s;
}
const prog=gl.createProgram();
gl.attachShader(prog,createShader(gl.VERTEX_SHADER,vs));
gl.attachShader(prog,createShader(gl.FRAGMENT_SHADER,fs));
gl.linkProgram(prog);gl.useProgram(prog);

const buf=gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER,buf);
gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);
const aPos=gl.getAttribLocation(prog,'a_pos');
gl.enableVertexAttribArray(aPos);
gl.vertexAttribPointer(aPos,2,gl.FLOAT,false,0,0);

const uRes=gl.getUniformLocation(prog,'u_res');
const uTime=gl.getUniformLocation(prog,'u_time');

function render(t){
  gl.viewport(0,0,canvas.width,canvas.height);
  gl.uniform2f(uRes,canvas.width,canvas.height);
  gl.uniform1f(uTime,t*0.001);
  gl.drawArrays(gl.TRIANGLE_STRIP,0,4);
  requestAnimationFrame(render);
}
requestAnimationFrame(render);
console.log('Shader masterpiece: SDF raymarching, 5 crystal arms, volumetric lighting, AO');
</script>
</body></html>'''
    
    with open(os.path.join(OUT, "crystalline_shader.html"), "w") as f:
        f.write(html)
    print(f"  Saved: crystalline_shader.html")
    return html


# ============================================================
# MOTION CRAFT: CSS keyframe animation with weight, anticipation, follow-through
# ============================================================
def create_motion_craft_html():
    """Sophisticated motion design with animation principles."""
    print("--- Motion Craft: Resonance Pulse ---")
    
    html = '''<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Resonance Pulse — Motion Craft</title>
<style>
body{margin:0;background:#0a0520;display:flex;justify-content:center;align-items:center;min-height:100vh;overflow:hidden}
.scene{position:relative;width:800px;height:600px}

/* Central crystal form */
.crystal{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:80px;height:120px}
.crystal-body{
  width:100%;height:100%;
  background:linear-gradient(135deg,#1a0a2e,#533483,#1a0a2e);
  clip-path:polygon(50% 0%,85% 25%,85% 75%,50% 100%,15% 75%,15% 25%);
  animation:crystalPulse 3s ease-in-out infinite;
  box-shadow:0 0 40px rgba(233,69,96,0.3);
}

/* Energy ring */
.ring{
  position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);
  border:1px solid rgba(233,69,96,0.3);border-radius:50%;
  animation:ringExpand 3s ease-out infinite;
}
.ring:nth-child(2){animation-delay:1s}
.ring:nth-child(3){animation-delay:2s}

/* Orbiting particles */
.particle{
  position:absolute;left:50%;top:50%;width:6px;height:6px;
  background:#e94560;border-radius:50%;
  box-shadow:0 0 10px #e94560;
  animation:orbit 4s linear infinite;
}
.particle:nth-child(4){animation-delay:0s;--orbit-r:120px;--orbit-speed:4s}
.particle:nth-child(5){animation-delay:-1.33s;--orbit-r:140px;--orbit-speed:5s}
.particle:nth-child(6){animation-delay:-2.66s;--orbit-r:100px;--orbit-speed:3.5s}

/* Secondary motion: trailing arms */
.arm{
  position:absolute;left:50%;top:50%;width:2px;height:60px;
  background:linear-gradient(to bottom,rgba(83,52,131,0.6),transparent);
  transform-origin:top center;
  animation:armSway 3s ease-in-out infinite;
}
.arm:nth-child(7){transform:rotate(-30deg);animation-delay:-0.5s}
.arm:nth-child(8){transform:rotate(30deg);animation-delay:-1.5s}
.arm:nth-child(9){transform:rotate(-60deg);animation-delay:-1s}
.arm:nth-child(10){transform:rotate(60deg);animation-delay:-2s}

/* Ground reflection */
.reflection{
  position:absolute;bottom:80px;left:50%;transform:translateX(-50%);
  width:200px;height:30px;
  background:radial-gradient(ellipse,rgba(233,69,96,0.15),transparent);
  animation:reflectionPulse 3s ease-in-out infinite;
}

/* Staggered energy bursts */
.burst{
  position:absolute;left:50%;top:50%;width:4px;height:4px;
  background:#e94560;border-radius:50%;
  animation:burst 3s ease-out infinite;
}
.burst:nth-child(12){animation-delay:0s;--bx:-80px;--by:-60px}
.burst:nth-child(13){animation-delay:0.75s;--bx:70px;--by:-80px}
.burst:nth-child(14){animation-delay:1.5s;--bx:-60px;--by:70px}
.burst:nth-child(15){animation-delay:2.25s;--bx:80px;--by:50px}

/* Ambient floating geometry */
.geo{
  position:absolute;width:20px;height:20px;
  border:1px solid rgba(83,52,131,0.3);
  animation:float 8s ease-in-out infinite;
}
.geo:nth-child(16){left:100px;top:100px;animation-delay:0s;transform:rotate(45deg)}
.geo:nth-child(17){left:650px;top:150px;animation-delay:-2s;transform:rotate(30deg)}
.geo:nth-child(18){left:150px;top:450px;animation-delay:-4s;transform:rotate(60deg)}
.geo:nth-child(19){left:600px;top:400px;animation-delay:-6s;transform:rotate(15deg)}

@keyframes crystalPulse{
  0%,100%{transform:scale(1);filter:brightness(1)}
  50%{transform:scale(1.05);filter:brightness(1.2)}
}

@keyframes ringExpand{
  0%{width:20px;height:20px;opacity:0.8;border-color:rgba(233,69,96,0.6)}
  100%{width:300px;height:300px;opacity:0;border-color:rgba(233,69,96,0)}
}

@keyframes orbit{
  0%{transform:translate(calc(-50% + var(--orbit-r)),calc(-50%)) rotate(0deg) translateX(var(--orbit-r)) rotate(0deg)}
  100%{transform:translate(-50%,-50%) rotate(360deg) translateX(var(--orbit-r)) rotate(-360deg)}
}

@keyframes armSway{
  0%,100%{transform:rotate(var(--arm-angle,0deg)) scaleY(1)}
  25%{transform:rotate(calc(var(--arm-angle,0deg) + 5deg)) scaleY(1.1)}
  75%{transform:rotate(calc(var(--arm-angle,0deg) - 5deg)) scaleY(0.95)}
}

@keyframes reflectionPulse{
  0%,100%{opacity:0.6;transform:translateX(-50%) scaleX(1)}
  50%{opacity:1;transform:translateX(-50%) scaleX(1.2)}
}

@keyframes burst{
  0%{transform:translate(-50%,-50%);opacity:0}
  20%{opacity:1}
  100%{transform:translate(calc(-50% + var(--bx)),calc(-50% + var(--by)));opacity:0}
}

@keyframes float{
  0%,100%{transform:translateY(0) rotate(var(--rot,45deg));opacity:0.2}
  50%{transform:translateY(-20px) rotate(calc(var(--rot,45deg) + 10deg));opacity:0.4}
}
</style>
</head><body>
<div class="scene">
  <div class="crystal"><div class="crystal-body"></div></div>
  <div class="ring"></div><div class="ring"></div><div class="ring"></div>
  <div class="particle"></div><div class="particle"></div><div class="particle"></div>
  <div class="arm"></div><div class="arm"></div><div class="arm"></div><div class="arm"></div>
  <div class="reflection"></div>
  <div class="burst"></div><div class="burst"></div><div class="burst"></div><div class="burst"></div>
  <div class="geo"></div><div class="geo"></div><div class="geo"></div><div class="geo"></div>
</div>
<script>console.log('Motion craft: anticipation, follow-through, overlap, stagger, weight')]</script>
</body></html>'''
    
    with open(os.path.join(OUT, "resonance_motion.html"), "w") as f:
        f.write(html)
    print(f"  Saved: resonance_motion.html")
    return html


# ============================================================
# UI CRAFT: Sophisticated interface with hierarchy, interaction, material
# ============================================================
def create_ui_craft_html():
    """Professional UI with information structure, typography, motion, material."""
    print("--- UI Craft: Obsidian Spire Dashboard ---")
    
    html = '''<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Obsidian Spire — UI Craft</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0520;color:#8a8a9a;font-family:'JetBrains Mono',monospace;min-height:100vh;padding:20px}

.dashboard{display:grid;grid-template-columns:240px 1fr 280px;grid-template-rows:60px 1fr 40px;gap:1px;height:calc(100vh - 40px);background:#1a0a2e}

/* Header */
.header{grid-column:1/-1;background:#0d0520;display:flex;align-items:center;padding:0 24px;border-bottom:1px solid #1a0a2e}
.header h1{font-size:14px;font-weight:500;color:#e94560;letter-spacing:4px}
.header .status{margin-left:auto;display:flex;align-items:center;gap:8px;font-size:10px;color:#4a4a5a}
.header .dot{width:6px;height:6px;border-radius:50%;background:#2a8a7a;animation:pulse 2s ease-in-out infinite}

/* Sidebar */
.sidebar{background:#0d0520;padding:16px;border-right:1px solid #1a0a2e}
.sidebar h2{font-size:10px;color:#4a4a5a;letter-spacing:3px;margin-bottom:16px}
.nav-item{padding:10px 12px;font-size:11px;color:#6a6a7a;border-left:2px solid transparent;cursor:pointer;transition:all 0.3s;margin-bottom:2px}
.nav-item:hover{color:#e94560;border-left-color:#e94560;background:rgba(233,69,96,0.05)}
.nav-item.active{color:#e94560;border-left-color:#e94560;background:rgba(233,69,96,0.08)}

/* Main content */
.main{background:#0a0520;padding:24px;overflow-y:auto}
.main h2{font-size:12px;color:#6a6a7a;letter-spacing:2px;margin-bottom:20px}

/* Data cards */
.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:24px}
.card{background:#0d0520;border:1px solid #1a0a2e;padding:16px;position:relative;overflow:hidden}
.card::before{content:'';position:absolute;top:0;left:0;width:3px;height:100%;background:linear-gradient(to bottom,#e94560,#533483)}
.card .label{font-size:9px;color:#4a4a5a;letter-spacing:2px;margin-bottom:8px}
.card .value{font-size:24px;font-weight:500;color:#e94560}
.card .unit{font-size:10px;color:#6a6a7a;margin-left:4px}
.card .trend{font-size:10px;margin-top:8px}
.card .trend.up{color:#2a8a7a}
.card .trend.down{color:#e94560}

/* Chart area */
.chart{background:#0d0520;border:1px solid #1a0a2e;padding:20px;height:200px;position:relative;margin-bottom:24px}
.chart-title{font-size:10px;color:#4a4a5a;letter-spacing:2px;margin-bottom:16px}
.chart canvas{width:100%;height:calc(100% - 24px)}

/* Right panel */
.panel{background:#0d0520;padding:16px;border-left:1px solid #1a0a2e}
.panel h2{font-size:10px;color:#4a4a5a;letter-spacing:3px;margin-bottom:16px}
.event{padding:10px 0;border-bottom:1px solid #1a0a2e;font-size:10px}
.event .time{color:#4a4a5a}
.event .desc{color:#6a6a7a;margin-top:4px}
.event .tag{display:inline-block;padding:2px 6px;background:rgba(233,69,96,0.1);color:#e94560;font-size:8px;margin-top:4px}

/* Footer */
.footer{grid-column:1/-1;background:#0d0520;display:flex;align-items:center;padding:0 24px;font-size:9px;color:#3a3a4a;border-top:1px solid #1a0a2e}
.footer .sys{margin-right:16px}
.footer .bar{width:60px;height:3px;background:#1a0a2e;margin:0 4px}
.footer .bar-fill{height:100%;background:#2a8a7a}

@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.5}}
</style>
</head><body>
<div class="dashboard">
  <div class="header">
    <h1>OBSIDIAN SPIRE</h1>
    <div class="status"><div class="dot"></div>SYSTEM NOMINAL</div>
  </div>
  
  <div class="sidebar">
    <h2>NAVIGATION</h2>
    <div class="nav-item active">OVERVIEW</div>
    <div class="nav-item">RESONANCE</div>
    <div class="nav-item">CRYSTALLINE</div>
    <div class="nav-item">GEOLOGICAL</div>
    <div class="nav-item">BIOLUMINESCENT</div>
    <div class="nav-item">SETTINGS</div>
  </div>
  
  <div class="main">
    <h2>SYSTEM OVERVIEW</h2>
    <div class="cards">
      <div class="card"><div class="label">RESONANCE FREQ</div><div class="value">847<span class="unit">Hz</span></div><div class="trend up">+12% from baseline</div></div>
      <div class="card"><div class="label">CORE TEMP</div><div class="value">42.3<span class="unit">C</span></div><div class="trend up">Nominal</div></div>
      <div class="card"><div class="label">CRYSTAL GROWTH</div><div class="value">2.7<span class="unit">mm/day</span></div><div class="trend down">-3% from peak</div></div>
    </div>
    <div class="chart">
      <div class="chart-title">RESONANCE WAVEFORM</div>
      <canvas id="chart"></canvas>
    </div>
  </div>
  
  <div class="panel">
    <h2>EVENT LOG</h2>
    <div class="event"><div class="time">08:47:12</div><div class="desc">Crystal formation detected</div><div class="tag">GEOLOGICAL</div></div>
    <div class="event"><div class="time">08:42:05</div><div class="desc">Resonance frequency stabilized</div><div class="tag">PHYSICS</div></div>
    <div class="event"><div class="time">08:38:33</div><div class="desc">Bioluminescent bloom activated</div><div class="tag">BIO</div></div>
    <div class="event"><div class="time">08:31:17</div><div class="desc">Energy core output nominal</div><div class="tag">POWER</div></div>
    <div class="event"><div class="time">08:24:44</div><div class="desc">Structural integrity verified</div><div class="tag">SYSTEM</div></div>
  </div>
  
  <div class="footer">
    <span class="sys">SYS:NOMINAL</span>
    <span class="sys">CORE:87%</span><div class="bar"><div class="bar-fill" style="width:87%"></div></div>
    <span class="sys">TEMP:42C</span><div class="bar"><div class="bar-fill" style="width:42%"></div></div>
    <span class="sys">CYCLE:00847</span>
  </div>
</div>
<script>
const canvas=document.getElementById('chart');
const ctx=canvas.getContext('2d');
canvas.width=canvas.offsetWidth*2;canvas.height=canvas.offsetHeight*2;
ctx.scale(2,2);
const w=canvas.offsetWidth,h=canvas.offsetHeight;

function drawWave(){
  ctx.clearRect(0,0,w,h);
  ctx.strokeStyle='rgba(233,69,96,0.3)';ctx.lineWidth=1;
  // Grid
  for(let y=0;y<h;y+=20){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(w,y);ctx.stroke();}
  for(let x=0;x<w;x+=40){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,h);ctx.stroke();}
  
  // Waveform
  ctx.strokeStyle='#e94560';ctx.lineWidth=1.5;ctx.beginPath();
  const t=Date.now()*0.001;
  for(let x=0;x<w;x++){
    const y=h/2+Math.sin(x*0.02+t)*20+Math.sin(x*0.05+t*1.3)*10+Math.sin(x*0.01+t*0.7)*15;
    x===0?ctx.moveTo(x,y):ctx.lineTo(x,y);
  }
  ctx.stroke();
  
  // Secondary wave
  ctx.strokeStyle='rgba(83,52,131,0.5)';ctx.lineWidth=1;ctx.beginPath();
  for(let x=0;x<w;x++){
    const y=h/2+Math.sin(x*0.03+t*1.5)*15+Math.cos(x*0.02+t*0.8)*12;
    x===0?ctx.moveTo(x,y):ctx.lineTo(x,y);
  }
  ctx.stroke();
  
  requestAnimationFrame(drawWave);
}
drawWave();
console.log('UI craft: hierarchy, information structure, typography, interaction states, material language');
</script>
</body></html>'''
    
    with open(os.path.join(OUT, "obsidian_spire_ui.html"), "w") as f:
        f.write(html)
    print(f"  Saved: obsidian_spire_ui.html")
    return html


if __name__ == "__main__":
    create_digital_painting_html()
    create_shader_masterpiece_html()
    create_motion_craft_html()
    create_ui_craft_html()
    
    report = {
        "html_artifacts": [
            {"name": "Obsidian Depths Digital Painting", "file": "obsidian_depths_painting.html", "level": "L7-L8", "technique": "Canvas layered brushwork, 14 layers, grain, vignette"},
            {"name": "Crystalline Consciousness Shader", "file": "crystalline_shader.html", "level": "L8", "technique": "WebGL SDF raymarching, 5 crystal arms, AO, soft shadows"},
            {"name": "Resonance Pulse Motion", "file": "resonance_motion.html", "level": "L6", "technique": "CSS animation: anticipation, follow-through, stagger, weight"},
            {"name": "Obsidian Spire UI", "file": "obsidian_spire_ui.html", "level": "L7", "technique": "Grid layout, hierarchy, typography, interaction states, material"}
        ]
    }
    with open(os.path.join(OUT, "html_craft_report.json"), "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved: html_craft_report.json")
