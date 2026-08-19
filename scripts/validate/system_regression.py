#!/usr/bin/env python3
from __future__ import annotations
import json, os, re, shutil, subprocess, sys, tempfile, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def run(cmd, cwd=None, timeout=60):
    r=subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout.strip(), r.stderr.strip()

def check_plugin():
    code,out,err=run(f'claude plugin validate "{ROOT / "plugin"}"')
    print('plugin_validate', code, out or err)
    return code==0

def check_skills():
    bad=[]
    for p in (ROOT/'plugin/skills').glob('*/SKILL.md'):
        t=p.read_text(encoding='utf-8')
        if not t.startswith('---\n'): bad.append(str(p))
        if 'description:' not in t: bad.append(str(p)+':no-description')
    print('plugin_skills', 'ok' if not bad else bad)
    return not bad

def check_agents():
    bad=[]
    for p in (ROOT/'plugin/agents').glob('*.md'):
        t=p.read_text(encoding='utf-8')
        if not t.startswith('---\n'): bad.append(str(p))
        if 'description:' not in t: bad.append(str(p)+':no-description')
        if 'tools:' not in t: bad.append(str(p)+':no-tools')
    print('plugin_agents', 'ok' if not bad else bad)
    return not bad

def check_manifest_template():
    code,out,err=run(f'python "{ROOT / "scripts/validate/manifest_validator.py"}" "{ROOT / "templates/product-repository/11vt.project.yaml"}"')
    # template intentionally has TODO name; validator should fail for real product but schema keys should exist
    ok='product.name still TODO' in (out+err)
    print('manifest_template_guard', ok)
    return ok

def check_hooks():
    guards=ROOT/'scripts/hooks/guards.py'
    p=subprocess.run(['python',str(guards),'pretool-bash'], input=json.dumps({'tool_input':{'command':'rm -rf /'}}), capture_output=True, text=True)
    ok='permissionDecision' in p.stdout and 'deny' in p.stdout
    print('hook_destructive_guard', ok)
    p=subprocess.run(['python',str(guards),'pretool-file'], input=json.dumps({'tool_input':{'file_path':'.env'}}), capture_output=True, text=True)
    ok2='permissionDecision' in p.stdout and 'deny' in p.stdout
    print('hook_secret_guard', ok2)
    return ok and ok2

def check_bootstrap():
    with tempfile.TemporaryDirectory() as td:
        repo=Path(td)/'blank'; repo.mkdir(); run('git init', cwd=repo)
        code,out,err=run(f'python "{ROOT / "scripts/bootstrap/bootstrap_project.py"}" "{repo}"')
        required=['11vt.project.yaml','CLAUDE.md','CURRENT_STATE.md','.claude/skills/project-verify/SKILL.md','tools/11vt/verify.py']
        ok=code==0 and all((repo/r).exists() for r in required)
        code2,out2,err2=run(f'python "{ROOT / "scripts/bootstrap/bootstrap_project.py"}" "{repo}"')
        idem='preserve existing' in out2
        print('bootstrap_blank', ok, 'idempotent', idem)
        # existing CLAUDE preservation
        repo2=Path(td)/'existing'; repo2.mkdir(); (repo2/'CLAUDE.md').write_text('existing guidance',encoding='utf-8'); run('git init', cwd=repo2)
        run(f'python "{ROOT / "scripts/bootstrap/bootstrap_project.py"}" "{repo2}"')
        preserved=(repo2/'CLAUDE.md').read_text(encoding='utf-8')=='existing guidance'
        print('bootstrap_preserve_claude', preserved)
        return ok and idem and preserved

def check_9router():
    try:
        data=json.loads(urllib.request.urlopen('http://127.0.0.1:20128/api/health',timeout=5).read().decode())
        print('9router_health', data)
        return data.get('ok') is True
    except Exception as e:
        print('9router_health_error', e); return False

def check_routing():
    code,out,err=run(f'python "{ROOT / "scripts/validate/routing_eval.py"}"')
    ok=code==0
    print('routing_eval', 'ok' if ok else (err or out)[-400:])
    return ok

def check_ontology():
    code,out,err=run(f'python "{ROOT / "scripts/validate/ontology_check.py"}"')
    ok=code==0
    tail=(out or err).strip().splitlines()[-4:]
    print('ontology_check', 'ok' if ok else tail)
    if ok: print('  ' + ' | '.join(tail[:3]))
    return ok

def check_media():
    """Media toolchain is a first-class regression gate: image/vector/video/audio."""
    cli=str(ROOT/'scripts/media/11vt_media.py')
    failures=[]
    for sub in ['image-test','vector-test','video-test','audio-test']:
        code,out,err=run(f'python "{cli}" {sub}', timeout=300)
        ok=code==0
        if not ok:
            failures.append(sub)
            print(f'media_{sub}', 'FAIL', (err or out)[-500:])
        else:
            print(f'media_{sub}', 'ok')
    print('media_gate', 'ok' if not failures else failures)
    return not failures

def main():
    checks=[check_plugin,check_skills,check_agents,check_manifest_template,check_hooks,check_bootstrap,check_media,check_routing,check_ontology,check_9router]
    results=[c() for c in checks]
    print('system_regression_ok', all(results))
    return 0 if all(results) else 1
if __name__=='__main__': sys.exit(main())
