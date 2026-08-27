#!/usr/bin/env python3
"""
Foundry Sync — canonical global deployment flow.
Operations: doctor, validate, sync --dry-run, sync, rollback, status.
"""
from __future__ import annotations
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def run(cmd, label):
    print(f"\n  --- {label} ---")
    r = subprocess.run(cmd, shell=True, cwd=str(ROOT), capture_output=False)
    return r.returncode

def main():
    if len(sys.argv) < 2:
        print("Usage: foundry_sync.py <command>")
        print("Commands: doctor, validate, sync, dry-run, status, rollback")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "doctor":
        sys.exit(run("python scripts/doctor/foundry_doctor.py", "FOUNDRY DOCTOR"))
    elif cmd == "validate":
        sys.exit(run("python scripts/validate/foundry_validate.py", "FOUNDRY VALIDATE"))
    elif cmd == "dry-run":
        sys.exit(run("python scripts/install/sync_to_claude.py --dry-run", "SYNC DRY RUN"))
    elif cmd == "sync":
        sys.exit(run("python scripts/install/sync_to_claude.py", "FOUNDRY SYNC"))
    elif cmd == "status":
        sys.exit(run("python scripts/doctor/foundry_doctor.py", "FOUNDRY STATUS"))
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)

if __name__ == "__main__":
    main()
