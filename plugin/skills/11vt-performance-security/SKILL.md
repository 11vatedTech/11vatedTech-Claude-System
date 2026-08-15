---
name: 11vt-performance-security
description: Performance and security engineering workflow for 11vatedTech. Use for profiling, benchmarking, optimization, threat modeling, dependency risk, secrets, subprocess/file/network boundaries, native/model/plugin security, or release hardening.
metadata:
  owner: 11vatedTech
  type: global-capability
  version: "2026-08-15"
---

# 11vatedTech Performance and Security Engineering

Do not optimize or secure by slogan.

## Performance workflow

1. establish workload
2. establish baseline
3. profile
4. identify bottleneck
5. form hypothesis
6. implement focused change
7. benchmark
8. compare
9. inspect regressions
10. document result

Cover CPU, memory, allocations, cache, I/O, network, GPU, VRAM, kernel utilization, latency, throughput, startup, bundle size, frame time, and frame pacing.

## Security workflow

1. define assets and trust boundaries
2. identify actors and entry points
3. inspect secrets/auth/authz
4. inspect input validation and serialization
5. inspect filesystem/path boundaries
6. inspect subprocess/command execution
7. inspect network boundaries
8. inspect dependency/supply-chain risk
9. inspect unsafe native/model/plugin execution
10. define mitigations and tests

Security is not `sanitize inputs`. Treat model files, plugins, scripts, and MCP servers as executable supply-chain surfaces.

## Rules

- Never print secrets.
- Do not run destructive/security tooling outside authorized scope.
- Verify dependency/license/security claims from sources.
- Benchmark before claiming performance improvement.

Use `references/threat-model-template.md` and `references/benchmark-template.md`.
