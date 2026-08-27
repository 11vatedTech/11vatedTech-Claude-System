# PUMKIT Character Reconstruction — Current Research

**Date:** 2026-08-24
**Decision:** capability closure remains incomplete; no generation output is approved.

## Current local capability

The current workstation has:

- NVIDIA GeForce RTX 5070 Ti Laptop GPU, 12,227 MB VRAM
- CUDA 13.3
- Blender 5.2
- Inkscape 1.4.4
- FFmpeg 8.1.2
- Node/Python
- 9Router image endpoint with current edit-capable models

It does **not** have ComfyUI, a local diffusion checkpoint, a proven background-removal model, a local image-editing workflow, or a local multimodal comparison model installed and regression-tested.

## Bounded candidate comparison

| Candidate | Conditioning/editing | Multi-reference / regional control | Windows + 12 GB VRAM | License / commercial status | Decision |
|---|---|---|---|---|---|
| Qwen-Image / Qwen-Image-Edit | Strong instruction-based editing; current official ComfyUI workflow | Good editing base; regional/pose control depends on additional workflow components | Full 20B is not a comfortable 12 GB target; quantized community builds require separate provenance review | Official Qwen repository/model search identifies Apache 2.0 for Qwen-Image; verify exact checkpoint and dependencies before commercial use | Best open/local-first candidate after a verified quantized install and benchmark |
| FLUX.1 Kontext [dev] | Strong multimodal image editing and text-guided changes | Reference image editing is strong; advanced multi-reference graph needs adapters/nodes | 12B; FP8 reports commonly exceed this GPU’s comfortable budget without offload/quantization | FLUX.1 [dev] Non-Commercial License; not acceptable as default commercial pipeline without explicit terms | Research-only/fallback, not selected for production asset |
| FLUX IP-Adapter variants | Image conditioning adapter for FLUX | Useful reference/style conditioning | Requires compatible FLUX base plus adapter and node stack | Adapter/base licenses vary; FLUX dev restrictions apply | Do not install until exact repository/checkpoint/node licenses are reviewed |
| GPT image via 9Router (`cx/gpt-5.5-image`, `cx/gpt-5.4-image`, `cx/gpt-5.3-image`) | Endpoint reports `edit` capability and accepts image inputs | Strongest immediately executable edit route exposed in current session; auditability depends on request/input/output capture | No local VRAM requirement; requires configured 9Router provider/account | Hosted/provider terms apply; not local/open and commercial rights require provider/account review | Viable bounded experiment only, not assumed approved or free |
| Gemini 3.1 Flash image via 9Router | Text-to-image only in current endpoint metadata | No edit capability reported | Hosted | Provider terms apply | Not selected |
| SAM 2 | Promptable segmentation/matting preparation | Excellent object-mask preparation; not a reconstruction model | Local viability depends on runtime/checkpoint; 12 GB is plausible with optimized inference | Official repository reports Apache 2.0 | Selected for preparation only if installed and benchmarked; never final art |
| Florence-2 | Captioning, grounding, segmentation, OCR | Useful analysis/region discovery | Lightweight Windows/local candidate | Official model card/license must be preserved and verified; commonly MIT distribution | Optional analysis helper, not reconstruction model |
| RMBG-2.0 | Background removal | Matting only | Local candidate but not installed | CC BY-NC 4.0; commercial use requires BRIA agreement | Rejected for commercial-default pipeline |

Research sources included official/primary pages where available: QwenLM Qwen-Image GitHub/model card, ComfyUI official Qwen tutorial, Black Forest Labs FLUX Kontext model card/license, Meta SAM2 repository/license, Microsoft Florence-2 model card, BRIA RMBG model card, and current 9Router model metadata.

## Selected workflow

The selected workflow is **2D-first, reference-conditioned, iterative, and approval-gated**:

1. Preserve original sheets read-only and hash them.
2. Normalize copies for color/orientation without replacing originals.
3. Build the structured reference package and morphology/marking map.
4. Use promptable segmentation only to prepare masks/reference crops.
5. Install ComfyUI only if the chosen checkpoint and nodes pass explicit review.
6. Prefer Qwen-Image-Edit after a quantized Windows/12 GB feasibility benchmark; use 9Router edit only as an explicitly hosted experiment.
7. Condition with neutral full-body and face/ear/marking references; preserve anatomical context.
8. Generate a canon-neutral hero first, with no dramatic environment.
9. Repair only failing regions: face/eyes, ears, markings, paws/limbs, tail, fur/color.
10. Compare actual renders against the supplied canon using visual evidence and independent review.
11. Generate editorial and behavioral variants only after neutral hero approval.

## ComfyUI policy

ComfyUI is an execution substrate, not a capability claim. Required policy is `DENY_ALL → explicit node review → minimal allowlist`. No community node was installed in this pass because the required local model/editing stack is not present and unreviewed installation would violate provenance and reproducibility requirements.

## Current installation/integration evidence

- `config/creative-toolchain.json` reports ComfyUI/image editing/background removal as unavailable or uninstalled.
- 9Router health is PASS; `/v1/models/image` reports four models, of which three expose edit capability.
- No local reference-conditioned render has been produced.
- No segmentation output has been promoted to final art.
- No model checkpoint, node graph, seed, input hash, or output hash exists for an approved reconstruction.

## Capability gap

The missing capability is not merely “an image generator.” It is an auditable, local/free-first **reference-conditioned identity-preserving 2D reconstruction pipeline** with segmentation preparation, multi-reference conditioning, regional repair, provenance, and independent visual comparison. Until that pipeline produces a canon-neutral hero that passes the stated gate, `CHARACTER_ASSET_APPROVED` remains false.
