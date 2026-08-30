#!/usr/bin/env python3
"""
Range Tests — shader, typography, vector, hybrid advantage.
All code-native, captured via Playwright.
"""

import os
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
ARTIFACTS = PROJECT_ROOT / "artifacts" / "visual" / "calibration"
ARTIFACTS.mkdir(parents=True, exist_ok=True)

# ============================================================
# SHADER RANGE — 5 diverse GLSL materials
# ============================================================

SHADERS = {
    "shader_metal": """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Brushed Metal</title>
<style>*{margin:0;padding:0}body{background:#0a0a0a;display:flex;align-items:center;justify-content:center;height:100vh;overflow:hidden}canvas{width:100vw;height:100vh}</style></head>
<body><canvas id="c"></canvas>
<script>
const c=document.getElementById('c'),gl=c.getContext('webgl');
c.width=1280;c.height=720;
const v=`attribute vec2 p;void main(){gl_Position=vec4(p,0,1);}`;
const f=`precision mediump float;
uniform vec2 r;uniform float t;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
void main(){
  vec2 uv=gl_FragCoord.xy/r;
  float grain=hash(uv*200.0+t*0.5)*0.04;
  float aniso=pow(abs(sin(uv.x*3.14159*60.0+uv.y*2.0+t*0.3)),0.3);
  float edge=pow(1.0-abs(uv.y-0.5)*2.0,3.0);
  vec3 base=vec3(0.75,0.72,0.68);
  vec3 gold=vec3(0.85,0.75,0.55);
  vec3 col=mix(base,gold,aniso*0.3+edge*0.2+grain);
  float spec=pow(max(0.0,sin(uv.x*10.0+t*2.0)*0.5+0.5),8.0)*0.15;
  col+=spec;
  float vig=1.0-length((uv-0.5)*1.5);
  col*=smoothstep(0.0,0.5,vig);
  gl_FragColor=vec4(col,1.0);
}`;
function s(t,s){const sh=gl.createShader(t);gl.shaderSource(sh,s);gl.compileShader(sh);return sh;}
const pg=gl.createProgram();gl.attachShader(pg,s(gl.VERTEX_SHADER,v));gl.attachShader(pg,s(gl.FRAGMENT_SHADER,f));gl.linkProgram(pg);gl.useProgram(pg);
gl.bindBuffer(gl.ARRAY_BUFFER,gl.createBuffer());gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);
const p=gl.getAttribLocation(pg,'p');gl.enableVertexAttribArray(p);gl.vertexAttribPointer(p,2,gl.FLOAT,false,0,0);
gl.uniform2f(gl.getUniformLocation(pg,'r'),1280,720);
(function loop(){gl.uniform1f(gl.getUniformLocation(pg,'t'),performance.now()/1000);gl.drawArrays(gl.TRIANGLE_STRIP,0,4);requestAnimationFrame(loop)})();
</script></body></html>""",

    "shader_organic": """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Organic Flow</title>
<style>*{margin:0;padding:0}body{background:#000;display:flex;align-items:center;justify-content:center;height:100vh;overflow:hidden}canvas{width:100vw;height:100vh}</style></head>
<body><canvas id="c"></canvas>
<script>
const c=document.getElementById('c'),gl=c.getContext('webgl');
c.width=1280;c.height=720;
const v=`attribute vec2 p;void main(){gl_Position=vec4(p,0,1);}`;
const f=`precision mediump float;
uniform vec2 r;uniform float t;
void main(){
  vec2 uv=gl_FragCoord.xy/r;
  float f1=sin(uv.x*6.0+t*0.8)*cos(uv.y*4.0+t*0.6)*0.5+0.5;
  float f2=sin((uv.x+uv.y)*5.0-t*1.2)*0.5+0.5;
  float f3=cos(length(uv-0.5)*10.0-t*0.5)*0.5+0.5;
  vec3 a=vec3(0.1,0.8,0.4);
  vec3 b=vec3(0.9,0.3,0.1);
  vec3 c2=vec3(0.2,0.3,0.9);
  vec3 col=mix(a,b,f1)*f2+mix(b,c2,f3)*0.3;
  float glow=exp(-length(uv-0.5)*3.0)*0.4;
  col+=glow*vec3(0.1,0.5,0.3);
  gl_FragColor=vec4(col,1.0);
}`;
function s(t,s){const sh=gl.createShader(t);gl.shaderSource(sh,s);gl.compileShader(sh);return sh;}
const pg=gl.createProgram();gl.attachShader(pg,s(gl.VERTEX_SHADER,v));gl.attachShader(pg,s(gl.FRAGMENT_SHADER,f));gl.linkProgram(pg);gl.useProgram(pg);
gl.bindBuffer(gl.ARRAY_BUFFER,gl.createBuffer());gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);
const p=gl.getAttribLocation(pg,'p');gl.enableVertexAttribArray(p);gl.vertexAttribPointer(p,2,gl.FLOAT,false,0,0);
gl.uniform2f(gl.getUniformLocation(pg,'r'),1280,720);
(function loop(){gl.uniform1f(gl.getUniformLocation(pg,'t'),performance.now()/1000);gl.drawArrays(gl.TRIANGLE_STRIP,0,4);requestAnimationFrame(loop)})();
</script></body></html>""",

    "shader_volumetric": """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Volumetric Fog</title>
<style>*{margin:0;padding:0}body{background:#000;display:flex;align-items:center;justify-content:center;height:100vh;overflow:hidden}canvas{width:100vw;height:100vh}</style></head>
<body><canvas id="c"></canvas>
<script>
const c=document.getElementById('c'),gl=c.getContext('webgl');
c.width=1280;c.height=720;
const v=`attribute vec2 p;void main(){gl_Position=vec4(p,0,1);}`;
const f=`precision mediump float;
uniform vec2 r;uniform float t;
float n(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float sn(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.0-2.0*f);return mix(mix(n(i),n(i+vec2(1,0)),f.x),mix(n(i+vec2(0,1)),n(i+vec2(1,1)),f.x),f.y);}
float fbm(vec2 p){float v=0.0;float a=0.5;for(int i=0;i<5;i++){v+=a*sn(p);p*=2.0;a*=0.5;}return v;}
void main(){
  vec2 uv=gl_FragCoord.xy/r;
  float fog=fbm(uv*3.0+vec2(t*0.1,t*0.05));
  float depth=fbm(uv*2.0-vec2(t*0.08,0.0));
  vec3 light=vec3(1.0,0.85,0.6)*exp(-abs(fog-0.5)*4.0);
  vec3 shadow=vec3(0.05,0.05,0.15)*depth;
  vec3 col=light+shadow;
  float beam=exp(-pow(abs(uv.x-0.4)*5.0,2.0))*exp(-uv.y*2.0)*fog;
  col+=beam*vec3(0.3,0.25,0.15);
  float grain=n(uv*500.0+t)*0.02;
  col+=grain;
  gl_FragColor=vec4(col,1.0);
}`;
function s(t,s){const sh=gl.createShader(t);gl.shaderSource(sh,s);gl.compileShader(sh);return sh;}
const pg=gl.createProgram();gl.attachShader(pg,s(gl.VERTEX_SHADER,v));gl.attachShader(pg,s(gl.FRAGMENT_SHADER,f));gl.linkProgram(pg);gl.useProgram(pg);
gl.bindBuffer(gl.ARRAY_BUFFER,gl.createBuffer());gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);
const p=gl.getAttribLocation(pg,'p');gl.enableVertexAttribArray(p);gl.vertexAttribPointer(p,2,gl.FLOAT,false,0,0);
gl.uniform2f(gl.getUniformLocation(pg,'r'),1280,720);
(function loop(){gl.uniform1f(gl.getUniformLocation(pg,'t'),performance.now()/1000);gl.drawArrays(gl.TRIANGLE_STRIP,0,4);requestAnimationFrame(loop)})();
</script></body></html>""",

    "shader_abstract": """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Abstract Field</title>
<style>*{margin:0;padding:0}body{background:#000;display:flex;align-items:center;justify-content:center;height:100vh;overflow:hidden}canvas{width:100vw;height:100vh}</style></head>
<body><canvas id="c"></canvas>
<script>
const c=document.getElementById('c'),gl=c.getContext('webgl');
c.width=1280;c.height=720;
const v=`attribute vec2 p;void main(){gl_Position=vec4(p,0,1);}`;
const f=`precision mediump float;
uniform vec2 r;uniform float t;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
void main(){
  vec2 uv=(gl_FragCoord.xy-0.5*r)/min(r.x,r.y);
  float a=atan(uv.y,uv.x);
  float d=length(uv);
  float r2=0.2+0.1*sin(a*5.0+t)+0.05*sin(a*13.0-t*2.0);
  float ring=smoothstep(0.01,0.0,abs(d-r2));
  float field=sin(d*20.0-a*3.0+t)*0.5+0.5;
  vec3 c1=vec3(0.9,0.2,0.4);
  vec3 c2=vec3(0.1,0.4,0.9);
  vec3 c3=vec3(0.9,0.7,0.1);
  vec3 col=mix(c1,c2,field)*ring+mix(c2,c3,uv.x*0.5+0.5)*0.15*field;
  float glow=exp(-d*3.0)*0.3;
  col+=glow*c1;
  gl_FragColor=vec4(col,1.0);
}`;
function s(t,s){const sh=gl.createShader(t);gl.shaderSource(sh,s);gl.compileShader(sh);return sh;}
const pg=gl.createProgram();gl.attachShader(pg,s(gl.VERTEX_SHADER,v));gl.attachShader(pg,s(gl.FRAGMENT_SHADER,f));gl.linkProgram(pg);gl.useProgram(pg);
gl.bindBuffer(gl.ARRAY_BUFFER,gl.createBuffer());gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);
const p=gl.getAttribLocation(pg,'p');gl.enableVertexAttribArray(p);gl.vertexAttribPointer(p,2,gl.FLOAT,false,0,0);
gl.uniform2f(gl.getUniformLocation(pg,'r'),1280,720);
(function loop(){gl.uniform1f(gl.getUniformLocation(pg,'t'),performance.now()/1000);gl.drawArrays(gl.TRIANGLE_STRIP,0,4);requestAnimationFrame(loop)})();
</script></body></html>""",

    "shader_chromatic": """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Chromatic Dispersion</title>
<style>*{margin:0;padding:0}body{background:#000;display:flex;align-items:center;justify-content:center;height:100vh;overflow:hidden}canvas{width:100vw;height:100vh}</style></head>
<body><canvas id="c"></canvas>
<script>
const c=document.getElementById('c'),gl=c.getContext('webgl');
c.width=1280;c.height=720;
const v=`attribute vec2 p;void main(){gl_Position=vec4(p,0,1);}`;
const f=`precision mediump float;
uniform vec2 r;uniform float t;
void main(){
  vec2 uv=(gl_FragCoord.xy-0.5*r)/min(r.x,r.y);
  float d=length(uv);
  float a=atan(uv.y,uv.x);
  float prism=d+sin(a*3.0+t*0.5)*0.1;
  float r3=smoothstep(0.3,0.0,abs(prism-0.2));
  float g=smoothstep(0.3,0.0,abs(prism-0.25));
  float b=smoothstep(0.3,0.0,abs(prism-0.3));
  vec3 col=vec3(r3,g*0.8,b);
  float glass=smoothstep(0.35,0.3,d)*smoothstep(0.15,0.2,d);
  col+=glass*vec3(0.8,0.8,0.9)*0.3;
  float dispersion=sin(a*7.0+d*10.0-t)*0.5+0.5;
  col+=dispersion*vec3(0.1,0.05,0.15)*0.3;
  gl_FragColor=vec4(col,1.0);
}`;
function s(t,s){const sh=gl.createShader(t);gl.shaderSource(sh,s);gl.compileShader(sh);return sh;}
const pg=gl.createProgram();gl.attachShader(pg,s(gl.VERTEX_SHADER,v));gl.attachShader(pg,s(gl.FRAGMENT_SHADER,f));gl.linkProgram(pg);gl.useProgram(pg);
gl.bindBuffer(gl.ARRAY_BUFFER,gl.createBuffer());gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);
const p=gl.getAttribLocation(pg,'p');gl.enableVertexAttribArray(p);gl.vertexAttribPointer(p,2,gl.FLOAT,false,0,0);
gl.uniform2f(gl.getUniformLocation(pg,'r'),1280,720);
(function loop(){gl.uniform1f(gl.getUniformLocation(pg,'t'),performance.now()/1000);gl.drawArrays(gl.TRIANGLE_STRIP,0,4);requestAnimationFrame(loop)})();
</script></body></html>""",
}

