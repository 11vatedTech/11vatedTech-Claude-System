#!/usr/bin/env python3
"""Evidence-driven V1 terminal matrix generator."""
from __future__ import annotations
import json, subprocess, sys, hashlib, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SPEC=ROOT/'scripts/validate/v1_terminal_requirements.json'

def run(cmd, timeout=60):
 try:
  p=subprocess.run(cmd,cwd=ROOT,shell=True,capture_output=True,text=True,timeout=timeout)
  return p.returncode,p.stdout+p.stderr
 except Exception as e: return 99,str(e)

def evaluate():
 criteria=json.loads(SPEC.read_text())['criteria']
 checks={}
 def exists(path): return (ROOT/path).exists()
 rc,doctor=run('python scripts/doctor/foundry_doctor.py')
 rc2,core=run('python scripts/validate/foundry_validate.py')
 checks.update({
  'REPOSITORY_HYGIENE': not bool(run('git status --porcelain=v1')[1].strip()),
  'PRODUCT_CONTAMINATION_REMOVED': 'no product files tracked' in doctor,
  'PUMKIT_EXTRACTION_COMPLETE': 'pumkit=e9c890d1' in doctor,
  'GROWTHOS_RECOVERY_CLASSIFIED_COMPLETE': exists(Path('artifacts')/'evidence'/'milestone-1.1'/'repository-boundary-audit.md') or exists(Path('docs')/'evidence'/'milestone-1.1'/'repository-boundary-audit.md'),
  'PRODUCT_REGISTRY_OPERATIONAL': 'registry=f9de4530' in doctor,
  'PRODUCT_MANIFEST_STANDARD': exists(Path('config')/'product-portfolio-registry.json'),
  'GLOBAL_DEPLOYMENT': 'deployment_parity' in core and rc2==0,
  'KAPIF_STORAGE': 'KAPIF_HEALTH: atoms=' in doctor,
  'KAPIF_SECURITY': exists(Path('scripts')/'kapif'/'security.py'),
  'TOOL_DISCOVERY': 'TOOLCHAIN: execution_proven=' in doctor,
  'BLENDER_PIPELINE': exists(Path('artifacts')/'creative-stack-validation'/'blender-ops'/'current-execution-evidence.json'),
  'UNREAL_PIPELINE': exists(Path('artifacts')/'creative-stack-validation'/'unreal-current-execution.json') and 'returncode' in (ROOT/'artifacts/creative-stack-validation/unreal-current-execution.json').read_text(),
  'MISSION_COMPILER': exists(Path('scripts')/'mission'/'foundry_mission.py'),
  'MISSION_RUNTIME': any((ROOT/'artifacts/missions').glob('*-result.json')) if (ROOT/'artifacts/missions').exists() else False,
  'FRONTEND_UI_UX_PATH': exists(Path('artifacts')/'frontend'/'wave-a-pumkit-before'/'pumkit-before-evidence.json'),
  'CHARACTER_IDENTITY_PATH': exists(Path('artifacts')/'frontend'/'wave-a-pumkit-before'/'pumkit-visual-canon-v2.json'),
  'CANONICAL_TRUTH_GENERATOR': exists(Path('scripts')/'validate'/'canonical_truth_generator.py') and not exists(Path('scripts')/'generate_v1_truth.py'),
  'FOUNDRY_VALIDATE': rc2==0,
  'FOUNDRY_DOCTOR': rc==0,
  'KNOWLEDGE_FRESHNESS': exists(Path('artifacts')/'knowledge-freshness.json'),
  '9ROUTER_HEALTH': '9ROUTER: port 20128 closed' not in doctor and '9ROUTER: ' in doctor,
  'GOLDEN_REAL_WORK_MISSIONS': all(exists(Path('artifacts/missions')/f'golden-{x}.json') for x in 'ABCDEFGH'),
 })
 for c in criteria: checks.setdefault(c,False)
 rows={c:{'status':'PASS' if checks[c] else 'NOT_PROVEN','evaluator':'terminal_matrix.evaluate'} for c in criteria}
 return {'criteria_count':len(criteria),'pass':sum(checks.values()),'not_proven':sum(not x for x in checks.values()),'rows':rows}

def main():
 out=ROOT/'artifacts'/'terminal-v1-acceptance.json'; result=evaluate(); out.write_text(json.dumps(result,indent=2)); print(json.dumps({k:result[k] for k in ('criteria_count','pass','not_proven')})); return 0 if result['not_proven']==0 else 1
if __name__=='__main__': sys.exit(main())
