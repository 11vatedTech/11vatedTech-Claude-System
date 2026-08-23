#!/usr/bin/env python3
import subprocess, time, threading, json
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[2] / 'tools' / 'lsp'
clangd = str(TOOLS / 'clangd-dist' / 'clangd_22.1.6' / 'bin' / 'clangd.exe')
root = Path('tools/fixtures/semantic-golden/cpp').resolve()

t0 = time.perf_counter()
proc = subprocess.Popen(
    [clangd, '--header-insertion=never'],
    cwd=str(root), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
)
print(f'POPEND {time.perf_counter()-t0:.1f}s', flush=True)

# Send initialize
req = json.dumps({'jsonrpc':'2.0','id':1,'method':'initialize','params':{
    'processId':None,'rootUri':root.as_uri(),'capabilities':{},
}})
body = req.encode('utf-8')
proc.stdin.write(f'Content-Length: {len(body)}\r\n\r\n'.encode('ascii') + body)
proc.stdin.flush()
print(f'SENT_INIT {time.perf_counter()-t0:.1f}s', flush=True)

# Read response
response = [None]
def reader():
    resp = b''
    while True:
        c = proc.stdout.read(1)
        if not c: break
        resp += c
        if b'\r\n\r\n' in resp:
            hdr, rest = resp.split(b'\r\n\r\n', 1)
            for line in hdr.decode().split('\r\n'):
                if line.lower().startswith('content-length:'):
                    length = int(line.split(':',1)[1])
                    while len(rest) < length:
                        rest += proc.stdout.read(min(4096, length-len(rest)))
                    response[0] = json.loads(rest[:length])
                    return
t = threading.Thread(target=reader, daemon=True); t.start()
t.join(60)
proc.terminate()
if response[0]:
    print(f'RESP id={response[0].get("id")} server={response[0].get("result",{}).get("serverInfo",{}).get("name")} {time.perf_counter()-t0:.1f}s', flush=True)
else:
    print(f'NO_RESPONSE_AFTER_60s', flush=True)