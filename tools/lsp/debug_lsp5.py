#!/usr/bin/env python3
"""Clean test — no monkey-patching, trace via subprocess stdout directly."""
import subprocess, time, json, threading
from pathlib import Path

clangd = str(Path('tools/lsp/clangd-dist/clangd_22.1.6/bin/clangd.exe').resolve())
root = Path('tools/fixtures/semantic-golden/cpp').resolve()

proc = subprocess.Popen(
    [clangd, '--header-insertion=never', f'--compile-commands-dir={root}'],
    cwd=str(root), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
)
print(f'PID={proc.pid}', flush=True)

# Helper: send an LSP message
_sid = 1
def lsp_req(method, params):
    global _sid
    _sid += 1
    req = json.dumps({'jsonrpc':'2.0','id':_sid,'method':method,'params':params})
    body = req.encode('utf-8')
    proc.stdin.write(f'Content-Length: {len(body)}\r\n\r\n'.encode('ascii') + body)
    proc.stdin.flush()

# Helper: read one LSP response
def lsp_read():
    buf = b''
    while True:
        c = proc.stdout.read(1)
        if not c: break
        buf += c
        if b'\r\n\r\n' in buf:
            hdr, rest = buf.split(b'\r\n\r\n', 1)
            for line in hdr.decode().split('\r\n'):
                if line.lower().startswith('content-length:'):
                    n = int(line.split(':',1)[1])
                    while len(rest) < n:
                        rest += proc.stdout.read(min(4096, n-len(rest)))
                    return json.loads(rest[:n])

# Initialize
lsp_req('initialize', {'processId':None,'rootUri':root.as_uri(),'capabilities':{}})
resp = lsp_read()
print(f'INIT id={resp.get("id")}', flush=True)

# Notify initialized
lsp_req('initialized', {'params':{}})

# Open a file
f = root / 'src' / 'player.cpp'
text = f.read_text(encoding='utf-8', errors='replace')
lsp_req('textDocument/didOpen', {'textDocument':{'uri':f.resolve().as_uri(),'languageId':'cpp','version':1,'text':text}})

# Request symbols
lsp_req('textDocument/documentSymbol', {'textDocument':{'uri':f.resolve().as_uri()}})
resp = lsp_read()
syms = resp.get('result', [])
print(f'SYMBOLS={len(syms)} names={[s.get("name") for s in syms[:5]]}', flush=True)

proc.terminate()
proc.wait()
print('DONE', flush=True)