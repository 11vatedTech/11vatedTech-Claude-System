#!/usr/bin/env python3
"""Test LspClient class with single file, no bus abstraction."""
import sys, time
from pathlib import Path

sys.path.insert(0, 'scripts/repo')
from lsp_client import LspClient, provider_command, to_uri, language_id_for

root = Path('tools/fixtures/semantic-golden/cpp').resolve()
cmd, cwd = provider_command('cpp', root, root)
print(f'CMD[0]={cmd[0]}', flush=True)

t0 = time.perf_counter()
client = LspClient(cmd, cwd, 'direct-test', timeout=20)
print(f'CREATED {time.perf_counter()-t0:.1f}s', flush=True)

try:
    client.initialize(root.as_uri())
    print(f'INITED {time.perf_counter()-t0:.1f}s', flush=True)
    
    f = root / 'src' / 'player.cpp'
    uri = to_uri(f)
    text = f.read_text(encoding='utf-8', errors='replace')
    client.open_document(uri, 'cpp', text)
    print(f'OPENED {time.perf_counter()-t0:.1f}s', flush=True)
    
    syms = client.document_symbols(uri)
    names = [s.get('name','?') for s in (syms if isinstance(syms,list) else [])]
    print(f'SYMBOLS={names} {time.perf_counter()-t0:.1f}s', flush=True)
finally:
    client.shutdown()
print(f'DONE {time.perf_counter()-t0:.1f}s', flush=True)