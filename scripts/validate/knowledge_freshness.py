#!/usr/bin/env python3
"""Deterministic freshness evaluator for version-sensitive Foundry knowledge."""
from __future__ import annotations
import json, datetime, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def evaluate(root: Path=ROOT) -> dict:
    now=datetime.datetime.now(datetime.timezone.utc)
    checked=0; stale=[]; malformed=[]
    for path in list((root/'config/resource-packs').glob('*.json')) + list((root/'data/kapif').rglob('*.json')):
        try: data=json.loads(path.read_text())
        except Exception: continue
        items=data if isinstance(data,list) else data.get('atoms', data.get('claims', []))
        if not isinstance(items,list): continue
        for item in items:
            if not isinstance(item,dict): continue
            checked+=1
            if not any(k in item for k in ('retrieved_at','retrieved','last_verified','version','version_date')):
                malformed.append(str(path)); continue
            date=item.get('last_verified') or item.get('retrieved_at') or item.get('retrieved')
            if isinstance(date,str):
                try:
                    parsed=datetime.datetime.fromisoformat(date.replace('Z','+00:00'))
                    if parsed.tzinfo is None: parsed=parsed.replace(tzinfo=datetime.timezone.utc)
                    if (now-parsed).days > 365: stale.append({'path':str(path),'date':date})
                except ValueError: pass
    return {'checked':checked,'stale':stale,'malformed_metadata':sorted(set(malformed)),'status':'PASS' if not stale and not malformed else 'WARN'}

if __name__=='__main__':
 print(json.dumps(evaluate(),indent=2)); sys.exit(0)
