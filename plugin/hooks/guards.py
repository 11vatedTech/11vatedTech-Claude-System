#!/usr/bin/env python3
from __future__ import annotations
import fnmatch, json, re, sys

def deny(reason):
    print(json.dumps({'hookSpecificOutput':{'hookEventName':'PreToolUse','permissionDecision':'deny','permissionDecisionReason':reason}})); sys.exit(0)

def main():
    mode=sys.argv[1] if len(sys.argv)>1 else ''
    try: data=json.load(sys.stdin)
    except Exception: data={}
    ti=data.get('tool_input',{})
    if mode=='pretool-bash':
        cmd=ti.get('command','')
        bad=[r'\brm\s+-rf\s+[/~.]', r'git\s+push\s+.*--force', r'git\s+reset\s+--hard', r'git\s+clean\s+-fdx', r'curl\s+[^|]+\|\s*(sh|bash)']
        for pat in bad:
            if re.search(pat, cmd): deny('11vatedTech guard blocked destructive or unsafe shell command')
    if mode=='pretool-file':
        path=ti.get('file_path') or ti.get('path') or ''
        protected=['*.env','.env','*.pem','*.key','secrets/*','**/secrets/**']
        for pat in protected:
            if fnmatch.fnmatch(path.replace('\\','/'), pat): deny('11vatedTech guard blocked secret/protected path access')
    sys.exit(0)
if __name__=='__main__': main()
