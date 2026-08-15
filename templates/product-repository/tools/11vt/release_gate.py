#!/usr/bin/env python3
from __future__ import annotations
import subprocess, sys

def dirty():
    try: return subprocess.run(['git','status','--short'],capture_output=True,text=True,timeout=5).stdout.strip()
    except Exception: return ''
if __name__=='__main__':
    d=dirty()
    if d:
        print('release_gate_blocked dirty git tree')
        print(d)
        sys.exit(1)
    print('release_gate_template_passed configure project-specific release checks')
