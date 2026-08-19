#!/usr/bin/env python3
from __future__ import annotations
import argparse, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT/'templates'/'product-repository'

MERGE_FILES=['11vt.project.yaml','CLAUDE.md','PRODUCT.md','CURRENT_STATE.md','ENGINEERING_CONSTITUTION.md','ARCHITECTURE.md','ROADMAP.md','VALIDATION_SPECIFICATION.md','TESTING_STRATEGY.md','SECURITY_MODEL.md','RELEASE.md','DESIGN_SYSTEM.md','ASSET_PIPELINE.md']

def git_dirty(repo: Path) -> str:
    try:
        r=subprocess.run(['git','status','--short'], cwd=repo, capture_output=True, text=True, timeout=10)
        return r.stdout.strip()
    except Exception:
        return ''

def copy_missing(src: Path, dst: Path, dry: bool, actions: list[str]):
    if dst.exists():
        actions.append(f'preserve existing {dst.relative_to(dst.parents[0]) if dst.parent else dst}')
        return
    actions.append(f'create {dst}')
    if not dry:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src,dst)

def bootstrap(repo: Path, dry=False) -> int:
    repo=repo.resolve(); actions=[]
    if not repo.exists(): repo.mkdir(parents=True)
    dirty=git_dirty(repo)
    if dirty: actions.append('dirty_git_tree_detected')
    for name in MERGE_FILES:
        copy_missing(TEMPLATE/name, repo/name, dry, actions)
    for sub in ['docs/adr','docs/research','docs/audits','docs/benchmarks','docs/validation','docs/evidence','docs/design','.claude/rules','tools/11vt']:
        p=repo/sub; actions.append(f'ensure_dir {p}');
        if not dry: p.mkdir(parents=True, exist_ok=True)
    for skill in ['project-build','project-run','project-verify','project-release']:
        src=TEMPLATE/'.claude/skills'/skill/'SKILL.md'; dst=repo/'.claude/skills'/skill/'SKILL.md'
        copy_missing(src,dst,dry,actions)
    # copy tooling
    for script in ['verify.py','release_gate.py','evidence.py']:
        src=TEMPLATE/'tools/11vt'/script; dst=repo/'tools/11vt'/script
        if src.exists(): copy_missing(src,dst,dry,actions)
    print('\n'.join(actions))
    return 0

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('repo'); ap.add_argument('--dry-run', action='store_true')
    ns=ap.parse_args(); sys.exit(bootstrap(Path(ns.repo), ns.dry_run))
