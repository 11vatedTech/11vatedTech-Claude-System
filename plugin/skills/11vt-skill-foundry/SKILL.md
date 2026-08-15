---
name: 11vt-skill-foundry
description: 11vatedTech skill engineering and capability maintenance workflow. Use when creating, auditing, sourcing, evaluating, consolidating, or updating skills, subagents, capability registries, source ledgers, or memory architecture.
metadata:
  owner: 11vatedTech
  type: global-capability
  version: "2026-08-15"
---

# 11vatedTech Skill Foundry

Create durable capability, not prompt clutter.

## Skill creation threshold

Create a skill only when recurring workflow needs at least one:

- specialized knowledge
- repeatable method
- deterministic automation
- tool integration
- project conventions
- evaluation procedure
- reusable references/templates/scripts

Do not create skill for ordinary memory, README content, one-time scripts, or narrow transient tasks.

## Skill quality standard

Each custom skill needs:

- clear responsibility
- strong trigger description
- minimal `SKILL.md` entrypoint
- references for deep material
- scripts for deterministic repeated operations when useful
- examples only when they improve outcomes
- validation criteria
- failure behavior
- current-source awareness for fast-moving tech

## Sourcing security gate

Before adopting third-party skill/plugin, inspect:

- owner and source
- maintenance activity
- license
- skill contents
- scripts and shell commands
- hooks and MCP config
- network behavior
- filesystem writes
- package install behavior
- permissions and dependencies
- credential access
- telemetry
- destructive operations
- hidden paid dependencies

Never run `curl ... | bash`. Never store secrets in `SKILL.md`.

## Evaluation

For important skills, define:

- should-trigger prompts
- should-not-trigger prompts
- representative tasks
- adversarial tasks
- ambiguous tasks
- assertions for output quality

Measure activation separately from output improvement.

## Maintenance

Maintain:

- capability registry
- source ledger
- update procedure
- evaluation records

Use `references/skill-evaluation-template.md`.
