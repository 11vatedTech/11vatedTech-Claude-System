# Apprenticeship Wave 001 — Truth Correction

## Date: 2026-08-23

## 1. PREVIOUS CLAIMS DOWNGRADED

### Wave 001 "COMPLETE" → INCOMPLETE (PRIMARY EVIDENCE MISSING)

The previous report claimed Wave 001 complete. In reality, only one discipline
(COMPOSITION) had genuine practice evidence. The others had knowledge packs
and diagnostic frameworks but no actual craft output.

| Discipline | Previous Claim | Truth | Evidence Gap |
|---|---|---|---|
| COMPOSITION | COMPLETE | COMPLETE (verified) | None — 5 alt layouts, blind review, repair, transfer |
| MATERIAL | "KNOWLEDGE + DIAGNOSTIC" | KNOWLEDGE ONLY | Image-gen is not shader authoring |
| LIGHTING | "KNOWLEDGE + DIAGNOSTIC" | KNOWLEDGE ONLY | No rendered lighting comparisons |
| ANIMATION | "KNOWLEDGE + MOTION PROFILES" | KNOWLEDGE ONLY | No temporal video evidence |
| VFX | "KNOWLEDGE + NIAGARA MAPPING" | KNOWLEDGE ONLY | No temporal effect execution |
| GAME FEEL | "INTERACTION HARNESS" | HARNESS EXISTS, UNTESTED | No human interaction evidence |

### Multimodal Benchmark Record

The v1 benchmark was corrected in a previous pass. No further changes needed.

### Builder Self-Critique

The builder_critique.md remains valuable as BUILDER_SELF_CRITIQUE only.
The "independent_critique.md" was from the same context — reclassified as
SELF_REVIEW, not INDEPENDENT_REVIEW.

## 2. TOOL DISCOVERY REGRESSION

### Finding

The previous report stated: "NO BLENDER AVAILABLE"

Reality: Blender 5.2.0 LTS is installed at:
`C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`

The resolver used PATH-only discovery. `blender.exe` is not on PATH because
Blender's Windows installer does not add it by default.

### Root Cause

The canonical tool resolver exists in the Foundry registry (capability-registry.json,
capability-truth-audit.json) with the exact path. The previous agent did not
consult it, falling back to `which blender` / PATH search.

### Classification

Failure class: **KNOWN_INSTALLED_TOOL_NOT_ON_PATH** (as specified in §30 of the brief)

Added to regression: TOOL_DISCOVERY_REGRESSION

### Repair

Future tool discovery must:
1. Check Foundry capability registry first
2. Check known Windows install paths
3. Fall back to PATH

## 3. FAILURE INTELLIGENCE ADDED

### MEDIUM_SUBSTITUTION

**Definition:** A result produced in a different medium is treated as if it
proved competence in the target craft.

**Examples:**
- AI-generated ceramic image != material lookdev skill
- AI-generated lighting image != lighting construction skill
- Still frame != animation skill
- Description of VFX != VFX execution skill

**Required response:** BLOCK CLAIM or explicitly downgrade to KNOWLEDGE/DESIGN
level. Do not credit as craft practice.

### TOOL_DISCOVERY_REGRESSION

**Definition:** A known installed tool is reported as unavailable because the
discovery mechanism regressed to PATH-only search, ignoring the canonical
Foundry tool registry.

**Required response:** Repair resolver, record regression, verify tool.

## 4. CORRECTED MATURITY LEDGER (PRE-PRIMARY-EVIDENCE)

| Discipline | Knowledge | Practice | Critique | Repair | Transfer | Primary Evidence |
|---|---|---|---|---|---|---|
| COMPOSITION | K4 | P3 | Yes | Yes | Yes | Image ✓ |
| MATERIAL | K3 | P1 (image-gen only) | No | No | No | None |
| LIGHTING | K3 | P1 (image-gen only) | No | No | No | None |
| ANIMATION | K2 | P0 | No | No | No | None |
| VFX | K2 | P0 | No | No | No | None |
| GAME FEEL | K2 | P1 (harness, untested) | No | No | No | Human TBD |

## 5. VERIFIED TOOL STATE

- **Blender 5.2.0 LTS**: Available at canonical path, working
- **Unreal 5.8**: Registry-referenced, not verified this session
- **FFmpeg**: Not yet verified
- **9Router**: Available at http://127.0.0.1:20128