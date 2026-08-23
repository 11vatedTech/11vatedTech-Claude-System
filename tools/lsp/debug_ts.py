import subprocess, json, threading, time
from pathlib import Path
TOOLS = str(Path('tools/lsp').resolve())
ts_server = 'node_modules/typescript-language-server/lib/cli.mjs'
root_uri = Path('tools/fixtures/semantic-golden/ts').resolve().as_uri()
proc = subprocess.Popen(
    ['node', ts_server, '--stdio'],
    cwd=TOOLS, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
)
t0 = time.perf_counter()
req = json.dumps({'jsonrpc':'2.0','id':1,'method':'initialize','params':{'processId':None,'rootUri':root_uri,'capabilities':{}}})
body = req.encode('utf-8')
proc.stdin.write(f'Content-Length: {len(body)}\r\n\r\n'.encode('ascii')+body)
proc.stdin.flush()
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
t = threading.Thread(target=read_resp, daemon=True); t.start()
t.join(20)
if result[0]:
    info = result[0].get('result',{}).get('serverInfo',{})
    print(f'OK {info.get("name")} v{info.get("version")} {time.perf_counter()-t0:.1f}s')
else:
    proc.terminate(); proc.wait()
    err = proc.stderr.read().decode(errors='replace')[:500]
    print(f'NO_RESP {time.perf_counter()-t0:.1f}s err={err[:300]}')