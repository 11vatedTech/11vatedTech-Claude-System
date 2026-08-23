#!/usr/bin/env python3
"""Import the real LspClient and use it, with inline tracing."""
import sys, time, threading, queue, traceback, os
from pathlib import Path
import json

# Add path
sys.path.insert(0, str(Path('scripts/repo').resolve()))

# Minimal inline tracing of the original _pump
import lsp_client as lc
orig_pump = lc.LspClient._pump
def traced_pump(self):
    print(f'PUMP_THREAD_STARTED id={threading.get_ident()}', flush=True)
    return orig_pump(self)
lc.LspClient._pump = traced_pump

root = Path('tools/fixtures/semantic-golden/cpp').resolve()
cmd = lc.provider_command('cpp', root, root)
print(f'CMD={cmd[0][-40:]}', flush=True)

t0 = time.perf_counter()
client = lc.LspClient(cmd, root, 'quick-test', timeout=5)
print(f'CREATED pid={client._proc.pid} pump_alive={client._thread.is_alive()} {time.perf_counter()-t0:.1f}s', flush=True)

client.initialize(root.as_uri())
print(f'INITED {time.perf_counter()-t0:.1f}s', flush=True)

client.shutdown()
print(f'DONE {time.perf_counter()-t0:.1f}s', flush=True)