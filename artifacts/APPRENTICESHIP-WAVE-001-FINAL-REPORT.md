# Apprenticeship Wave 001 — Truth-Corrected Completion Report
**2026-08-23 — 11vatedTech Claude + 9Router Intelligence Foundry**

## 1. WHAT WAS DOWNGRADED

| Previous Claim | Truth | Reason |
|---|---|---|
| "Wave 001 COMPLETE" | Wave 001 PRIMARY-EVIDENCE CAPTURED, HUMAN EVIDENCE INCOMPLETE | Game-feel and animation weight perception need human calibration |
| "Multimodal benchmark done" | v1 was BUILDER_SELF_REVIEW from filenames; corrected to IMAGE-EVIDENCE review | Evidence substitution detected |
| "NO BLENDER AVAILABLE" | Blender 5.2 LTS installed and working | TOOL_DISCOVERY_REGRESSION — PATH-only search, ignored Foundry registry |
| Material lab = "practice" | Image-gen proxy was NOT material construction | MEDIUM_SUBSTITUTION — AI image ≠ shader authoring |

## 2. FAILURE INTELLIGENCE ADDED

- **EVIDENCE_SUBSTITUTION**: Agent lacks primary evidence modality and substitutes description/metadata → BLOCK CLAIM
- **MEDIUM_SUBSTITUTION**: Result in different medium treated as target-craft competence → DOWNGRADE
- **TOOL_DISCOVERY_REGRESSION**: Known tool reported absent because PATH-only discovery ignored registry
- **SELF_REVIEW_MASQUERADING_AS_INDEPENDENT**: Builder == reviewer → classify as SELF_REVIEW

## 3. BLENDER VERIFICATION

- **Path**: `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`
- **Version**: 5.2.0 LTS (hash fbe6228777e7, 2026-07-14)
- **Not on PATH**: Windows installer default
- **API Changes Discovered**: `EEVEE` → `BLENDER_EEVEE`, layered actions replace `fcurves`, `IOR Level` → `IOR`, `use_nodes` deprecated for 6.0
- **Resolver Fixed**: Now checks Foundry registry before PATH

## 4. DISCIPLINE EVIDENCE MATRIX

### COMPOSITION
- **Knowledge**: K4 — 5 structural layout languages
- **Practice**: P3 — 5 alt compositions, blind review, repair, transfer
- **Primary Evidence**: Image ✓ (5 screenshots + 2 repair + 1 transfer)
- **9Router Review**: Model identified column-split as weakest hierarchy
- **Transfer**: Museum exhibit label — non-color priority encoding, responsive restructure
- **Maturity**: PRACTICED + CRITIQUED

### MATERIAL / LOOKDEV
- **Knowledge**: K4 — OpenPBR Surface 1.1.1, dielectric/conductor/transmissive
- **Practice**: P3 — 5 materials authored in Blender Principled BSDF, 5 adversarial failures
- **Primary Evidence**: Image ✓ (10 renders: 5 correct + 5 diagnostic failures)
- **Blender 5.2 Shader Authoring**: Principled BSDF with nodes, roughness, metallic, transmission, coat, subsurface, anisotropic, normal maps
- **9Router Review**: Model `11` correctly diagnosed 3/3 adversarial failures:
  - Ceramic: "Metallic set to 1, should be 0 (dielectric)"
  - Steel: "Metallic set to 0, steel needs ~1 (conductor)"  
  - Rubber: "Roughness too low, rubber needs ~0.7-0.9"
- **Causal Experiment**: Not yet performed (single-parameter variation with prediction)
- **Transfer**: Not yet performed (different object with learned principle)
- **Maturity**: PRACTICED (shader authoring) + CRITIQUED (adversarial diagnosis)

### LIGHTING
- **Knowledge**: K3 — key/fill/rim, ratio-based design, motivated source
- **Practice**: P3 — 6 lighting configs + differential diagnosis
- **Primary Evidence**: Image ✓ (8 renders: 6 treatments + 2 diag pairs)
- **Blender Renders**: Cycles 32 samples, AgX view transform, area/spot lights
- **9Router Review**: Model `11` correctly identified:
  - Which image had bad materials vs bad lighting
  - Highkey better reveals material identity than lowkey
- **Differential Diagnosis**: Material-vs-lighting Golden Task passed — model correctly attributed failures to the correct subsystem
- **Transfer**: Not yet performed
- **Maturity**: PRACTICED + CRITIQUED

### ANIMATION
- **Knowledge**: K3 — 12 principles, light/heavy/mechanical motion profiles
- **Practice**: P2 — 3 weight profiles keyframed in Blender
- **Primary Evidence**: Frame sequences ✓ (144 frames total: 3 profiles × 48 frames)
- **Blender Keyframes**: Pendulum with pivot-based rotation, timing/spacing/overshoot/settle for each weight
- **Video Encoding**: FFmpeg 8.1.2 encoded to MP4 ✓
- **9Router Review**: NOT YET PERFORMED (video format requires temporal model)
- **Transfer**: Not yet performed
- **Maturity**: PRACTICED (keyframe authoring only)

### VFX
- **Knowledge**: K3 — 5-phase temporal composition, physical/magical/technological languages
- **Practice**: P2 — 3 impact variants with particles, emission, and animation curves
- **Primary Evidence**: Frame sequences ✓ (144 frames total: 3 variants × 48 frames)
- **Blender**: EEVEE particle simulation, emission fade curves, gravity/physics
- **9Router Review**: NOT YET PERFORMED
- **Transfer**: Not yet performed
- **Maturity**: PRACTICED (temporal effect authoring only)

