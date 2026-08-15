# Free / Open Development Principle

11vatedTech products should not require customers or 11vatedTech to maintain paid API access for core product behavior when a viable local/open alternative exists.

## Prefer

- open source
- permissive licensing where appropriate
- self-hostability
- local execution
- open standards
- replaceable components
- free development tooling
- transparent data formats

## Paid services

Paid service may be acceptable when:

- user explicitly authorizes dependency
- service is optional integration
- open alternative is infeasible for current scope
- cost, privacy, lock-in, failure mode, and exit path are documented

## AI dependencies

For AI features, investigate local or open options first:

- local LLMs
- local embeddings
- ONNX Runtime
- DirectML/CUDA/TensorRT when useful
- quantized models
- self-hosted inference
- offline fallback path

Never claim local viability until model has been benchmarked against actual workload when feasible.
