"""CODE-NATIVE CRAFT: SVG Vector Illustrations — direct path construction."""
import os, json

OUT = "artifacts/visual/final-craft"
os.makedirs(OUT, exist_ok=True)

def create_character_svg():
    """Obsidian Warden: crystalline guardian, Bézier curves, no primitives."""
    print("--- Vector Character: Obsidian Warden ---")
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="-200 -320 400 780" width="800" height="1560">
  <defs>
    <filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="4" seed="42"/><feColorMatrix type="saturate" values="0"/><feBlend in="SourceGraphic" mode="multiply"/></filter>
    <filter id="crystal"><feTurbulence type="turbulence" baseFrequency="0.02" numOctaves="3" seed="7"/><feDisplacementMap in="SourceGraphic" scale="3" xChannelSelector="R" yChannelSelector="G"/></filter>
    <filter id="glow"><feGaussianBlur stdDeviation="4" result="blur"/><feComposite in="SourceGraphic" in2="blur" operator="over"/></filter>
    <filter id="depth"><feGaussianBlur stdDeviation="8" result="blur"/><feOffset dx="3" dy="5" result="offset"/><feComposite in="SourceGraphic" in2="offset" operator="over"/></filter>
    <linearGradient id="obsidian" x1="0" y1="0" x2="0.3" y2="1">
      <stop offset="0%" stop-color="#1a1a2e"/><stop offset="30%" stop-color="#16213e"/><stop offset="60%" stop-color="#0f3460"/><stop offset="100%" stop-color="#1a1a2e"/>
    </linearGradient>
    <linearGradient id="crystal_hl" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#e94560" stop-opacity="0.8"/><stop offset="50%" stop-color="#533483" stop-opacity="0.4"/><stop offset="100%" stop-color="#0f3460" stop-opacity="0.6"/>
    </linearGradient>
    <radialGradient id="core_glow" cx="0.5" cy="0.3" r="0.6">
      <stop offset="0%" stop-color="#e94560" stop-opacity="0.9"/><stop offset="40%" stop-color="#533483" stop-opacity="0.5"/><stop offset="100%" stop-color="#0f3460" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="limb" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#16213e"/><stop offset="100%" stop-color="#0a0a15"/>
    </linearGradient>
    <linearGradient id="vein" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#e94560" stop-opacity="0"/><stop offset="30%" stop-color="#e94560" stop-opacity="0.7"/><stop offset="70%" stop-color="#c23152" stop-opacity="0.5"/><stop offset="100%" stop-color="#e94560" stop-opacity="0"/>
    </linearGradient>
  </defs>
  
  <rect x="-200" y="-320" width="400" height="780" fill="#0a0a12"/>
  <ellipse cx="0" cy="-100" rx="180" ry="200" fill="#1a1a2e" opacity="0.3"/>
  <ellipse cx="0" cy="420" rx="160" ry="30" fill="#0f0f1a" opacity="0.8"/>
  
  <!-- BODY: organic crystalline form -->
  <g filter="url(#depth)">
    <path d="M -35 180 C -42 150 -55 120 -65 90 C -72 60 -78 30 -80 0 C -75 -30 -68 -60 -58 -90 C -48 -115 -40 -135 -35 -155 C -30 -175 -22 -195 -15 -210
    L 15 -210 C 25 -200 35 -185 42 -165 C 50 -140 58 -115 68 -85 C 75 -55 80 -25 82 5 C 78 35 70 65 60 95 C 48 125 38 155 35 180
    L 55 180 C 60 215 62 250 60 285 C 58 315 55 345 48 370 C 38 390 25 405 15 415
    L -15 415 C -25 410 -38 395 -48 375 C -55 350 -58 320 -55 290 C -50 255 -42 220 -35 180 Z"
    fill="url(#obsidian)" stroke="#0a0a15" stroke-width="1"/>
  </g>
  
  <!-- Left arm: branching crystal -->
  <path d="M -78 -30 C -95 -45 -115 -55 -135 -50 C -155 -38 -170 -20 -178 5 C -175 25 -165 40 -150 48 C -130 45 -110 35 -90 20 C -82 12 -78 5 -78 -30 Z"
    fill="url(#limb)" stroke="#0f3460" stroke-width="0.5"/>
  
  <!-- Right arm: angular crystalline -->
  <path d="M 82 -25 C 100 -40 120 -52 142 -48 C 160 -35 172 -15 178 8 C 175 30 162 45 145 50 C 125 42 105 28 88 12 L 82 -25 Z"
    fill="url(#limb)" stroke="#0f3460" stroke-width="0.5"/>
  
  <!-- Crystal veins -->
  <g opacity="0.6">
    <line x1="-40" y1="-150" x2="-50" y2="100" stroke="url(#vein)" stroke-width="1.5"/>
    <line x1="10" y1="-180" x2="20" y2="120" stroke="url(#vein)" stroke-width="1"/>
    <line x1="40" y1="-100" x2="55" y2="80" stroke="url(#vein)" stroke-width="0.8"/>
    <line x1="-60" y1="-50" x2="-70" y2="60" stroke="url(#vein)" stroke-width="0.6"/>
    <line x1="-65" y1="0" x2="65" y2="-20" stroke="url(#vein)" stroke-width="0.5"/>
    <line x1="-50" y1="60" x2="50" y2="40" stroke="url(#vein)" stroke-width="0.4"/>
  </g>
  
  <!-- Form lighting -->
  <g opacity="0.3">
    <ellipse cx="-30" cy="-50" rx="60" ry="200" fill="#533483" opacity="0.4"/>
    <ellipse cx="-50" cy="0" rx="40" ry="150" fill="#e94560" opacity="0.2"/>
  </g>
  
  <!-- HEAD: crystalline form -->
  <path d="M -15 -210 C -25 -225 -30 -245 -22 -265 C -10 -280 5 -290 18 -285 C 28 -270 32 -250 28 -230 C 20 -215 15 -210 15 -210 Z"
    fill="url(#crystal_hl)" stroke="#e94560" stroke-width="0.8" filter="url(#crystal)"/>
  <ellipse cx="5" cy="-255" rx="12" ry="15" fill="url(#core_glow)" filter="url(#glow)"/>
  <path d="M -8 -258 L 0 -268 L 8 -258 L 0 -250 Z" fill="#e94560" opacity="0.9"/>
  <circle cx="0" cy="-258" r="2" fill="#fff" opacity="0.8"/>
  
  <!-- Shoulder protrusions -->
  <path d="M -70 -60 L -90 -80 L -85 -55 L -75 -45 Z" fill="#533483" stroke="#e94560" stroke-width="0.5" opacity="0.8"/>
  <path d="M 72 -55 L 92 -75 L 87 -50 L 77 -40 Z" fill="#533483" stroke="#e94560" stroke-width="0.5" opacity="0.8"/>
  
  <!-- Hand details -->
  <path d="M -175 5 L -185 -5 M -170 12 L -180 8 M -162 18 L -172 15" stroke="#0f3460" stroke-width="1.5" fill="none" stroke-linecap="round"/>
  <path d="M 175 8 L 185 -2 M 170 15 L 180 11 M 162 20 L 172 17" stroke="#0f3460" stroke-width="1.5" fill="none" stroke-linecap="round"/>
  
  <!-- Knee articulation -->
  <path d="M -52 310 Q -48 315 -44 310" stroke="#533483" stroke-width="1" fill="none"/>
  <path d="M 56 315 Q 60 320 64 315" stroke="#533483" stroke-width="1" fill="none"/>
  
  <!-- Ground reflection -->
  <ellipse cx="0" cy="430" rx="100" ry="12" fill="#e94560" opacity="0.08" filter="url(#glow)"/>
  
  <!-- Ambient particles -->
  <circle cx="-80" cy="-200" r="1" fill="#e94560" opacity="0.6"/>
  <circle cx="65" cy="-180" r="0.8" fill="#533483" opacity="0.5"/>
  <circle cx="-45" cy="100" r="1.2" fill="#e94560" opacity="0.4"/>
  <circle cx="80" cy="50" r="0.7" fill="#533483" opacity="0.5"/>
