---
name: 11vt-ai-ml-local-inference
description: AI/ML and local inference workflow for 11vatedTech. Use for model selection, embeddings, vision/speech, ONNX, quantization, GPU/VRAM planning, local-first AI, benchmark design, or hosted-vs-local architecture decisions.
metadata:
  owner: 11vatedTech
  type: global-capability
  version: "2026-08-15"
---

# 11vatedTech AI / ML / Local Inference

Default to local/open feasibility analysis before making hosted inference mandatory.

## Workflow

1. define actual workload and latency/quality targets
2. identify modality: text, vision, speech, embeddings, multimodal, generation
3. research candidate models and licenses
4. estimate memory/VRAM, batch size, throughput, and context needs
5. choose runtime: ONNX Runtime, CUDA, TensorRT, DirectML, llama.cpp, vLLM, PyTorch, or project-native engine
6. benchmark against representative input
7. document fallback path and failure behavior
8. verify reproducibility

## Evaluate

- license and redistribution rights
- model size and quantization support
- VRAM/RAM footprint
- CPU fallback viability
- throughput and tail latency
- numerical correctness
- platform support
- model update risk
- privacy boundary
- dataset/task fit
- failure modes

## Rules

- Never claim model works because README says it works.
- Prefer replaceable inference interfaces.
- Keep hosted APIs optional when viable.
- Do not store model/provider secrets in skills or repos.
- Treat model files as untrusted inputs; verify source and hash when practical.

Use `references/local-inference-checklist.md` for evaluation.
