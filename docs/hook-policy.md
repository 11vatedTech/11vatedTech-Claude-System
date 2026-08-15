# Hook Policy

Hooks enforce only deterministic high-value safeguards:

- block obvious destructive shell operations (`rm -rf /`, force push, hard reset, clean -fdx, curl pipe shell)
- block common secret/protected file path access (`.env`, keys, secrets/)
- inject tiny session status when plugin loaded

Hooks do not run full tests after edits and do not replace permissions or judgment.
