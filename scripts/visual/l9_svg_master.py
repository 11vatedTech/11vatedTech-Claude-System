"""L9 Master Pass on SVG Vesper Alchemist."""
import re

with open('artifacts/visual/final-craft/heroes/vesper_alchemist.svg', 'r') as f:
    svg = f.read()

# 1. ENHANCE LEGS: Replace simple stroke paths with articulated construction
old_legs = """  <!-- LEGS: Articulated obsidian plates -->
  <g>
    <!-- Left leg -->
    <path d="M 550 650 C 540 700 530 750 525 800 C 520 850 530 880 545 900"
          stroke="url(#obs_body)" stroke-width="14" fill="none" stroke-linecap="round"/>
    <!-- Knee joint (copper) -->
    <circle cx="530" cy="760" r="8" fill="url(#copper_body)" stroke="#6b4423" stroke-width="1"/>
    <!-- Boot -->
    <path d="M 540 895 L 520 910 L 510 920 L 560 920 L 555 900 Z" fill="#1a1a2e" stroke="#0a0a18" stroke-width="1"/>
    
    <!-- Right leg -->
    <path d="M 660 650 C 670 700 680 750 685 800 C 690 850 680 880 665 900"
          stroke="url(#obs_body)" stroke-width="14" fill="none" stroke-linecap="round"/>
    <!-- Knee joint (copper) -->
    <circle cx="680" cy="760" r="8" fill="url(#copper_body)" stroke="#6b4423" stroke-width="1"/>
    <!-- Boot -->
    <path d="M 670 895 L 690 910 L 700 920 L 650 920 L 655 900 Z" fill="#1a1a2e" stroke="#0a0a18" stroke-width="1"/>
  </g>"""

new_legs = """  <!-- LEGS: Articulated obsidian plates with proper joints -->
  <g>
    <!-- Left leg: thigh plate -->
    <path d="M 548 650 C 542 670 536 690 532 710 C 528 730 526 748 528 758"
          stroke="url(#obs_body)" stroke-width="16" fill="none" stroke-linecap="round"/>
    <!-- Left leg: shin plate -->
    <path d="M 528 768 C 526 785 524 805 524 825 C 524 845 528 865 535 885"
          stroke="url(#obs_body)" stroke-width="14" fill="none" stroke-linecap="round"/>
    <!-- Left knee joint (copper, larger) -->
    <ellipse cx="528" cy="763" rx="10" ry="7" fill="url(#copper_body)" stroke="#6b4423" stroke-width="1"/>
    <ellipse cx="528" cy="763" rx="6" ry="4" fill="url(#copper_hl)" opacity="0.3"/>
    <!-- Left ankle joint -->
    <ellipse cx="535" cy="888" rx="7" ry="5" fill="url(#copper_body)" stroke="#6b4423" stroke-width="0.8"/>
    <!-- Left boot: articulated plates -->
    <path d="M 530 892 L 515 905 L 508 918 L 512 922 L 558 922 L 562 918 L 555 905 L 545 892 Z"
          fill="#1a1a2e" stroke="#0a0a18" stroke-width="1"/>
    <path d="M 520 908 L 515 918 L 555 918 L 550 908 Z" fill="#16162a" stroke="#2a2a4a" stroke-width="0.5"/>
    <!-- Boot highlight -->
    <path d="M 525 910 L 520 918" stroke="#3a3a5a" stroke-width="0.6" fill="none" opacity="0.4"/>
    
    <!-- Right leg: thigh plate -->
    <path d="M 662 650 C 668 670 674 690 678 710 C 682 730 684 748 682 758"
          stroke="url(#obs_body)" stroke-width="16" fill="none" stroke-linecap="round"/>
    <!-- Right leg: shin plate -->
    <path d="M 682 768 C 684 785 686 805 686 825 C 686 845 682 865 675 885"
          stroke="url(#obs_body)" stroke-width="14" fill="none" stroke-linecap="round"/>
    <!-- Right knee joint -->
    <ellipse cx="682" cy="763" rx="10" ry="7" fill="url(#copper_body)" stroke="#6b4423" stroke-width="1"/>
    <ellipse cx="682" cy="763" rx="6" ry="4" fill="url(#copper_hl)" opacity="0.3"/>
    <!-- Right ankle joint -->
    <ellipse cx="675" cy="888" rx="7" ry="5" fill="url(#copper_body)" stroke="#6b4423" stroke-width="0.8"/>
    <!-- Right boot -->
    <path d="M 670 892 L 685 905 L 692 918 L 688 922 L 642 922 L 638 918 L 645 905 L 655 892 Z"
          fill="#1a1a2e" stroke="#0a0a18" stroke-width="1"/>
    <path d="M 680 908 L 685 918 L 645 918 L 650 908 Z" fill="#16162a" stroke="#2a2a4a" stroke-width="0.5"/>
    <path d="M 675 910 L 680 918" stroke="#3a3a5a" stroke-width="0.6" fill="none" opacity="0.4"/>
  </g>"""

