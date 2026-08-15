---
name: 11vt-language-workflows
description: 11vatedTech C++, Python, and TypeScript engineering workflows. Use for language choice, CMake/build systems, type systems, packaging, concurrency, performance-sensitive code, or cross-language architecture.
metadata:
  owner: 11vatedTech
  type: global-capability
  version: "2026-08-15"
---

# 11vatedTech Language Workflows

Select language from runtime constraints, not familiarity.

## Language choice

- C++: tight latency, native integration, graphics, GPU, engines, inference runtimes, memory/layout control.
- Python: experiments, automation, ML pipelines, data tooling, scripts, fast iteration.
- TypeScript: web frontends, Node services, schema-heavy APIs, product UI, browser/runtime integration.

## C++ standard

Use modern C++ with attention to:

- ownership and lifetime
- RAII
- move semantics
- templates/concepts/constexpr when justified
- concurrency and atomics
- cache behavior and memory layout
- SIMD/GPU interop
- ABI/platform boundaries
- sanitizers/static analysis
- CMake reproducibility
- tests and benchmarks

## Python standard

Use:

- modern typing
- virtual env or project-managed environment
- deterministic dependency files
- async/multiprocessing when justified
- packaging hygiene
- testable modules, not script blobs
- profiling for bottlenecks
- reproducible ML experiments

## TypeScript standard

Use:

- strict typing
- runtime schema validation at trust boundaries
- clear frontend state ownership
- typed API contracts
- accessible UI patterns
- unit/component/e2e tests as appropriate
- no unnecessary `any`
- build tooling aligned with project conventions

## Verification

Run language-native checks where present:

- C++: configure/build/tests/sanitizers/static analysis if configured.
- Python: type check/lint/tests/import smoke.
- TypeScript: typecheck/lint/tests/build/runtime smoke.
