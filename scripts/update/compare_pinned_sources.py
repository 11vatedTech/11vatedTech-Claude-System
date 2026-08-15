#!/usr/bin/env python3
from __future__ import annotations
import hashlib, sys, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SHA='699edac3273e13d4744bc46f6082618f08560702'
SKILLS=['9router','9router-chat','9router-image','9router-tts','9router-embeddings','9router-web-search','9router-web-fetch','9router-stt','9router-video']
BASE=f'https://raw.githubusercontent.com/decolua/9router/{SHA}/skills'

def main():
    ok=True
    for s in SKILLS:
        local=ROOT/'plugin/skills'/s/'SKILL.md'
        url=f'{BASE}/{s}/SKILL.md'
        try:
            remote=urllib.request.urlopen(url,timeout=20).read()
        except Exception as e:
            print(f'{s} fetch_error {type(e).__name__}: {e}'); ok=False; continue
        if not local.exists(): print(f'{s} missing_local'); ok=False; continue
        lh=hashlib.sha256(local.read_bytes()).hexdigest(); rh=hashlib.sha256(remote).hexdigest()
        match=lh==rh
        print(f'{s} pinned_match={match} local_sha256={lh[:16]} remote_sha256={rh[:16]}')
        ok &= match
    return 0 if ok else 1
if __name__=='__main__': sys.exit(main())