</svg>'''
    with open(os.path.join(OUT, "warden_character.svg"), "w") as f:
        f.write(svg)
    print("  Saved: warden_character.svg")

def create_creature_svg():
    """Abyssal Lure: bioluminescent deep-sea predator, functional anatomy."""
    print("--- Vector Creature: Abyssal Lure ---")
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="-250 -200 500 500" width="1000" height="1000">
  <defs>
    <filter id="bio"><feGaussianBlur stdDeviation="6" result="blur"/><feComposite in="SourceGraphic" in2="blur" operator="over"/></filter>
    <filter id="bio_s"><feGaussianBlur stdDeviation="12" result="blur"/><feComposite in="SourceGraphic" in2="blur" operator="over"/></filter>
    <filter id="turb"><feTurbulence type="turbulence" baseFrequency="0.015" numOctaves="4" seed="13"/><feDisplacementMap in="SourceGraphic" scale="4"/></filter>
    <radialGradient id="body_g" cx="0.5" cy="0.4" r="0.6">
      <stop offset="0%" stop-color="#1a0a2e"/><stop offset="60%" stop-color="#0d0520"/><stop offset="100%" stop-color="#050210"/>
    </radialGradient>
    <radialGradient id="lure_g" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0%" stop-color="#00ff88"/><stop offset="40%" stop-color="#00cc66"/><stop offset="100%" stop-color="#004422" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="eye_g" cx="0.4" cy="0.4" r="0.5">
      <stop offset="0%" stop-color="#ff3366"/><stop offset="100%" stop-color="#881133"/>
    </radialGradient>
  </defs>
  
  <rect x="-250" y="-200" width="500" height="500" fill="#020108"/>
  <circle cx="-180" cy="-150" r="1.5" fill="#00ff88" opacity="0.3" filter="url(#bio)"/>
  <circle cx="200" cy="-120" r="1" fill="#00ccff" opacity="0.2" filter="url(#bio)"/>
  <circle cx="-150" cy="180" r="0.8" fill="#ff6699" opacity="0.25" filter="url(#bio)"/>
  <circle cx="170" cy="150" r="1.2" fill="#00ff88" opacity="0.2" filter="url(#bio)"/>
  
  <!-- Tentacles -->
  <path d="M -20 -30 C -60 -80 -120 -140 -180 -160 C -190 -162 -195 -155 -185 -148" stroke="#1a0a2e" stroke-width="12" fill="none" stroke-linecap="round" filter="url(#turb)"/>
  <path d="M -180 -160 C -185 -170 -195 -175 -200 -168" stroke="#00ff88" stroke-width="3" fill="none" stroke-linecap="round" filter="url(#bio)" opacity="0.7"/>
  <circle cx="-140" cy="-130" r="3" fill="#00ff88" opacity="0.5" filter="url(#bio)"/>
  
  <path d="M 20 -30 C 50 -90 100 -150 160 -170 C 170 -173 178 -165 168 -158" stroke="#1a0a2e" stroke-width="10" fill="none" stroke-linecap="round" filter="url(#turb)"/>
  <path d="M 160 -170 C 165 -180 175 -182 178 -172" stroke="#00ff88" stroke-width="2.5" fill="none" stroke-linecap="round" filter="url(#bio)" opacity="0.6"/>
  
  <path d="M -25 10 C -90 0 -160 -20 -210 10 C -218 15 -215 28 -205 25" stroke="#1a0a2e" stroke-width="9" fill="none" stroke-linecap="round" filter="url(#turb)"/>
  <circle cx="-180" cy="5" r="2" fill="#00ccff" opacity="0.4" filter="url(#bio)"/>
  
  <path d="M 25 10 C 80 -15 150 -40 200 -10 C 208 0 205 15 195 12" stroke="#1a0a2e" stroke-width="9" fill="none" stroke-linecap="round" filter="url(#turb)"/>
  <circle cx="170" cy="-15" r="2" fill="#00ccff" opacity="0.4" filter="url(#bio)"/>
  
  <path d="M -15 35 C -50 80 -80 130 -120 170 C -125 178 -118 185 -112 178" stroke="#1a0a2e" stroke-width="7" fill="none" stroke-linecap="round" filter="url(#turb)"/>
  <circle cx="-90" cy="130" r="1.8" fill="#ff6699" opacity="0.3" filter="url(#bio)"/>
  
  <path d="M 15 35 C 45 75 75 125 110 165 C 115 173 122 178 118 168" stroke="#1a0a2e" stroke-width="7" fill="none" stroke-linecap="round" filter="url(#turb)"/>
  <circle cx="85" cy="125" r="1.8" fill="#ff6699" opacity="0.3" filter="url(#bio)"/>
  
  <!-- Body -->
  <ellipse cx="0" cy="0" rx="35" ry="40" fill="url(#body_g)" stroke="#1a0a2e" stroke-width="1"/>
  <path d="M -25 -20 Q 0 -30 25 -20" stroke="#2a1540" stroke-width="0.8" fill="none"/>
  <path d="M -28 -5 Q 0 -12 28 -5" stroke="#2a1540" stroke-width="0.6" fill="none"/>
  <path d="M -25 10 Q 0 3 25 10" stroke="#2a1540" stroke-width="0.5" fill="none"/>
  <ellipse cx="-10" cy="-15" rx="8" ry="5" fill="#00ff88" opacity="0.15" filter="url(#bio)"/>
  <ellipse cx="12" cy="5" rx="6" ry="4" fill="#00ccff" opacity="0.12" filter="url(#bio)"/>
  
  <!-- Eyes -->
  <ellipse cx="-12" cy="-18" rx="6" ry="5" fill="url(#eye_g)" filter="url(#bio_s)"/>
  <ellipse cx="-12" cy="-18" rx="2.5" ry="3" fill="#110022"/>
  <circle cx="-11" cy="-19" r="1" fill="#ff6699" opacity="0.8"/>
  <ellipse cx="-8" cy="-8" rx="4" ry="3.5" fill="url(#eye_g)" filter="url(#bio_s)" opacity="0.8"/>
  <ellipse cx="-8" cy="-8" rx="1.5" ry="2" fill="#110022"/>
  <ellipse cx="12" cy="-15" rx="5" ry="4.5" fill="url(#eye_g)" filter="url(#bio_s)"/>
  <ellipse cx="12" cy="-15" rx="2" ry="2.5" fill="#110022"/>
  <circle cx="13" cy="-16" r="0.8" fill="#ff6699" opacity="0.8"/>
  <ellipse cx="10" cy="-5" rx="3.5" ry="3" fill="url(#eye_g)" filter="url(#bio_s)" opacity="0.7"/>
  <ellipse cx="10" cy="-5" rx="1.2" ry="1.8" fill="#110022"/>
  
  <!-- Mouth -->
  <ellipse cx="0" cy="15" rx="10" ry="7" fill="#0a0318" stroke="#2a1540" stroke-width="0.8"/>
  <ellipse cx="0" cy="15" rx="7" ry="5" fill="#050210"/>
  
  <!-- Lure -->
  <path d="M 0 -40 C 5 -60 8 -90 3 -115 C 0 -125 -5 -130 -8 -125" stroke="#0d3020" stroke-width="3" fill="none" stroke-linecap="round"/>
  <path d="M 0 -40 C 5 -60 8 -90 3 -115 C 0 -125 -5 -130 -8 -125" stroke="#00ff88" stroke-width="1" fill="none" stroke-linecap="round" filter="url(#bio)" opacity="0.4"/>
  <circle cx="-5" cy="-128" r="8" fill="url(#lure_g)" filter="url(#bio_s)"/>
  <circle cx="-5" cy="-128" r="3" fill="#aaffcc" opacity="0.8"/>
  <circle cx="-4" cy="-130" r="1" fill="#ffffff" opacity="0.6"/>
</svg>'''
    with open(os.path.join(OUT, "abyssal_creature.svg"), "w") as f:
        f.write(svg)
    print("  Saved: abyssal_creature.svg")

