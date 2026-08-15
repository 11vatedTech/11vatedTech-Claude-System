#!/usr/bin/env python3
from __future__ import annotations
import json, os, platform, subprocess, sys
from pathlib import Path
from datetime import datetime, timezone

def git_sha():
    try: return subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True,timeout=5).stdout.strip()
    except Exception: return None

def write(kind, command, result, notes=''):
    d=Path('docs/evidence'); d.mkdir(parents=True, exist_ok=True)
    rec={'date':datetime.now(timezone.utc).isoformat(),'kind':kind,'commit':git_sha(),'platform':platform.platform(),'command':command,'result':result,'notes':notes}
    path=d/(rec['date'].replace(':','-')+'-'+kind+'.json')
    path.write_text(json.dumps(rec,indent=2),encoding='utf-8')
    print(path)
if __name__=='__main__': write(sys.argv[1] if len(sys.argv)>1 else 'manual', ' '.join(sys.argv[2:]), 'recorded')
