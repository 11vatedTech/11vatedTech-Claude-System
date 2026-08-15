# 11vatedTech Capability Update and Maintenance Procedure

Cadence: monthly, plus whenever Claude Code, 9Router, or core project needs change.

## 1. Inventory

- List user/global skills.
- List project skills for active repos.
- List plugins, commands, agents, hooks, MCP configs.
- Check settings scopes without exposing secrets.

## 2. Upstream checks

- Claude Code skill documentation and settings documentation.
- Anthropic bundled skills and first-party plugin marketplace.
- 9Router endpoints and skill repository.
- External skills/plugins already adopted.
- Important dependency/security advisories.

## 3. Security review before update

For each candidate update, inspect:

- scripts
- shell commands
- hooks
- MCP servers
- dependencies
- network behavior
- filesystem writes
- permissions
- credential access
- telemetry
- destructive operations
- hidden paid services

No blind auto-update. No `curl ... | bash`.

## 4. Apply

- Preserve existing custom changes.
- Prefer small diffs.
- Update source ledger with source, revision, license, files, modifications, security review, reason.
- Update capability registry with validation date and notes.

## 5. Evaluate

- Run static structure validation for skills.
- Run trigger tests for descriptions.
- Run representative behavioral prompts where practical.
- Runtime-check 9Router health and model categories.
- Record failures and corrections.

## 6. Memory/canon hygiene

- Store durable company lessons globally.
- Store project facts in repo canon.
- Do not store transient state as permanent memory.
- Keep memory index compact.