svg = svg.replace(old_legs, new_legs)

# 2. ENHANCE ARMOR: Add surface variation, wear marks, highlights
old_armor_detail = """    <!-- Armor surface detail \u2014 volcanic texture lines -->
    <path d="M 560 420 C 570 440 565 460 555 480" stroke="#2a2a4a" stroke-width="0.8" fill="none" opacity="0.5"/>
    <path d="M 620 410 C 630 430 625 450 615 470" stroke="#2a2a4a" stroke-width="0.8" fill="none" opacity="0.5"/>
    <path d="M 590 400 C 595 420 590 440 580 460" stroke="#2a2a4a" stroke-width="0.6" fill="none" opacity="0.4"/>"""

new_armor_detail = """    <!-- Armor surface detail \u2014 volcanic texture + wear + highlights -->
    <!-- Fracture lines (conchoidal fracture pattern) -->
    <path d="M 560 420 C 570 440 565 460 555 480" stroke="#2a2a4a" stroke-width="0.8" fill="none" opacity="0.5"/>
    <path d="M 620 410 C 630 430 625 450 615 470" stroke="#2a2a4a" stroke-width="0.8" fill="none" opacity="0.5"/>
    <path d="M 590 400 C 595 420 590 440 580 460" stroke="#2a2a4a" stroke-width="0.6" fill="none" opacity="0.4"/>
    <!-- Secondary fracture network -->
    <path d="M 575 430 L 585 445 L 578 460" stroke="#1e1e3a" stroke-width="0.5" fill="none" opacity="0.4"/>
    <path d="M 610 425 L 618 440 L 612 455" stroke="#1e1e3a" stroke-width="0.5" fill="none" opacity="0.4"/>
    <!-- Wear scratches (horizontal, shallow) -->
    <path d="M 545 450 L 565 448" stroke="#3a3a5a" stroke-width="0.4" fill="none" opacity="0.3"/>
    <path d="M 625 445 L 645 443" stroke="#3a3a5a" stroke-width="0.4" fill="none" opacity="0.3"/>
    <path d="M 555 470 L 575 468" stroke="#3a3a5a" stroke-width="0.3" fill="none" opacity="0.25"/>
    <!-- Specular highlights on armor edges -->
    <path d="M 540 440 C 538 450 536 460 535 470" stroke="#4a4a6a" stroke-width="0.6" fill="none" opacity="0.3"/>
    <path d="M 700 440 C 702 450 704 460 705 470" stroke="#4a4a6a" stroke-width="0.6" fill="none" opacity="0.3"/>"""

svg = svg.replace(old_armor_detail, new_armor_detail)

# 3. ENHANCE CAPE: Add richer fold details
old_cape_folds = """    <!-- Cape fold details -->
    <path d="M 460 500 C 470 520 465 540 455 560" stroke="#2a2a3a" stroke-width="1.5" fill="none" opacity="0.6"/>
    <path d="M 480 550 C 490 570 485 590 475 610" stroke="#2a2a3a" stroke-width="1" fill="none" opacity="0.5"/>
    <path d="M 500 600 C 510 620 505 640 495 660" stroke="#2a2a3a" stroke-width="0.8" fill="none" opacity="0.4"/>"""

