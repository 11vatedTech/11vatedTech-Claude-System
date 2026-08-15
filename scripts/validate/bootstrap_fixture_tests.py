#!/usr/bin/env python3
from __future__ import annotations
import subprocess, tempfile, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BOOT=ROOT/'scripts/bootstrap/bootstrap_project.py'
MANIFEST=ROOT/'scripts/validate/manifest_validator.py'

def run(cmd,cwd=None):
    return subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True, timeout=60)

def main():
    results=[]
    with tempfile.TemporaryDirectory() as td:
        base=Path(td)
        # blank repo
        repo=base/'blank'; repo.mkdir(); run('git init',repo)
        r=run(f'python "{BOOT}" "{repo}"')
        results.append(('blank_bootstrap', r.returncode==0 and (repo/'11vt.project.yaml').exists()))
        # existing code repo
        ex=base/'existing-code'; ex.mkdir(); (ex/'main.py').write_text('print("hi")\n'); run('git init',ex); run('git add main.py && git commit -m init',ex)
        r=run(f'python "{BOOT}" "{ex}"')
        results.append(('existing_code_preserved', (ex/'main.py').read_text()=='print("hi")\n'))
        # existing CLAUDE.md and .claude preservation
        pr=base/'preserve'; pr.mkdir(); (pr/'CLAUDE.md').write_text('existing'); (pr/'.claude').mkdir(); (pr/'.claude/settings.local.json').write_text('{}')
        run('git init',pr); r=run(f'python "{BOOT}" "{pr}"')
        results.append(('existing_claude_preserved', (pr/'CLAUDE.md').read_text()=='existing' and (pr/'.claude/settings.local.json').exists()))
        # idempotence
        r2=run(f'python "{BOOT}" "{pr}"')
        results.append(('idempotence', 'preserve existing' in r2.stdout))
        # malformed manifest
        bad=base/'bad'; bad.mkdir(); (bad/'11vt.project.yaml').write_text('schema_version: 2\n')
        v=run(f'python "{MANIFEST}" "{bad/"11vt.project.yaml"}"')
        results.append(('malformed_manifest_rejected', v.returncode!=0))
        # dirty tree detected
        dirty=base/'dirty'; dirty.mkdir(); run('git init',dirty); (dirty/'x.txt').write_text('x')
        r=run(f'python "{BOOT}" "{dirty}"')
        results.append(('dirty_tree_reported', 'dirty_git_tree_detected' in r.stdout))
        # secret file preserved and hook test covers guard
        sec=base/'secret'; sec.mkdir(); (sec/'.env').write_text('SECRET=x')
        r=run(f'python "{BOOT}" "{sec}"')
        results.append(('secret_file_preserved', (sec/'.env').read_text()=='SECRET=x'))
    for name, ok in results: print(name, ok)
    overall=all(ok for _,ok in results)
    print('bootstrap_fixture_tests_ok', overall)
    return 0 if overall else 1
if __name__=='__main__': sys.exit(main())
