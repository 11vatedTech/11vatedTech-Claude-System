#!/usr/bin/env python3
from __future__ import annotations
import json, os, platform, shutil, subprocess

def run(cmd):
    try:
        r=subprocess.run(cmd, capture_output=True, text=True, timeout=10, shell=True)
        return (r.stdout or r.stderr).strip().splitlines()[0] if r.returncode==0 and (r.stdout or r.stderr).strip() else None
    except Exception:
        return None

tools={
 'git':'git --version','gh':'gh --version','node':'node --version','npm':'npm --version','pnpm':'pnpm --version','python':'python --version','uv':'uv --version','ruff':'ruff --version','mypy':'mypy --version','pytest':'pytest --version','cmake':'cmake --version','ninja':'ninja --version','gcc':'gcc --version','clang':'clang --version','clangd':'clangd --version','lldb':'lldb --version','playwright':'npx playwright --version'
}
print('os='+platform.platform())
print('arch='+platform.machine())
print('cpu='+platform.processor())
for k,cmd in tools.items():
    v=run(cmd)
    print(f'{k}='+(v if v else 'unavailable'))
print('nvidia_smi='+(run('nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader') or 'unavailable'))