new_cape_folds = """    <!-- Cape fold details: deep folds + highlight ridges + fabric texture -->
    <!-- Deep fold shadows -->
    <path d="M 460 500 C 470 520 465 540 455 560" stroke="#141424" stroke-width="1.8" fill="none" opacity="0.7"/>
    <path d="M 480 550 C 490 570 485 590 475 610" stroke="#141424" stroke-width="1.2" fill="none" opacity="0.6"/>
    <path d="M 500 600 C 510 620 505 640 495 660" stroke="#141424" stroke-width="1" fill="none" opacity="0.5"/>
    <!-- Fold highlight ridges (where light catches) -->
    <path d="M 465 505 C 475 525 470 545 460 565" stroke="#3a3a5a" stroke-width="0.6" fill="none" opacity="0.3"/>
    <path d="M 485 555 C 495 575 490 595 480 615" stroke="#3a3a5a" stroke-width="0.5" fill="none" opacity="0.25"/>
    <!-- Secondary fold tension lines -->
    <path d="M 450 520 C 458 535 455 550 448 565" stroke="#2a2a3a" stroke-width="0.6" fill="none" opacity="0.35"/>
    <path d="M 470 570 C 478 585 475 600 468 615" stroke="#2a2a3a" stroke-width="0.5" fill="none" opacity="0.3"/>
    <!-- Fabric weave texture (very subtle) -->
    <path d="M 455 530 L 465 528" stroke="#2a2a3a" stroke-width="0.3" fill="none" opacity="0.2"/>
    <path d="M 475 580 L 485 578" stroke="#2a2a3a" stroke-width="0.3" fill="none" opacity="0.2"/>
    <path d="M 495 630 L 505 628" stroke="#2a2a3a" stroke-width="0.3" fill="none" opacity="0.2"/>"""

svg = svg.replace(old_cape_folds, new_cape_folds)

# 4. ENHANCE HELM: Add surface detail
old_helm_detail = """    <!-- Helm surface detail -->
    <path d="M 580 280 C 590 270 610 268 625 275" stroke="#3a3a5a" stroke-width="0.8" fill="none" opacity="0.5"/>
    <path d="M 570 310 C 580 300 600 298 615 305" stroke="#3a3a5a" stroke-width="0.6" fill="none" opacity="0.4"/>"""

new_helm_detail = """    <!-- Helm surface detail: fracture + wear + specular -->
    <path d="M 580 280 C 590 270 610 268 625 275" stroke="#3a3a5a" stroke-width="0.8" fill="none" opacity="0.5"/>
    <path d="M 570 310 C 580 300 600 298 615 305" stroke="#3a3a5a" stroke-width="0.6" fill="none" opacity="0.4"/>
    <!-- Helm fracture network -->
    <path d="M 590 275 L 598 285 L 592 295" stroke="#1e1e3a" stroke-width="0.4" fill="none" opacity="0.35"/>
    <path d="M 620 280 L 625 290 L 618 298" stroke="#1e1e3a" stroke-width="0.4" fill="none" opacity="0.3"/>
    <!-- Helm specular edge -->
    <path d="M 575 275 C 580 268 595 265 610 268" stroke="#4a4a6a" stroke-width="0.5" fill="none" opacity="0.35"/>
    <!-- Helm wear mark -->
    <path d="M 600 305 L 612 303" stroke="#3a3a5a" stroke-width="0.4" fill="none" opacity="0.25"/>"""

svg = svg.replace(old_helm_detail, new_helm_detail)

# 5. ENHANCE WORKSHOP: Add more atmosphere
old_workshop = """  <!-- WORKSHOP ELEMENTS: Shelves with crystal specimens -->
  <g opacity="0.3">
    <rect x="50" y="300" width="200" height="8" fill="#2a2a3a"/>
    <rect x="50" y="500" width="200" height="8" fill="#2a2a3a"/>
    <!-- Crystal specimens on shelves -->
    <path d="M 80 300 L 90 260 L 100 300 Z" fill="#6a5acd" opacity="0.4"/>
    <path d="M 120 300 L 128 270 L 136 300 Z" fill="#7b68ee" opacity="0.3"/>
    <path d="M 160 300 L 170 250 L 180 300 Z" fill="#9370db" opacity="0.35"/>
    <path d="M 80 500 L 92 460 L 104 500 Z" fill="#6a5acd" opacity="0.3"/>
    <path d="M 140 500 L 150 470 L 160 500 Z" fill="#7b68ee" opacity="0.25"/>
  </g>"""