# ============================================================
# TYPOGRAPHY RANGE — 5 styles
# ============================================================

TYPOGRAPHY = {
    "typo_editorial": """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Editorial</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400&family=Inter:wght@300;400&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{background:#f5f0eb;color:#1a1a1a;font-family:'Inter',sans-serif;padding:80px;min-height:100vh;display:flex;flex-direction:column;justify-content:center}
.issue{font-size:11px;letter-spacing:6px;text-transform:uppercase;color:#888;margin-bottom:60px}
.headline{font-family:'Playfair Display',serif;font-size:82px;font-weight:900;line-height:0.92;margin-bottom:40px;max-width:800px}
.headline em{font-style:italic;color:#8b4513}
.sub{font-size:18px;font-weight:300;line-height:1.7;max-width:500px;color:#555;margin-bottom:60px}
.meta{display:flex;gap:40px;border-top:1px solid #ccc;padding-top:20px}
.meta span{font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#999}
</style></head>
<body>
<div class="issue">Issue 47 / Autumn 2026</div>
<h1 class="headline">The Quiet <em>Revolution</em> in Material Culture</h1>
<p class="sub">How a new generation of makers is redefining the relationship between craft, technology, and the objects we choose to live with.</p>
<div class="meta"><span>Words by S. Nakamura</span><span>Photography by L. Voss</span><span>pp. 42-58</span></div>
</body></html>""",

    "typo_luxury": """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Luxury</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0c0c0c;color:#d4c5a0;font-family:'Cormorant Garamond',serif;display:flex;align-items:center;justify-content:center;height:100vh;overflow:hidden}
.container{text-align:center;padding:60px}
.brand{font-size:13px;letter-spacing:12px;text-transform:uppercase;color:#8b7d5e;margin-bottom:80px}
.hero{font-size:120px;font-weight:300;line-height:1;letter-spacing:-2px;margin-bottom:40px;background:linear-gradient(135deg,#d4c5a0 0%,#f0e6c8 40%,#8b7d5e 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.sub{font-size:16px;font-weight:300;letter-spacing:4px;text-transform:uppercase;color:#6b6040}
.line{width:60px;height:1px;background:#8b7d5e;margin:40px auto}
.year{font-size:12px;letter-spacing:6px;color:#5a5030}
</style></head>
<body>
<div class="container">
  <div class="brand">Maison Oreille</div>
  <h1 class="hero">Silence</h1>
  <div class="line"></div>
  <p class="sub">A collection in stillness</p>
  <div class="year">MMXXVI</div>
</div>
</body></html>""",

    "typo_experimental": """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Experimental</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a0a;color:#fff;font-family:'Space Mono',monospace;height:100vh;overflow:hidden;position:relative}
.grid{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,0.03) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.03) 1px,transparent 1px);background-size:40px 40px}
.t1{position:absolute;top:80px;left:80px;font-size:140px;font-weight:700;line-height:0.85;color:transparent;-webkit-text-stroke:1px rgba(255,255,255,0.6)}
.t2{position:absolute;top:200px;left:120px;font-size:140px;font-weight:700;line-height:0.85;color:rgba(255,50,50,0.9)}
.t3{position:absolute;top:160px;right:100px;font-size:48px;font-weight:400;writing-mode:vertical-rl;color:rgba(255,255,255,0.15);letter-spacing:8px}
.accent{position:absolute;bottom:120px;left:80px;font-size:11px;letter-spacing:6px;text-transform:uppercase;color:#666}
.dots{position:absolute;bottom:80px;right:80px;display:flex;gap:8px}
.dots span{width:6px;height:6px;border-radius:50%;background:#333}
.dots span:first-child{background:#ff3333}
</style></head>
<body>
<div class="grid"></div>
<div class="t1">DIS</div>
<div class="t2">RUPT</div>
<div class="t3">CONSTRUCT VISUAL LANGUAGE</div>
<div class="accent">Typography as architecture / 2026</div>
<div class="dots"><span></span><span></span><span></span><span></span></div>
</body></html>""",

    "typo_kinetic": """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kinetic</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{background:#111;color:#fff;font-family:'Bebas Neue',sans-serif;height:100vh;display:flex;align-items:center;justify-content:center;overflow:hidden}
.word{font-size:160px;letter-spacing:20px;display:flex;gap:4px}
.letter{display:inline-block;animation:rise 2s ease-out both}
@keyframes rise{from{transform:translateY(80px);opacity:0}to{transform:translateY(0);opacity:1}}
.letter:nth-child(1){animation-delay:0.0s}.letter:nth-child(2){animation-delay:0.08s}
.letter:nth-child(3){animation-delay:0.16s}.letter:nth-child(4){animation-delay:0.24s}
.letter:nth-child(5){animation-delay:0.32s}.letter:nth-child(6){animation-delay:0.40s}
.letter:nth-child(7){animation-delay:0.48s}
.underline{width:0;height:3px;background:#ff4444;animation:grow 0.8s 0.6s ease-out forwards}
@keyframes grow{to{width:100%}}
.sub{position:absolute;bottom:35%;font-size:14px;letter-spacing:8px;text-transform:uppercase;color:#555;opacity:0;animation:fade 1s 1s forwards}
@keyframes fade{to{opacity:1}}
</style></head>
<body>
<div style="text-align:center">
  <div class="word">
    <span class="letter">M</span><span class="letter">O</span><span class="letter">T</span>
    <span class="letter">I</span><span class="letter">O</span><span class="letter">N</span>
  </div>
  <div class="underline"></div>
  <div class="sub">Kinetic Typography Study</div>
</div>
</body></html>""",

    "typo_ui": """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>UI Typography</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{background:#fafafa;color:#1a1a1a;font-family:'Inter',sans-serif;padding:60px;min-height:100vh}
.nav{display:flex;justify-content:space-between;align-items:center;margin-bottom:120px}
.logo{font-size:18px;font-weight:700;letter-spacing:-0.5px}
.nav-links{display:flex;gap:32px}
.nav-links a{font-size:13px;font-weight:500;color:#666;text-decoration:none;letter-spacing:0.5px}
.hero-title{font-size:64px;font-weight:700;line-height:1.05;letter-spacing:-2px;max-width:700px;margin-bottom:24px}
.hero-sub{font-size:18px;font-weight:300;color:#666;line-height:1.6;max-width:450px;margin-bottom:48px}
.cta{display:inline-block;background:#1a1a1a;color:#fff;padding:14px 32px;font-size:14px;font-weight:500;border:none;cursor:pointer;letter-spacing:0.5px}
.stats{display:flex;gap:60px;margin-top:80px;padding-top:40px;border-top:1px solid #e0e0e0}
.stat-num{font-size:42px;font-weight:700;letter-spacing:-1px}
.stat-label{font-size:12px;color:#999;letter-spacing:1px;text-transform:uppercase;margin-top:4px}
</style></head>
<body>
<nav class="nav">
  <div class="logo">Arclight</div>
  <div class="nav-links"><a>Product</a><a>Studio</a><a>Journal</a><a>Contact</a></div>
</nav>
<h1 class="hero-title">Design tools that think at the speed of light.</h1>
<p class="hero-sub">Precision instruments for creative teams who refuse to compromise between form and function.</p>
<button class="cta">Start Building</button>
<div class="stats">
  <div><div class="stat-num">2.4M</div><div class="stat-label">Active Users</div></div>
  <div><div class="stat-num">99.9%</div><div class="stat-label">Uptime</div></div>
  <div><div class="stat-num">140+</div><div class="stat-label">Countries</div></div>
</div>
</body></html>""",
}

