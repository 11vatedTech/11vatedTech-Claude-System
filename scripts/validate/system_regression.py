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

def check_blender_ops():
    """Structured Blender ops are a first-class gate when Blender is present;
    a clear SKIP report (not a silent pass) when it is missing."""
    sys.path.insert(0, str(ROOT/'scripts/media'))
    from vtmedia.blender_bridge import available
    if not available():
        print('blender_ops SKIP blender_not_detected')
        return True
    out_dir=ROOT/'artifacts/creative-stack-validation/blender-ops'
    try:
        code,out,err=run(f'cd "{ROOT / "scripts/media"}" && python -m vtmedia.blender_ops --suite --out "{out_dir}"', timeout=420)
        ok=code==0
        print('blender_ops', 'ok' if ok else (err or out)[-500:])
    except Exception as e:
        ok=False
        print('blender_ops', 'FAILED', type(e).__name__, str(e)[:200])
    return ok

def check_assets():
    """Asset pipeline gate: requirement discovery -> resolver -> vault smoke
    (hermetic temp vault). Quality models must parse and have dimensions."""
    ok=True
    code,out,err=run(f'python "{ROOT / "scripts/assets/requirement_discovery.py"}" creature_entity "Regression Probe"')
    import json
    try:
        d=json.loads(out)
        ok &= bool(d.get('ok') and d.get('node_count',0)>=10)
        print('asset_discovery', 'ok' if ok else (out or err)[-200:])
    except Exception as e:
        ok=False; print('asset_discovery', 'FAILED', e)
    # resolver: fixture with one originality-critical and one utility requirement
    import tempfile
    fixture={"name":"hero_model","category":"3d-model","quality_target":"PRODUCTION","flags":{"needs_originality":True,"can_create":True,"license_known":False}}
    with tempfile.TemporaryDirectory() as td:
        reqf=Path(td)/'reqs.json'; reqf.write_text(json.dumps([fixture]),encoding='utf-8')
        code,out,err=run(f'python "{ROOT / "scripts/assets/asset_resolver.py"}" "{reqf}"')
        try:
            d=json.loads(out)
            ok &= d.get('decision',{}).get('mode') is not None
            print('asset_resolver', 'ok' if d.get('decision',{}).get('mode') else out[:200])
        except Exception as e:
            ok=False; print('asset_resolver', 'FAILED', e)
        # vault smoke (hermetic index)
        idx=Path(td)/'vault.json'
        src=ROOT/'artifacts/creative-stack-validation/image/generated.png'
        code,out,err=run(f'python "{ROOT / "scripts/assets/asset_vault.py"}" --index "{idx}" add "{src}" --kind raster --license generated-local --source procedural --creator regression')
        try:
            d=json.loads(out); ok &= bool(d.get('ok')); vid=d.get('id','')
            code,out,err=run(f'python "{ROOT / "scripts/assets/asset_vault.py"}" --index "{idx}" add "{src}" --kind raster --license generated-local --source procedural --project p2')
            d2=json.loads(out); ok &= bool(d2.get('duplicate'))
            code,out,err=run(f'python "{ROOT / "scripts/assets/asset_vault.py"}" --index "{idx}" lineage "{vid}"')
            ok &= bool(json.loads(out).get('asset'))
            print('asset_vault_smoke', 'ok' if ok else (out or err)[-200:])
        except Exception as e:
            ok=False; print('asset_vault_smoke', 'FAILED', e)
    # quality models parse + dimensions
    try:
        qm=json.loads((ROOT/'config/quality-models.json').read_text(encoding='utf-8'))
        models=qm.get('models',{}); ok &= len(models)>=6
        ok &= all(m.get('dimensions') for m in models.values())
        print('quality_models', f'ok ({len(models)} models)' if ok else 'FAILED')
    except Exception as e:
        ok=False; print('quality_models', 'FAILED', e)
    return ok

def check_failure_tests():
    code,out,err=run(f'python "{ROOT / "scripts/validate/failure_tests.py"}"')
    ok=code==0
    print('failure_tests', 'ok' if ok else (err or out)[-400:])
    return ok

def check_l5_evidence():
    code,out,err=run(f'python "{ROOT / "scripts/validate/l5_evidence.py"}"')
    ok=code==0
    tail=(out or err).strip().splitlines()[:2]
    print('l5_evidence', 'ok' if ok else tail)
    if ok: print('  ' + ' | '.join(tail[:2]))
    return ok

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
    checks=[check_plugin,check_skills,check_agents,check_manifest_template,check_hooks,check_bootstrap,check_media,check_blender_ops,check_assets,check_failure_tests,check_l5_evidence,check_routing,check_ontology,check_9router]
    results=[c() for c in checks]
    print('system_regression_ok', all(results))
    return 0 if all(results) else 1
if __name__=='__main__': sys.exit(main())