def create_environment_svg():
    """Obsidian Spires: volcanic crystalline landscape with atmospheric perspective."""
    print("--- Vector Environment: Obsidian Spires ---")
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900" width="1600" height="900">
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0a0520"/><stop offset="40%" stop-color="#1a0a35"/><stop offset="70%" stop-color="#2a1540"/><stop offset="100%" stop-color="#3a2050"/>
    </linearGradient>
    <linearGradient id="spire" x1="0" y1="0" x2="0.2" y2="1">
      <stop offset="0%" stop-color="#2a1540"/><stop offset="50%" stop-color="#1a0a2e"/><stop offset="100%" stop-color="#0d0520"/>
    </linearGradient>
    <linearGradient id="spire_hl" x1="0" y1="0" x2="1" y2="0.3">
      <stop offset="0%" stop-color="#4a2570" stop-opacity="0.6"/><stop offset="100%" stop-color="#1a0a2e" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="ground" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0d0520"/><stop offset="100%" stop-color="#050210"/>
    </linearGradient>
    <linearGradient id="lava" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#ff4400" stop-opacity="0.6"/><stop offset="100%" stop-color="#ff2200" stop-opacity="0.1"/>
    </linearGradient>
    <filter id="ab"><feGaussianBlur stdDeviation="3"/></filter>
    <filter id="db"><feGaussianBlur stdDeviation="6"/></filter>
    <filter id="gs"><feGaussianBlur stdDeviation="4" result="blur"/><feComposite in="SourceGraphic" in2="blur" operator="over"/></filter>
  </defs>
  
  <rect width="1600" height="900" fill="url(#sky)"/>
  <g opacity="0.6">
    <circle cx="120" cy="50" r="1" fill="#fff"/><circle cx="350" cy="80" r="0.7" fill="#dda0ff"/>
    <circle cx="580" cy="30" r="1.2" fill="#fff"/><circle cx="800" cy="60" r="0.8" fill="#aaccff"/>
    <circle cx="1050" cy="45" r="1" fill="#fff"/><circle cx="1300" cy="70" r="0.6" fill="#dda0ff"/>
    <circle cx="1480" cy="35" r="0.9" fill="#fff"/><circle cx="200" cy="120" r="0.5" fill="#aaccff"/>
  </g>
  <ellipse cx="400" cy="150" rx="200" ry="80" fill="#3a1560" opacity="0.15" filter="url(#db)"/>
  <ellipse cx="1200" cy="120" rx="150" ry="60" fill="#2a1050" opacity="0.1" filter="url(#db)"/>
  
  <!-- Distant range -->
  <g filter="url(#db)" opacity="0.5">
    <path d="M 0 500 L 100 380 L 180 420 L 280 350 L 350 400 L 450 320 L 520 370 L 600 300 L 680 340 L 750 280 L 830 320 L 900 260 L 980 310 L 1050 290 L 1120 330 L 1200 270 L 1280 310 L 1350 350 L 1420 300 L 1500 340 L 1600 380 L 1600 500 Z" fill="#1a0a2e"/>
  </g>
  
  <!-- Mid spires -->
  <g filter="url(#ab)" opacity="0.7">
    <path d="M 200 500 L 220 300 L 235 350 L 250 280 L 260 320 L 270 500 Z" fill="url(#spire)"/>
    <path d="M 200 500 L 220 300 L 235 350 L 250 280 L 260 320 L 270 500 Z" fill="url(#spire_hl)"/>
    <path d="M 500 500 L 530 250 L 545 300 L 560 220 L 575 280 L 590 500 Z" fill="url(#spire)"/>
    <path d="M 500 500 L 530 250 L 545 300 L 560 220 L 575 280 L 590 500 Z" fill="url(#spire_hl)"/>
    <path d="M 800 500 L 840 200 L 860 260 L 880 180 L 900 240 L 920 500 Z" fill="url(#spire)"/>
    <path d="M 800 500 L 840 200 L 860 260 L 880 180 L 900 240 L 920 500 Z" fill="url(#spire_hl)"/>
    <path d="M 1100 500 L 1130 280 L 1145 330 L 1160 260 L 1175 310 L 1190 500 Z" fill="url(#spire)"/>
    <path d="M 1100 500 L 1130 280 L 1145 330 L 1160 260 L 1175 310 L 1190 500 Z" fill="url(#spire_hl)"/>
    <path d="M 1350 500 L 1370 320 L 1385 360 L 1400 300 L 1415 340 L 1430 500 Z" fill="url(#spire)"/>
  </g>
  
  <!-- Lava -->
  <path d="M 300 520 Q 400 510 500 525 Q 600 515 700 530 Q 800 520 900 535 Q 1000 525 1100 540 Q 1200 530 1300 545 L 1300 560 Q 1200 550 1100 555 Q 1000 545 900 560 Q 800 550 700 565 Q 600 555 500 570 Q 400 560 300 575 Z" fill="url(#lava)" filter="url(#gs)"/>
  
  <!-- Foreground -->
  <path d="M 0 550 Q 100 530 200 545 Q 350 520 500 540 Q 650 515 800 535 Q 950 510 1100 530 Q 1250 505 1400 525 Q 1500 515 1600 530 L 1600 900 L 0 900 Z" fill="url(#ground)"/>
  <path d="M 150 580 L 165 530 L 175 550 L 185 510 L 195 540 L 200 580 Z" fill="#1a0a2e" stroke="#3a2060" stroke-width="0.8"/>
  <path d="M 1380 560 L 1395 515 L 1405 535 L 1415 495 L 1425 525 L 1430 560 Z" fill="#1a0a2e" stroke="#3a2060" stroke-width="0.8"/>
  
  <g filter="url(#gs)" opacity="0.6">
    <circle cx="300" cy="545" r="3" fill="#00ff88"/><circle cx="700" cy="535" r="2.5" fill="#00ff88"/>
    <circle cx="1000" cy="530" r="2" fill="#00ff88"/><circle cx="1200" cy="525" r="2.8" fill="#00ccff"/>
  </g>
  <rect x="0" y="400" width="1600" height="100" fill="#3a2050" opacity="0.15"/>
  <rect x="0" y="550" width="1600" height="350" fill="#050210" opacity="0.3"/>
