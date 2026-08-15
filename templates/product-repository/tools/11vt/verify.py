#!/usr/bin/env python3
from __future__ import annotations
import subprocess, sys

def run(cmd):
    print('RUN', cmd)
    return subprocess.run(cmd, shell=True).returncode
if __name__=='__main__':
    mode=sys.argv[1] if len(sys.argv)>1 else 'changed'
    print(f'11vt verify {mode}: configure project-specific gates in 11vt.project.yaml')
    sys.exit(0)
