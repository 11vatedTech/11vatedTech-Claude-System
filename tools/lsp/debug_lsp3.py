#!/usr/bin/env python3
"""Minimal reproduction: Popen + first stdout read."""
import subprocess, time, json
from pathlib import Path

TOOLS = Path('tools/lsp').resolve()
clangd = str(TOOLS / 'clangd-dist' / 'clangd_22.1.6' / 'bin' / 'clangd.exe')
root = Path('tools/fixtures/semantic-golden/cpp').resolve()

t0 = time.perf_counter()
proc = subprocess.Popen(
    [clangd, '--header-insertion=never', f'--compile-commands-dir={root}'],
    cwd=str(root), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
)
print(f'POPEN_OK pid={proc.pid} {time.perf_counter()-t0:.2f}s', flush=True)

# Send initialize
req = json.dumps({'jsonrpc':'2.0','id':1,'method':'initialize','params':{
    'processId':None,'rootUri':root.as_uri(),'capabilities':{},
}})
body = req.encode('utf-8')
header = f'Content-Length: {len(body)}\r\n\r\n'.encode('ascii')
proc.stdin.write(header + body)
proc.stdin.flush()
print(f'INIT_SENT {time.perf_counter()-t0:.2f}s', flush=True)

import threading
result = [None]
def read_resp():
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
                    result[0] = json.loads(rest[:n])
                    return
t = threading.Thread(target=read_resp, daemon=True)
t.start()
t.join(10)

if result[0]:
    info = result[0].get('result',{}).get('serverInfo',{})
    print(f'INIT_RESP {info.get("name")} v{info.get("version")} {time.perf_counter()-t0:.2f}s', flush=True)
else:
    print(f'NO_RESP {time.perf_counter()-t0:.2f}s', flush=True)

proc.terminate()
proc.wait()