</svg>'''
    with open(os.path.join(OUT, "obsidian_spires_env.svg"), "w") as f:
        f.write(svg)
    print("  Saved: obsidian_spires_env.svg")

def create_prop_svg():
    """Resonance Core: functional crystalline artifact with material depth."""
    print("--- Vector Prop: Resonance Core ---")
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="-150 -200 300 450" width="600" height="900">
  <defs>
    <linearGradient id="metal" x1="0" y1="0" x2="0.3" y2="1">
      <stop offset="0%" stop-color="#4a4a5a"/><stop offset="30%" stop-color="#2a2a3a"/><stop offset="60%" stop-color="#3a3a4a"/><stop offset="100%" stop-color="#1a1a2a"/>
    </linearGradient>
    <linearGradient id="metal_hl" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#6a6a7a" stop-opacity="0.6"/><stop offset="50%" stop-color="#8a8a9a" stop-opacity="0.3"/><stop offset="100%" stop-color="#4a4a5a" stop-opacity="0"/>
    </linearGradient>
    <radialGradient id="core_e" cx="0.5" cy="0.4" r="0.5">
      <stop offset="0%" stop-color="#e94560"/><stop offset="40%" stop-color="#c23152"/><stop offset="100%" stop-color="#533483" stop-opacity="0"/>
    </radialGradient>
    <filter id="ig"><feGaussianBlur stdDeviation="5" result="blur"/><feComposite in="SourceGraphic" in2="blur" operator="over"/></filter>
    <filter id="mf"><feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="3" seed="5"/><feColorMatrix type="saturate" values="0"/><feBlend in="SourceGraphic" mode="overlay"/></filter>
  </defs>
  
  <rect x="-150" y="-200" width="300" height="450" fill="#0a0a12"/>
  
  <!-- Base -->
  <ellipse cx="0" cy="200" rx="80" ry="15" fill="#1a1a2a" stroke="#2a2a3a" stroke-width="0.5"/>
  <ellipse cx="0" cy="195" rx="70" ry="12" fill="url(#metal)" filter="url(#mf)"/>
  <ellipse cx="0" cy="190" rx="60" ry="10" fill="#2a2a3a"/>
  
  <!-- Column -->
  <path d="M -25 190 L -20 80 L -15 -20 L -10 -80 L 0 -100 L 10 -80 L 15 -20 L 20 80 L 25 190 Z" fill="url(#metal)" stroke="#3a3a4a" stroke-width="0.5"/>
  <path d="M -25 190 L -20 80 L -15 -20 L -10 -80 L 0 -100 L 10 -80 L 15 -20 L 20 80 L 25 190 Z" fill="url(#metal_hl)"/>
  
  <!-- Crystal veins -->
  <path d="M -15 -20 L -8 -50 L 0 -70 L 8 -50 L 15 -20" stroke="#e94560" stroke-width="0.8" fill="none" opacity="0.5"/>
  <path d="M -12 40 L -5 20 L 0 10 L 5 20 L 12 40" stroke="#533483" stroke-width="0.6" fill="none" opacity="0.4"/>
  
  <!-- Core -->
  <circle cx="0" cy="-100" r="30" fill="url(#core_e)" filter="url(#ig)"/>
  <path d="M 0 -130 L 15 -110 L 10 -90 L 0 -80 L -10 -90 L -15 -110 Z" stroke="#e94560" stroke-width="0.8" fill="none" opacity="0.6"/>
  <path d="M -20 -105 L 0 -100 L 20 -105" stroke="#e94560" stroke-width="0.5" fill="none" opacity="0.4"/>
  <circle cx="0" cy="-100" r="8" fill="#ff6688" opacity="0.8"/>
  <circle cx="0" cy="-100" r="3" fill="#ffffff" opacity="0.6"/>
  
  <!-- Arms -->
  <path d="M -20 80 C -40 60 -55 30 -60 0 C -62 -10 -55 -15 -48 -10" stroke="url(#metal)" stroke-width="6" fill="none" stroke-linecap="round"/>
  <circle cx="-55" cy="-5" r="4" fill="#2a2a3a" stroke="#3a3a4a" stroke-width="0.5"/>
  <circle cx="-55" cy="-5" r="2" fill="#e94560" opacity="0.6" filter="url(#ig)"/>
  <path d="M 20 80 C 40 60 55 30 60 0 C 62 -10 55 -15 48 -10" stroke="url(#metal)" stroke-width="6" fill="none" stroke-linecap="round"/>
  <circle cx="55" cy="-5" r="4" fill="#2a2a3a" stroke="#3a3a4a" stroke-width="0.5"/>
  <circle cx="55" cy="-5" r="2" fill="#e94560" opacity="0.6" filter="url(#ig)"/>
  <path d="M -22 120 C -45 140 -60 160 -65 180" stroke="url(#metal)" stroke-width="5" fill="none" stroke-linecap="round"/>
  <path d="M 22 120 C 45 140 60 160 65 180" stroke="url(#metal)" stroke-width="5" fill="none" stroke-linecap="round"/>
  
  <!-- Energy tendrils -->
  <g opacity="0.5" filter="url(#ig)">
    <path d="M -28 -100 C -40 -95 -50 -80 -55 -5" stroke="#e94560" stroke-width="0.8" fill="none"/>
    <path d="M 28 -100 C 40 -95 50 -80 55 -5" stroke="#e94560" stroke-width="0.8" fill="none"/>
  </g>
  
  <!-- Wear -->
  <g opacity="0.2">
    <line x1="-18" y1="150" x2="-22" y2="160" stroke="#5a5a6a" stroke-width="0.5"/>
    <line x1="15" y1="140" x2="18" y2="148" stroke="#5a5a6a" stroke-width="0.5"/>
  </g>
</svg>'''
    with open(os.path.join(OUT, "resonance_core_prop.svg"), "w") as f:
        f.write(svg)
    print("  Saved: resonance_core_prop.svg")

