# Rollback Procedure

## Claude Code upgrade rollback

Pre-upgrade backup: `C:/Users/11vat/OneDrive/Desktop/claude-backups/phase-ii-pre-upgrade-2026-08-15/`.

If regression appears:

1. Record failing command/output.
2. Restore backed up `settings.json`, skills, commands only if local files were changed.
3. Reinstall previous Claude Code version through supported installer/package if available.
4. Rerun capability validation and 9Router smoke tests.

## Capability rollback

Use Git history in this repository. Revert commits rather than hand-deleting capability files.