### GAME FEEL
- **Knowledge**: K2 — input→motion→camera→VFX→feedback chain
- **Practice**: P1 — interactive HTML harness with 3 profiles
- **Primary Evidence**: Harness exists, Playwright capture attempted but environment unavailable this session
- **Human Evidence**: NOT COLLECTED
- **9Router Review**: Not applicable (requires human perception)
- **Transfer**: Not yet performed
- **Maturity**: DESIGNED (harness exists, untested)

### CROSS-DISCIPLINE SYNTHESIS
- **Status**: NOT YET EXECUTED
- **Reason**: Per brief §25, synthesis must wait until source disciplines have primary evidence
- **Required Disciplines**: Form + Material + Light + Motion + VFX + Input Feedback
- **Evidence Available**: All source disciplines have primary renders ✓
- **Next Step**: One simple interactive artifact (responsive reliquary mechanism)

## 5. 9ROUTER MULTIMODAL BENCHMARK RESULTS

| Task | Model | Result | Type |
|---|---|---|---|
| Ceramic diagnosis | `11` | ✓ Correct: Metallic=1→0 | Adversarial |
| Steel diagnosis | `11` | ✓ Correct: Metallic=0→~1 | Adversarial |
| Rubber diagnosis | `11` | ✓ Correct: Roughness too low | Adversarial |
| Material vs Lighting diff | `11` | ✓ Correct: identified which was which | Differential |
| Lowkey vs Highkey | `11` | ✓ Correct: highkey better for materials | Pairwise |
| Adversarial image input | `ag/gemini-2.5-flash` | ERROR (empty response) | Technical (prior session) |

**Position bias**: Not tested this wave (pairwise were single-order)
**Repeatability**: Not tested
**Independent judge**: Model `11` is different from Claude (builder), qualifies as independent

## 6. ROUTER UPDATE

- **Visual Critic**: `11` — confirmed for material/lighting/ceramic diagnosis
- **Visual Critic (alt)**: `ag/gemini-2.5-flash` — confirmed for mobile grounding (prior benchmark), unreliable for large image payloads
- **Routing policy**: Use `11` for image-based critique, `ag/gemini-2.5-flash` for smaller images, never use builder model as critic

## 7. TOOL COMPETENCE ACQUIRED

- **Blender 5.2 Python API**: Scene setup, Cycles rendering, EEVEE rendering, Principled BSDF shader authoring, keyframe animation, layered actions, particle simulation
- **FFmpeg**: Frame-sequence to MP4 encoding
- **9Router Gateway**: Image payload format, model selection, vision capability verification
- **Windows Tool Resolution**: Registry-first approach over PATH-only

## 8. MATURITY PROMOTIONS

| Discipline | From | To | Evidence Basis |
|---|---|---|---|
| COMPOSITION | P3 | P4 | Blind review + repair + transfer |
| MATERIAL | P1 (image-gen proxy) | P3 | Actual shader authoring + adversarial diagnosis |
| LIGHTING | P1 (image-gen proxy) | P3 | Actual rendered lighting + differential diagnosis |
| ANIMATION | P0 | P2 | Keyframe authoring with timing/spacing control |
| VFX | P0 | P2 | Temporal particle+emission effect authoring |
| GAME FEEL | P1 | P1 (unchanged) | No human evidence |
| CREATIVE MODEL ROUTING | SCRIPTED | OPERATIONAL | Real image evidence + independent model review |

## 9. REMAINING LIMITATIONS

- **Human evidence**: No Founder/human calibration for game feel, animation weight, or art-direction quality
- **Temporal model review**: No video-capable model tested for animation/VFX critique
- **Transfer gaps**: Material, lighting, animation, VFX transfers not yet executed
- **Cross-discipline synthesis**: Not yet executed
- **Single model reviewer**: Only `11` tested for image critique
- **No position-bias control**: A/B swaps not performed this wave
- **No repeatability test**: Each task run only once

## 10. PRIMARY-EVIDENCE LAW (ESTABLISHED)

The Foundry now enforces:
1. **Material craft requires actual shader renders** — AI image generation ≠ lookdev
2. **Lighting craft requires actual light renders** — lighting description ≠ lighting construction
3. **Animation craft requires temporal output** — keyframe count ≠ animation skill
4. **VFX craft requires temporal effects** — Niagara mapping ≠ VFX execution
5. **Game feel requires human perception** — harness ≠ game feel evidence
6. **Image review requires actual image bytes** — filename ≠ image evidence
7. **Builder ≠ Reviewer** — self-critique is NOT independent review

## 11. EXPERIENCE RECORDS STORED

```
artifacts/
  composition-lab/experience-record.json
  material-lab/renders/manifest.json
  lighting-lab/renders/
  animation-lab/renders/
  vfx-lab/renders/
  gamefeel-lab/
  APPRENTICESHIP-WAVE-001-TRUTH-CORRECTION.md
  APPRENTICESHIP-WAVE-001-FINAL-REPORT.md (this file)
```

## 12. NEXT PHASE DECISION

Wave 001 is PARTIALLY COMPLETE. Decision required:

**Option A: Close Wave 001**. Accept current evidence. Complete transfers + synthesis in Wave 002.
**Option B: Complete transfers**. Execute missing material/lighting/animation/VFX transfers before closing.
**Option C: Add human calibration**. Have Founder blind-review animation weight and game-feel profiles.

Do NOT start Wave 002 automatically. Await Founder direction.