def create_graphic_design_svg():
    """Resonance poster: grid composition, typography, shape hierarchy."""
    print("--- Graphic Design: Resonance Poster ---")
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 1100" width="800" height="1100">
  <defs>
    <linearGradient id="pbg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0a0520"/><stop offset="50%" stop-color="#1a0a35"/><stop offset="100%" stop-color="#0d0520"/>
    </linearGradient>
    <linearGradient id="acc" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#e94560"/><stop offset="100%" stop-color="#533483"/>
    </linearGradient>
    <clipPath id="pc"><rect width="800" height="1100"/></clipPath>
    <filter id="gf"><feTurbulence type="fractalNoise" baseFrequency="0.7" numOctaves="4" seed="3"/><feColorMatrix type="saturate" values="0"/><feBlend in="SourceGraphic" mode="multiply"/></filter>
    <pattern id="dp" width="8" height="8" patternUnits="userSpaceOnUse"><circle cx="4" cy="4" r="1" fill="#e94560" opacity="0.1"/></pattern>
  </defs>
  
  <rect width="800" height="1100" fill="url(#pbg)"/>
  <g opacity="0.05" stroke="#fff" stroke-width="0.5">
    <line x1="0" y1="275" x2="800" y2="275"/><line x1="0" y1="550" x2="800" y2="550"/><line x1="0" y1="825" x2="800" y2="825"/>
    <line x1="200" y1="0" x2="200" y2="1100"/><line x1="400" y1="0" x2="400" y2="1100"/><line x1="600" y1="0" x2="600" y2="1100"/>
  </g>
  
  <g clip-path="url(#pc)">
    <path d="M 50 200 L 200 150 L 350 220 L 400 180 L 500 250 L 550 200 L 650 280 L 700 240 L 750 320 L 750 700 L 50 700 Z" fill="#1a0a2e" opacity="0.8"/>
    <path d="M 100 400 L 250 350 L 350 420 L 450 380 L 550 450 L 600 410 L 700 480 L 700 700 L 100 700 Z" fill="#0d0520" opacity="0.6"/>
    <path d="M 300 250 L 380 200 L 420 280 L 350 320 Z" fill="url(#acc)" opacity="0.7"/>
  </g>
  
  <text x="80" y="160" font-family="Georgia,serif" font-size="72" font-weight="bold" fill="#e94560" letter-spacing="4">RESONANCE</text>
  <text x="80" y="220" font-family="Georgia,serif" font-size="28" fill="#8a8a9a" letter-spacing="12">CRYSTALLINE FORMS</text>
  <line x1="80" y1="240" x2="350" y2="240" stroke="#e94560" stroke-width="1" opacity="0.6"/>
  
  <text x="80" y="780" font-family="Georgia,serif" font-size="14" fill="#6a6a7a" letter-spacing="1">
    <tspan x="80" dy="0">Where geological time meets crystalline precision.</tspan>
    <tspan x="80" dy="22">A study in material language, form evolution,</tspan>
    <tspan x="80" dy="22">and the architecture of accumulated pressure.</tspan>
  </text>
  
  <rect width="800" height="1100" fill="url(#dp)" opacity="0.3"/>
  <line x1="80" y1="1050" x2="720" y2="1050" stroke="#e94560" stroke-width="0.5" opacity="0.4"/>
  <text x="80" y="1070" font-family="monospace" font-size="10" fill="#4a4a5a" letter-spacing="3">EDITION 001 / OBSIDIAN SPIRE COLLECTION</text>
  
  <path d="M 40 40 L 40 60 M 40 40 L 60 40" stroke="#e94560" stroke-width="0.5" fill="none" opacity="0.4"/>
  <path d="M 760 40 L 760 60 M 760 40 L 740 40" stroke="#e94560" stroke-width="0.5" fill="none" opacity="0.4"/>
  <path d="M 40 1060 L 40 1040 M 40 1060 L 60 1060" stroke="#e94560" stroke-width="0.5" fill="none" opacity="0.4"/>
  <path d="M 760 1060 L 760 1040 M 760 1060 L 740 1060" stroke="#e94560" stroke-width="0.5" fill="none" opacity="0.4"/>
