#!/usr/bin/env python3
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[2]

def sync_tree(src: Path, dst: Path, required_file: str) -> int:
    count=0
    dst.mkdir(parents=True, exist_ok=True)
    for d in src.iterdir():
        if d.is_dir() and (d/required_file).exists():
            target=dst/d.name
            shutil.copytree(d,target,dirs_exist_ok=True)
            count+=1
        elif d.is_file() and required_file == '*.md' and d.suffix == '.md':
            shutil.copy2(d, dst/d.name)
            count+=1
    return count

skills=sync_tree(ROOT/'plugin'/'skills', Path.home()/'.claude'/'skills', 'SKILL.md')
agents=sync_tree(ROOT/'plugin'/'agents', Path.home()/'.claude'/'agents', '*.md')
print(f'synced_skills={skills}')
print(f'synced_agents={agents}')