# ============================================================
# VECTOR RANGE — 4 SVG types
# ============================================================

VECTORS = {
    "vec_brand_mark": """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Brand Mark</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0d1117;display:flex;align-items:center;justify-content:center;height:100vh}
svg{width:400px;height:400px}
</style></head>
<body>
<svg viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="g1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#4ade80"/>
      <stop offset="100%" stop-color="#0ea5e9"/>
    </linearGradient>
  </defs>
  <!-- Abstract botanical form: stem + leaves as bezier curves -->
  <path d="M200,350 Q200,280 180,220 Q160,160 200,100 Q240,160 220,220 Q200,280 200,350Z" fill="none" stroke="url(#g1)" stroke-width="2.5"/>
  <!-- Left leaf -->
  <path d="M180,220 Q120,200 90,150 Q120,130 170,170 Q180,190 180,220Z" fill="url(#g1)" opacity="0.3"/>
  <path d="M180,220 Q120,200 90,150" fill="none" stroke="url(#g1)" stroke-width="1.5"/>
  <!-- Right leaf -->
  <path d="M220,200 Q280,170 310,120 Q280,110 230,150 Q220,170 220,200Z" fill="url(#g1)" opacity="0.3"/>
  <path d="M220,200 Q280,170 310,120" fill="none" stroke="url(#g1)" stroke-width="1.5"/>
  <!-- Small accent leaves -->
  <path d="M190,270 Q150,260 140,230 Q160,230 185,255Z" fill="url(#g1)" opacity="0.2"/>
  <path d="M210,250 Q250,235 265,210 Q245,215 215,238Z" fill="url(#g1)" opacity="0.2"/>
  <!-- Top bud -->
  <circle cx="200" cy="95" r="6" fill="url(#g1)" opacity="0.8"/>
  <circle cx="200" cy="95" r="3" fill="#fff" opacity="0.6"/>
  <!-- Brand text -->
  <text x="200" y="380" text-anchor="middle" fill="#8892a0" font-family="Inter,sans-serif" font-size="11" letter-spacing="4">VERDANT</text>
</svg>
</body></html>""",

    "vec_organic_ornament": """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Organic Ornament</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#1a1520;display:flex;align-items:center;justify-content:center;height:100vh}
svg{width:600px;height:600px}
</style></head>
<body>
<svg viewBox="0 0 600 600" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <radialGradient id="rg" cx="50%" cy="50%"><stop offset="0%" stop-color="#c084fc" stop-opacity="0.6"/><stop offset="100%" stop-color="#7c3aed" stop-opacity="0"/></radialGradient>
    <filter id="glow"><feGaussianBlur stdDeviation="3" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <!-- Central mandala-like organic form -->
  <circle cx="300" cy="300" r="120" fill="url(#rg)" opacity="0.4"/>
  <!-- Spiraling petal forms -->
  <g filter="url(#glow)" opacity="0.7">
    <path d="M300,180 Q340,220 320,280 Q300,300 300,300 Q300,300 280,280 Q260,220 300,180Z" fill="#c084fc" opacity="0.5"/>
    <path d="M300,180 Q340,220 320,280 Q300,300 300,300 Q300,300 280,280 Q260,220 300,180Z" fill="#c084fc" opacity="0.5" transform="rotate(45,300,300)"/>
    <path d="M300,180 Q340,220 320,280 Q300,300 300,300 Q300,300 280,280 Q260,220 300,180Z" fill="#c084fc" opacity="0.5" transform="rotate(90,300,300)"/>
    <path d="M300,180 Q340,220 320,280 Q300,300 300,300 Q300,300 280,280 Q260,220 300,180Z" fill="#c084fc" opacity="0.5" transform="rotate(135,300,300)"/>
    <path d="M300,180 Q340,220 320,280 Q300,300 300,300 Q300,300 280,280 Q260,220 300,180Z" fill="#c084fc" opacity="0.5" transform="rotate(180,300,300)"/>
    <path d="M300,180 Q340,220 320,280 Q300,300 300,300 Q300,300 280,280 Q260,220 300,180Z" fill="#c084fc" opacity="0.5" transform="rotate(225,300,300)"/>
    <path d="M300,180 Q340,220 320,280 Q300,300 300,300 Q300,300 280,280 Q260,220 300,180Z" fill="#c084fc" opacity="0.5" transform="rotate(270,300,300)"/>
    <path d="M300,180 Q340,220 320,280 Q300,300 300,300 Q300,300 280,280 Q260,220 300,180Z" fill="#c084fc" opacity="0.5" transform="rotate(315,300,300)"/>
  </g>
  <!-- Outer ring tendrils -->
  <g fill="none" stroke="#a78bfa" stroke-width="1" opacity="0.4">
    <circle cx="300" cy="300" r="160"/>
    <circle cx="300" cy="300" r="200" stroke-dasharray="4 8"/>
  </g>
  <!-- Dot accents -->
  <g fill="#c084fc" opacity="0.6">
    <circle cx="300" cy="120" r="3"/><circle cx="420" cy="180" r="2.5"/>
    <circle cx="460" cy="300" r="3"/><circle cx="420" cy="420" r="2.5"/>
    <circle cx="300" cy="480" r="3"/><circle cx="180" cy="420" r="2.5"/>
    <circle cx="140" cy="300" r="3"/><circle cx="180" cy="180" r="2.5"/>
  </g>
</svg>
</body></html>""",

    "vec_tech_graphic": """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Technical Graphic</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0f172a;display:flex;align-items:center;justify-content:center;height:100vh}
svg{width:500px;height:500px}
</style></head>
<body>
<svg viewBox="0 0 500 500" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="tg" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#38bdf8"/><stop offset="100%" stop-color="#818cf8"/></linearGradient>
  </defs>
  <!-- Technical blueprint style -->
  <g stroke="url(#tg)" fill="none" stroke-width="0.8" opacity="0.3">
    <line x1="50" y1="250" x2="450" y2="250"/><line x1="250" y1="50" x2="250" y2="450"/>
    <circle cx="250" cy="250" r="150"/><circle cx="250" cy="250" r="100"/>
    <circle cx="250" cy="250" r="50"/>
  </g>
  <!-- Hexagonal structure -->
  <g stroke="url(#tg)" fill="none" stroke-width="1.5" opacity="0.8">
    <polygon points="250,100 380,175 380,325 250,400 120,325 120,175"/>
    <polygon points="250,150 340,200 340,300 250,350 160,300 160,200"/>
  </g>
  <!-- Connection nodes -->
  <g fill="#38bdf8">
    <circle cx="250" cy="100" r="4"/><circle cx="380" cy="175" r="4"/>
    <circle cx="380" cy="325" r="4"/><circle cx="250" cy="400" r="4"/>
    <circle cx="120" cy="325" r="4"/><circle cx="120" cy="175" r="4"/>
  </g>
  <!-- Internal structure lines -->
  <g stroke="#818cf8" stroke-width="0.5" opacity="0.4">
    <line x1="250" y1="100" x2="250" y2="150"/><line x1="380" y1="175" x2="340" y2="200"/>
    <line x1="380" y1="325" x2="340" y2="300"/><line x1="250" y1="400" x2="250" y2="350"/>
    <line x1="120" y1="325" x2="160" y2="300"/><line x1="120" y1="175" x2="160" y2="200"/>
  </g>
  <!-- Labels -->
  <text x="250" y="440" text-anchor="middle" fill="#475569" font-family="monospace" font-size="10" letter-spacing="3">NODE.TOPOLOGY.v3</text>
</svg>
</body></html>""",

    "vec_abstract_composition": """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Abstract Composition</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#f8f6f3;display:flex;align-items:center;justify-content:center;height:100vh}
svg{width:600px;height:600px}
</style></head>
<body>
<svg viewBox="0 0 600 600" xmlns="http://www.w3.org/2000/svg">
  <!-- Large asymmetric shape -->
  <path d="M80,400 Q120,200 300,150 Q480,100 520,300 Q540,450 400,500 Q200,550 80,400Z" fill="#1a1a1a" opacity="0.08"/>
  <!-- Overlapping circles -->
  <circle cx="220" cy="280" r="100" fill="#e63946" opacity="0.15"/>
  <circle cx="320" cy="320" r="80" fill="#457b9d" opacity="0.15"/>
  <circle cx="380" cy="240" r="60" fill="#2a9d8f" opacity="0.15"/>
  <!-- Line elements -->
  <line x1="100" y1="450" x2="500" y2="450" stroke="#1a1a1a" stroke-width="0.5" opacity="0.3"/>
  <line x1="150" y1="100" x2="150" y2="500" stroke="#1a1a1a" stroke-width="0.5" opacity="0.15"/>
  <!-- Typography as form -->
  <text x="300" y="310" text-anchor="middle" fill="#1a1a1a" font-family="Inter,sans-serif" font-size="120" font-weight="900" opacity="0.06">Aa</text>
  <text x="300" y="520" text-anchor="middle" fill="#1a1a1a" font-family="Inter,sans-serif" font-size="11" letter-spacing="6" opacity="0.4">ABSTRACTION STUDY NO. 7</text>
  <!-- Small precise elements -->
  <rect x="460" y="120" width="40" height="40" fill="none" stroke="#e63946" stroke-width="1" opacity="0.5"/>
  <circle cx="130" cy="160" r="15" fill="none" stroke="#457b9d" stroke-width="1" opacity="0.5"/>
</svg>
</body></html>""",
}