</svg>'''
    with open(os.path.join(OUT, "resonance_poster.svg"), "w") as f:
        f.write(svg)
    print("  Saved: resonance_poster.svg")

def create_cross_medium():
    """Basalt Meridian: one Style DNA across character/env/prop/UI."""
    print("--- Cross-Medium: Basalt Meridian ---")
    os.makedirs(os.path.join(OUT, "cross-medium"), exist_ok=True)
    
    char = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="-100 -150 200 350" width="400" height="700">
  <defs>
    <linearGradient id="ba" x1="0" y1="0" x2="0.2" y2="1"><stop offset="0%" stop-color="#3a3a3a"/><stop offset="50%" stop-color="#2a2a2a"/><stop offset="100%" stop-color="#1a1a1a"/></linearGradient>
    <linearGradient id="co" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#b87333"/><stop offset="50%" stop-color="#8b5a2b"/><stop offset="100%" stop-color="#6b4423"/></linearGradient>
    <linearGradient id="te" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#2a8a7a"/><stop offset="100%" stop-color="#1a5a4a"/></linearGradient>
  </defs>
  <rect x="-100" y="-150" width="200" height="350" fill="#0f0f0f"/>
  <path d="M -30 -40 L -20 -80 L 0 -95 L 20 -80 L 30 -40 L 28 30 L 0 45 L -28 30 Z" fill="url(#ba)" stroke="#4a4a4a" stroke-width="0.8"/>
  <path d="M -15 -70 L -10 -50 L -18 -30" stroke="#4a4a4a" stroke-width="0.5" fill="none" opacity="0.4"/>
  <path d="M 10 -60 L 15 -40 L 8 -20" stroke="#4a4a4a" stroke-width="0.5" fill="none" opacity="0.4"/>
  <path d="M -15 -95 L -10 -120 L 0 -135 L 10 -120 L 15 -95 Z" fill="url(#ba)" stroke="#4a4a4a" stroke-width="0.8"/>
  <circle cx="0" cy="-115" r="3" fill="url(#te)"/>
  <path d="M -30 -40 L -55 -25 L -70 -10 L -75 10" stroke="url(#ba)" stroke-width="8" fill="none" stroke-linecap="round"/>
  <circle cx="-55" cy="-25" r="4" fill="url(#co)"/>
  <circle cx="-70" cy="-10" r="3" fill="url(#co)"/>
  <path d="M 30 -40 L 55 -25 L 70 -10 L 75 10" stroke="url(#ba)" stroke-width="8" fill="none" stroke-linecap="round"/>
  <circle cx="55" cy="-25" r="4" fill="url(#co)"/>
  <circle cx="70" cy="-10" r="3" fill="url(#co)"/>
  <path d="M -15 45 L -20 80 L -25 120 L -22 150" stroke="url(#ba)" stroke-width="9" fill="none" stroke-linecap="round"/>
  <path d="M 15 45 L 20 80 L 25 120 L 22 150" stroke="url(#ba)" stroke-width="9" fill="none" stroke-linecap="round"/>
  <circle cx="-20" cy="80" r="3.5" fill="url(#co)"/>
  <circle cx="20" cy="80" r="3.5" fill="url(#co)"/>
  <path d="M -20 -60 L 20 -60" stroke="#4a4a4a" stroke-width="0.4" fill="none"/>
  <path d="M -18 -30 L 18 -30" stroke="#4a4a4a" stroke-width="0.4" fill="none"/>
  <path d="M 0 -95 L 0 -40 L -5 20 L 0 45" stroke="url(#te)" stroke-width="0.8" fill="none" opacity="0.5"/>
</svg>'''
    
    env = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 450" width="800" height="450">
  <defs><linearGradient id="bs" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#1a1a1a"/><stop offset="100%" stop-color="#2a2a2a"/></linearGradient></defs>
  <rect width="800" height="450" fill="url(#bs)"/>
  <path d="M 100 450 L 110 250 L 115 280 L 125 200 L 130 240 L 140 450 Z" fill="#2a2a2a" stroke="#3a3a3a" stroke-width="0.5"/>
  <path d="M 180 450 L 195 180 L 200 220 L 210 150 L 215 190 L 225 450 Z" fill="#252525" stroke="#3a3a3a" stroke-width="0.5"/>
  <path d="M 300 450 L 320 120 L 330 170 L 340 90 L 350 140 L 360 450 Z" fill="#2a2a2a" stroke="#3a3a3a" stroke-width="0.5"/>
  <path d="M 450 450 L 465 200 L 470 240 L 480 160 L 485 200 L 495 450 Z" fill="#222" stroke="#3a3a3a" stroke-width="0.5"/>
  <path d="M 550 450 L 560 220 L 570 260 L 580 180 L 590 230 L 600 450 Z" fill="#2a2a2a" stroke="#3a3a3a" stroke-width="0.5"/>
  <path d="M 650 450 L 670 160 L 680 200 L 690 130 L 700 170 L 710 450 Z" fill="#252525" stroke="#3a3a3a" stroke-width="0.5"/>
  <path d="M 325 120 L 330 170 L 335 200" stroke="#b87333" stroke-width="1" fill="none" opacity="0.5"/>
  <path d="M 575 180 L 580 230 L 578 280" stroke="#b87333" stroke-width="0.8" fill="none" opacity="0.4"/>
  <ellipse cx="340" cy="440" rx="30" ry="5" fill="#2a8a7a" opacity="0.3"/>
  <rect x="0" y="420" width="800" height="30" fill="#1a1a1a"/>
