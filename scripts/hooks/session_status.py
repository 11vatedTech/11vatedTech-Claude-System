#!/usr/bin/env python3
from pathlib import Path
import subprocess, os
cwd=Path(os.environ.get('CLAUDE_PROJECT_DIR') or os.getcwd())
print('11vatedTech session status:')
print(f'- cwd: {cwd}')
print(f'- manifest: {"present" if (cwd/"11vt.project.yaml").exists() else "absent"}')
print(f'- current_state: {"present" if (cwd/"CURRENT_STATE.md").exists() else "absent"}')
try:
    branch=subprocess.run(['git','branch','--show-current'],cwd=cwd,capture_output=True,text=True,timeout=3).stdout.strip()
    dirty=subprocess.run(['git','status','--short'],cwd=cwd,capture_output=True,text=True,timeout=3).stdout.strip()
    print(f'- git_branch: {branch or "unknown"}')
    print(f'- git_dirty: {"yes" if dirty else "no"}')
except Exception:
    print('- git: unavailable')