# ============================================================
# HYBRID ADVANTAGE TEST — same brief, 3 approaches
# ============================================================

HYBRID_GENERATIVE_ONLY = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Hybrid Test A - Generative Only</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a0f;color:#fff;font-family:'Inter',sans-serif;height:100vh;display:flex;align-items:center;justify-content:center}
.note{position:absolute;bottom:30px;font-size:10px;letter-spacing:3px;color:#444;text-transform:uppercase}
.scene{position:relative;width:800px;height:500px;background:linear-gradient(135deg,#0f172a 0%,#1e1b4b 50%,#0f172a 100%);border-radius:8px;overflow:hidden;display:flex;align-items:center;justify-content:center}
.glow{position:absolute;width:300px;height:300px;background:radial-gradient(circle,rgba(99,102,241,0.3),transparent 70%);top:50%;left:50%;transform:translate(-50%,-50%)}
.orb{width:120px;height:120px;border-radius:50%;background:radial-gradient(circle at 35% 35%,#818cf8,#4f46e5,#312e81);box-shadow:0 0 60px rgba(99,102,241,0.4),inset 0 -10px 20px rgba(0,0,0,0.3)}
.title{position:absolute;bottom:60px;font-size:11px;letter-spacing:8px;text-transform:uppercase;color:#666}
</style></head>
<body>
<div class="scene">
  <div class="glow"></div>
  <div class="orb"></div>
  <div class="title">Generative Concept Only</div>
</div>
<div class="note">Approach A: CSS/HTML only (no shaders, no SVG, no generative)</div>
</body></html>"""

HYBRID_CODE_NATIVE_ONLY = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Hybrid Test B - Code Native Only</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{background:#060610;color:#fff;font-family:'Inter',sans-serif;height:100vh;display:flex;align-items:center;justify-content:center}
.note{position:absolute;bottom:30px;font-size:10px;letter-spacing:3px;color:#444;text-transform:uppercase}
canvas{position:absolute;inset:0}
.overlay{position:relative;z-index:1;text-align:center}
.title{font-size:48px;font-weight:700;letter-spacing:-1px;background:linear-gradient(135deg,#c4b5fd,#818cf8,#6366f1);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.sub{font-size:13px;letter-spacing:6px;text-transform:uppercase;color:#6366f1;margin-top:16px}
</style></head>
<body>
<canvas id="c"></canvas>
<div class="overlay">
  <div class="title">Code Native Only</div>
  <div class="sub">WebGL shader + HTML typography</div>
</div>
<div class="note">Approach B: WebGL shader + deterministic type (no generative imagery)</div>
<script>
const c=document.getElementById('c'),gl=c.getContext('webgl');
c.width=window.innerWidth;c.height=window.innerHeight;
const v=`attribute vec2 p;void main(){gl_Position=vec4(p,0,1);}`;
const f=`precision mediump float;uniform vec2 r;uniform float t;
void main(){
  vec2 uv=gl_FragCoord.xy/r;
  float d=length(uv-0.5);
  float field=sin(d*20.0-t*2.0)*0.5+0.5;
  float glow=exp(-d*4.0);
  vec3 col=vec3(0.39,0.40,0.95)*glow*field;
  col+=vec3(0.2,0.15,0.5)*exp(-d*8.0)*0.5;
  gl_FragColor=vec4(col,1.0);
}`;
function s(t,s){const sh=gl.createShader(t);gl.shaderSource(sh,s);gl.compileShader(sh);return sh;}
const pg=gl.createProgram();gl.attachShader(pg,s(gl.VERTEX_SHADER,v));gl.attachShader(pg,s(gl.FRAGMENT_SHADER,f));gl.linkProgram(pg);gl.useProgram(pg);
gl.bindBuffer(gl.ARRAY_BUFFER,gl.createBuffer());gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);
const p=gl.getAttribLocation(pg,'p');gl.enableVertexAttribArray(p);gl.vertexAttribPointer(p,2,gl.FLOAT,false,0,0);
gl.uniform2f(gl.getUniformLocation(pg,'r'),c.width,c.height);
(function loop(){gl.uniform1f(gl.getUniformLocation(pg,'t'),performance.now()/1000);gl.drawArrays(gl.TRIANGLE_STRIP,0,4);requestAnimationFrame(loop)})();
</script>
</body></html>"""

HYBRID_FULL = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Hybrid Test C - Full Hybrid</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700;900&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{background:#060610;color:#fff;font-family:'Inter',sans-serif;height:100vh;overflow:hidden}
canvas#bg{position:absolute;inset:0;z-index:0}
.content{position:relative;z-index:1;height:100vh;display:flex;flex-direction:column;justify-content:center;align-items:center;padding:60px}
.brand{font-size:11px;letter-spacing:8px;text-transform:uppercase;color:rgba(255,255,255,0.3);margin-bottom:60px}
.hero{font-size:72px;font-weight:900;letter-spacing:-2px;text-align:center;line-height:1;background:linear-gradient(135deg,#c4b5fd 0%,#818cf8 40%,#e0e7ff 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:24px}
.sub{font-size:16px;font-weight:300;color:rgba(255,255,255,0.5);letter-spacing:2px;text-align:center;max-width:500px;line-height:1.6}
svg.deco{position:absolute;top:80px;right:80px;width:200px;height:200px;opacity:0.2}
svg.deco2{position:absolute;bottom:80px;left:80px;width:150px;height:150px;opacity:0.15}
.line{width:1px;height:80px;background:linear-gradient(to bottom,transparent,rgba(129,140,248,0.3),transparent);margin:30px 0}
</style></head>
<body>
<canvas id="bg"></canvas>
<div class="content">
  <div class="brand">Nova Collective</div>
  <svg class="deco" viewBox="0 0 200 200"><defs><linearGradient id="dg" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#818cf8"/><stop offset="100%" stop-color="#c4b5fd"/></linearGradient></defs>
    <circle cx="100" cy="100" r="80" fill="none" stroke="url(#dg)" stroke-width="0.8"/>
    <circle cx="100" cy="100" r="60" fill="none" stroke="url(#dg)" stroke-width="0.5" stroke-dasharray="4 6"/>
    <path d="M100,20 Q140,60 100,100 Q60,60 100,20Z" fill="url(#dg)" opacity="0.2"/>
    <path d="M100,100 Q140,140 100,180 Q60,140 100,100Z" fill="url(#dg)" opacity="0.2"/>
  </svg>
  <svg class="deco2" viewBox="0 0 150 150">
    <rect x="20" y="20" width="110" height="110" rx="4" fill="none" stroke="#818cf8" stroke-width="0.6" opacity="0.4"/>
    <line x1="20" y1="75" x2="130" y2="75" stroke="#818cf8" stroke-width="0.3" opacity="0.3"/>
  </svg>
  <div class="line"></div>
  <h1 class="hero">Where Light<br>Meets Form</h1>
  <p class="sub">An immersive exploration of material, light, and the spaces between digital and physical reality.</p>
</div>
<script>
const c=document.getElementById('bg'),gl=c.getContext('webgl');
c.width=window.innerWidth;c.height=window.innerHeight;
const v=`attribute vec2 p;void main(){gl_Position=vec4(p,0,1);}`;
const f=`precision mediump float;uniform vec2 r;uniform float t;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
void main(){
  vec2 uv=gl_FragCoord.xy/r;
  float d=length(uv-0.5);
  float f1=exp(-d*3.0)*0.3;
  float f2=sin(uv.x*6.0+t*0.5)*cos(uv.y*4.0-t*0.3)*0.1;
  float particles=step(0.99,hash(floor(uv*50.0)+floor(t*2.0)))*exp(-d*2.0);
  vec3 col=vec3(0.25,0.26,0.60)*(f1+f2)+vec3(0.5,0.5,0.8)*particles*0.3;
  gl_FragColor=vec4(col,1.0);
}`;
function s(t,s){const sh=gl.createShader(t);gl.shaderSource(sh,s);gl.compileShader(sh);return sh;}
const pg=gl.createProgram();gl.attachShader(pg,s(gl.VERTEX_SHADER,v));gl.attachShader(pg,s(gl.FRAGMENT_SHADER,f));gl.linkProgram(pg);gl.useProgram(pg);
gl.bindBuffer(gl.ARRAY_BUFFER,gl.createBuffer());gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);
const p=gl.getAttribLocation(pg,'p');gl.enableVertexAttribArray(p);gl.vertexAttribPointer(p,2,gl.FLOAT,false,0,0);
gl.uniform2f(gl.getUniformLocation(pg,'r'),c.width,c.height);
(function loop(){gl.uniform1f(gl.getUniformLocation(pg,'t'),performance.now()/1000);gl.drawArrays(gl.TRIANGLE_STRIP,0,4);requestAnimationFrame(loop)})();
</script>
</body></html>"""


def write_all():
    """Write all range test HTML files."""
    out_dir = PROJECT_ROOT / "artifacts" / "visual" / "calibration"
    out_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for name, html in {**SHADERS, **TYPOGRAPHY, **VECTORS}.items():
        path = out_dir / f"{name}.html"
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        count += 1

    # Hybrid advantage tests
    for name, html in [
        ("hybrid_gen_only", HYBRID_GENERATIVE_ONLY),
        ("hybrid_code_native", HYBRID_CODE_NATIVE_ONLY),
        ("hybrid_full", HYBRID_FULL),
    ]:
        path = out_dir / f"{name}.html"
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        count += 1

    print(f"Wrote {count} range test HTML files to {out_dir}")
    return count


if __name__ == "__main__":
    write_all()
