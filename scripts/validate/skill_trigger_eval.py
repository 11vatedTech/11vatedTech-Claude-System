#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
cases=json.loads((ROOT/'evaluations/trigger/core-skill-trigger-cases.json').read_text(encoding='utf-8'))['cases']
skills={p.parent.name:(p.read_text(encoding='utf-8')) for p in (ROOT/'plugin/skills').glob('*/SKILL.md')}
fail=[]
for c in cases:
    prompt=c['prompt'].lower()
    for e in c.get('expect',[]):
        if e not in skills and e!='11vt-independent-reviewer': fail.append((c['prompt'],e,'missing'))
    for e in c.get('expect_not',[]):
        if e not in skills: continue
print('trigger_cases=',len(cases),'failures=',len(fail))
for f in fail: print('FAIL',f)
raise SystemExit(1 if fail else 0)