new_workshop = """  <!-- WORKSHOP ELEMENTS: Shelves with crystal specimens + tools + atmosphere -->
  <g opacity="0.35">
    <!-- Shelving structure -->
    <rect x="50" y="300" width="200" height="8" fill="#2a2a3a"/>
    <rect x="50" y="500" width="200" height="8" fill="#2a2a3a"/>
    <rect x="48" y="300" width="4" height="208" fill="#1e1e2e"/>
    <!-- Crystal specimens on shelves (varied sizes) -->
    <path d="M 80 300 L 90 260 L 100 300 Z" fill="#6a5acd" opacity="0.4"/>
    <path d="M 120 300 L 128 270 L 136 300 Z" fill="#7b68ee" opacity="0.3"/>
    <path d="M 160 300 L 170 250 L 180 300 Z" fill="#9370db" opacity="0.35"/>
    <path d="M 200 300 L 208 275 L 216 300 Z" fill="#6a5acd" opacity="0.25"/>
    <path d="M 80 500 L 92 460 L 104 500 Z" fill="#6a5acd" opacity="0.3"/>
    <path d="M 140 500 L 150 470 L 160 500 Z" fill="#7b68ee" opacity="0.25"/>
    <path d="M 180 500 L 188 478 L 196 500 Z" fill="#9370db" opacity="0.2"/>
    <!-- Tools on shelf -->
    <rect x="105" y="494" width="25" height="4" rx="1" fill="#3a3a4a" opacity="0.5"/>
    <rect x="165" y="496" width="15" height="3" rx="1" fill="#4a4a5a" opacity="0.4"/>
    <!-- Hanging chains/hooks -->
    <path d="M 180 280 L 180 300" stroke="#3a3a4a" stroke-width="0.8" fill="none" opacity="0.3"/>
    <path d="M 180 280 L 185 278" stroke="#3a3a4a" stroke-width="0.6" fill="none" opacity="0.3"/>
  </g>"""

svg = svg.replace(old_workshop, new_workshop)

# 6. Add SECOND ANVIL / TOOL RACK for environment depth
old_anvil = """  <!-- ANVIL (left of character) -->"""

new_anvil = """  <!-- TOOL RACK (right background) -->
  <g opacity="0.2">
    <rect x="1300" y="350" width="8" height="300" fill="#1e1e2e"/>
    <rect x="1350" y="380" width="6" height="250" fill="#1e1e2e"/>
    <!-- Hanging tools -->
    <path d="M 1304 360 L 1304 400 L 1310 400 L 1310 360" stroke="#3a3a4a" stroke-width="0.8" fill="none" opacity="0.4"/>
    <path d="M 1353 390 L 1353 430 L 1357 430 L 1357 390" stroke="#3a3a4a" stroke-width="0.6" fill="none" opacity="0.3"/>
    <!-- Small crystal on rack -->
    <path d="M 1308 355 L 1312 340 L 1316 355 Z" fill="#6a5acd" opacity="0.3"/>
  </g>
  
  <!-- ANVIL (left of character) -->"""

svg = svg.replace(old_anvil, new_anvil)

# Write enhanced file
with open('artifacts/visual/final-craft/heroes/vesper_alchemist.svg', 'w') as f:
    f.write(svg)

print(f"L9 Master Pass complete: {len(svg)} bytes")
print("Enhancements:")
print("  1. Legs: articulated thigh/shin plates, copper knee/ankle joints, boot detail")
print("  2. Armor: fracture network, wear scratches, specular highlights")
print("  3. Cape: deep fold shadows, highlight ridges, tension lines, fabric weave")
print("  4. Helm: fracture network, specular edge, wear marks")
print("  5. Workshop: shelving structure, varied crystals, tools, hanging chains")
print("  6. Environment: tool rack with hanging tools, background depth")
