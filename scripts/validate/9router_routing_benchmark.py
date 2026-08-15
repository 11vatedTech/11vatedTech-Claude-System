#!/usr/bin/env python3
from __future__ import annotations
import json, time, urllib.request, pathlib, sys
ROOT=pathlib.Path(__file__).resolve().parents[2]
PROFILE=ROOT/'evaluations/model-routing/routing-profile.json'
BASE='http://127.0.0.1:20128'
MODELS=['11','kr/auto-thinking','kr/claude-sonnet-4.5-thinking-agentic']
TASKS=json.loads((ROOT/'evaluations/model-routing/routing-suite.json').read_text(encoding='utf-8'))['tasks'][:2]

def post(model,prompt):
    data=json.dumps({'model':model,'messages':[{'role':'user','content':prompt}], 'max_tokens':80,'stream':False}).encode()
    req=urllib.request.Request(BASE+'/v1/chat/completions',data=data,headers={'Content-Type':'application/json','Authorization':'Bearer sk_9router'})
    t=time.perf_counter()
    with urllib.request.urlopen(req,timeout=30) as r:
        out=json.loads(r.read().decode('utf-8','replace'))
    return int((time.perf_counter()-t)*1000), out.get('choices',[{}])[0].get('message',{}).get('content','')

def main():
    results=[]
    discovery=json.loads(urllib.request.urlopen(BASE+'/v1/models',timeout=10).read().decode())
    avail={m.get('id') for m in discovery.get('data',[]) if isinstance(m,dict)}
    for m in MODELS:
        if m not in avail: continue
        for task in TASKS:
            try:
                ms,content=post(m, task['prompt'])
                results.append({'model':m,'task':task['id'],'ok':True,'latency_ms':ms,'chars':len(content),'sample':content[:120]})
                print(m, task['id'], 'ok', ms)
            except Exception as e:
                results.append({'model':m,'task':task['id'],'ok':False,'error':type(e).__name__+': '+str(e)[:200]})
                print(m, task['id'], 'error', e)
    profile={'suite_version':'0.2.0','date':'2026-08-15','no_paid_spend':True,'results':results,'preferred':{'general':'11','reasoning':'kr/auto-thinking if available and successful, else 11'},'limitations':['Tiny smoke benchmark only; requires real project calibration','No paid-model spend authorized','Correctness manually sampled, not fully graded']}
    PROFILE.write_text(json.dumps(profile,indent=2),encoding='utf-8')
    return 0 if any(r.get('ok') for r in results) else 1
if __name__=='__main__': sys.exit(main())
