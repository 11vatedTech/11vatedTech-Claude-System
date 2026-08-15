#!/usr/bin/env python3
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'plugin'/'skills'
DST=Path.home()/'.claude'/'skills'
count=0
for d in SRC.iterdir():
    if d.is_dir() and (d/'SKILL.md').exists():
        target=DST/d.name
        if target.exists(): shutil.rmtree(target)
        shutil.copytree(d,target)
        count+=1
print(f'synced_skills={count}')
