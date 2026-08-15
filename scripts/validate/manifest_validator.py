#!/usr/bin/env python3
from __future__ import annotations
import sys, re
from pathlib import Path

REQUIRED_TOP = ['schema_version:', 'product:', 'commands:', 'canon:']
REQUIRED_PRODUCT = ['  name:', '  type:', '  maturity:']

def validate(path: Path) -> list[str]:
    errors=[]
    if not path.exists():
        return [f'missing manifest: {path}']
    text=path.read_text(encoding='utf-8')
    for key in REQUIRED_TOP:
        if key not in text: errors.append(f'missing top-level key {key}')
    for key in REQUIRED_PRODUCT:
        if key not in text: errors.append(f'missing product key {key.strip()}')
    if 'schema_version: 1' not in text: errors.append('schema_version must be 1')
    if re.search(r'name:\s*["\']?TODO["\']?', text): errors.append('product.name still TODO')
    return errors

if __name__ == '__main__':
    p=Path(sys.argv[1]) if len(sys.argv)>1 else Path('11vt.project.yaml')
    errs=validate(p)
    if errs:
        print('\n'.join('ERROR '+e for e in errs)); sys.exit(1)
    print(f'manifest_ok {p}')