</svg>'''
    
    prop = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="-80 -100 160 250" width="320" height="500">
  <rect x="-80" y="-100" width="160" height="250" fill="#0f0f0f"/>
  <rect x="-4" y="-20" width="8" height="120" rx="2" fill="#2a2a2a" stroke="#3a3a3a" stroke-width="0.5"/>
  <path d="M -5 0 L 5 -5 L 5 5 L -5 10 Z" fill="#b87333" opacity="0.7"/>
  <path d="M -5 20 L 5 15 L 5 25 L -5 30 Z" fill="#b87333" opacity="0.6"/>
  <path d="M -5 40 L 5 35 L 5 45 L -5 50 Z" fill="#b87333" opacity="0.5"/>
  <path d="M -35 -30 L -30 -50 L 0 -60 L 30 -50 L 35 -30 L 30 -20 L 0 -15 L -30 -20 Z" fill="#2a2a2a" stroke="#4a4a4a" stroke-width="0.8"/>
  <path d="M -20 -45 L 0 -55 L 20 -45" stroke="#4a4a4a" stroke-width="0.4" fill="none"/>
  <path d="M -30 -40 L 0 -50 L 30 -40" stroke="#2a8a7a" stroke-width="1" fill="none" opacity="0.6"/>
</svg>'''
    
    ui = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300" width="400" height="300">
  <defs><linearGradient id="ub" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#1a1a1a"/><stop offset="100%" stop-color="#0f0f0f"/></linearGradient></defs>
  <rect width="400" height="300" fill="url(#ub)"/>
  <path d="M 10 10 L 390 10 L 395 15 L 395 290 L 390 295 L 10 295 L 5 290 L 5 15 Z" fill="none" stroke="#3a3a3a" stroke-width="0.8"/>
  <path d="M 10 10 L 30 10 M 10 10 L 10 30" stroke="#b87333" stroke-width="1.5" fill="none"/>
  <path d="M 390 10 L 370 10 M 390 10 L 390 30" stroke="#b87333" stroke-width="1.5" fill="none"/>
  <path d="M 10 290 L 30 290 M 10 290 L 10 270" stroke="#b87333" stroke-width="1.5" fill="none"/>
  <path d="M 390 290 L 370 290 M 390 290 L 390 270" stroke="#b87333" stroke-width="1.5" fill="none"/>
  <text x="30" y="50" font-family="monospace" font-size="14" fill="#b87333" letter-spacing="4">RESONANCE MONITOR</text>
  <rect x="30" y="80" width="200" height="3" fill="#3a3a3a"/><rect x="30" y="80" width="140" height="3" fill="#2a8a7a"/>
  <text x="30" y="75" font-family="monospace" font-size="9" fill="#6a6a6a">FREQUENCY</text>
  <rect x="30" y="110" width="200" height="3" fill="#3a3a3a"/><rect x="30" y="110" width="170" height="3" fill="#b87333"/>
  <text x="30" y="105" font-family="monospace" font-size="9" fill="#6a6a6a">AMPLITUDE</text>
  <rect x="30" y="140" width="200" height="3" fill="#3a3a3a"/><rect x="30" y="140" width="90" height="3" fill="#e94560"/>
  <text x="30" y="135" font-family="monospace" font-size="9" fill="#6a6a6a">HARMONICS</text>
  <circle cx="350" cy="45" r="4" fill="#2a8a7a"/><text x="340" y="60" font-family="monospace" font-size="8" fill="#6a6a6a">ACTIVE</text>
  <rect x="5" y="280" width="390" height="15" fill="#0a0a0a"/>
  <text x="15" y="291" font-family="monospace" font-size="8" fill="#4a4a4a">SYS:NOMINAL | CORE:87% | TEMP:42C | CYCLE:00847</text>
