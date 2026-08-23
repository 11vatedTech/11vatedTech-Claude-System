#!/usr/bin/env python3
"""Trace LspClient internals to find the hang."""
import sys, time, threading, queue
from pathlib import Path

sys.path.insert(0, 'scripts/repo')

# Monkey-patch to trace
import lsp_client
orig_init = lsp_client.LspClient.__init__
def traced_init(self, cmd, cwd, name, timeout=60.0):
    print(f'LspClient.__init__ START name={name} pid=None', flush=True)
    orig_init(self, cmd, cwd, name, timeout)
    print(f'LspClient.__init__ DONE pid={self._proc.pid}', flush=True)
lsp_client.LspClient.__init__ = traced_init

orig_start = lsp_client.LspClient._start_pump
def traced_start(self):
    print(f'_start_pump START', flush=True)
    orig_start(self)
    print(f'_start_pump DONE', flush=True)
lsp_client.LspClient._start_pump = traced_start

orig_request = lsp_client.LspClient._request
def traced_request(self, method, params):
    print(f'_request START {method}', flush=True)
    r = orig_request(self, method, params)
    print(f'_request DONE {method}', flush=True)
    return r
lsp_client.LspClient._request = traced_request

orig_pump = lsp_client.LspClient._pump
def traced_pump(self):
    print(f'_pump START', flush=True)
    orig_pump(self)
    print(f'_pump END', flush=True)
lsp_client.LspClient._pump = traced_pump

from lsp_client import LspClient, provider_command, to_uri, language_id_for

root = Path('tools/fixtures/semantic-golden/cpp').resolve()
cmd = provider_command('cpp', root, root)
print(f'CMD[0]={cmd[0]}', flush=True)

t0 = time.perf_counter()
client = LspClient(cmd, root, 'trace-test', timeout=10)
print(f'CREATED {time.perf_counter()-t0:.1f}s', flush=True)

client.initialize(root.as_uri())
print(f'INITED {time.perf_counter()-t0:.1f}s', flush=True)

f = root / 'src' / 'player.cpp'
client.open_document(to_uri(f), 'cpp', f.read_text(encoding='utf-8', errors='replace'))
syms = client.document_symbols(to_uri(f))
print(f'SYMS={len(syms) if syms else 0} {time.perf_counter()-t0:.1f}s', flush=True)

client.shutdown()
print('DONE', flush=True)