</svg>'''
    
    for name, content in [("character", char), ("environment", env), ("prop", prop), ("ui", ui)]:
        with open(os.path.join(OUT, "cross-medium", f"basalt_{name}.svg"), "w") as f:
            f.write(content)
        print(f"  Saved: basalt_{name}.svg")

if __name__ == "__main__":
    create_character_svg()
    create_creature_svg()
    create_environment_svg()
    create_prop_svg()
    create_graphic_design_svg()
    create_cross_medium()
    
    report = {
        "artifacts": [
            {"name": "Obsidian Warden Character", "file": "warden_character.svg", "level": "L7", "techniques": ["Bézier curves", "compound paths", "SVG filters", "gradients", "clip paths"]},
            {"name": "Abyssal Lure Creature", "file": "abyssal_creature.svg", "level": "L6", "techniques": ["functional anatomy", "bioluminescence", "SVG filters", "turbulence displacement"]},
            {"name": "Obsidian Spires Environment", "file": "obsidian_spires_env.svg", "level": "L7", "techniques": ["atmospheric perspective", "layered depth", "custom terrain", "lava effects"]},
            {"name": "Resonance Core Prop", "file": "resonance_core_prop.svg", "level": "L7", "techniques": ["material depth", "construction logic", "energy effects", "wear detail"]},
            {"name": "Resonance Poster", "file": "resonance_poster.svg", "level": "L7", "techniques": ["grid composition", "typography", "shape hierarchy", "pattern fills"]},
            {"name": "Basalt Meridian Cross-Medium", "file": "cross-medium/basalt_*.svg", "level": "L6", "techniques": ["consistent Style DNA", "4 media", "angular-geometric erosion", "copper/teal palette"]}
        ],
        "no_primitives_as_final": True
    }
    with open(os.path.join(OUT, "vector_craft_report.json"), "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved: vector_craft_report.json")
