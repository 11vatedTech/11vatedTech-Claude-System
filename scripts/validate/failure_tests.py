#!/usr/bin/env python3
"""Failure-path tests — the difference between a check that exists and a check
that works. Each test deliberately breaks something and asserts the gate
catches it. An L5 capability must fail loudly on its failure path, not pass
silently.

Covered here (fast, no Blender render):
- pixel diff / PSNR: different images must be flagged not-equivalent
- GLB structural validator: corrupt GLB must be rejected
- rollback guard: unknown deployment must error, not silently succeed
- asset resolver: unknown-license external must be blocked
- asset vault: unknown license/source must be rejected on add
- routing eval: a coverage gap must fail (mutation)
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "media"))
sys.path.insert(0, str(ROOT / "scripts" / "assets"))


def run(cmd, timeout=120):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout, r.stderr


def test_pixel_diff_catches_difference() -> bool:
    from vtmedia import image_tools
    with tempfile.TemporaryDirectory() as td:
        a = Path(td) / "a.png"
        b = Path(td) / "b.png"
        image_tools.make_gradient(a, 64, 64)
        image_tools.alpha_test(b, 64, 64)
        cmp = image_tools.compare_images(a, b)
        ok = cmp["mode"] == "imagemagick_absolute_error" and (cmp.get("absolute_error") or 0) > 0
        ok = ok and cmp.get("visual_equivalence_claim") is False
        print("  pixel_diff", "ok" if ok else f"FAIL {cmp}")
        return ok


def test_glb_validator_rejects_corrupt() -> bool:
    from vtmedia.blender_ops import glb_validate
    src = ROOT / "artifacts" / "creative-stack-validation" / "blender-ops" / "hero-scene.glb"
    if not src.exists():
        print("  glb_validator SKIP no_sample_glb")
        return True
    with tempfile.TemporaryDirectory() as td:
        good = glb_validate(src)
        assert good["valid"], f"sample GLB should be valid: {good}"
        trunc = Path(td) / "trunc.glb"
        trunc.write_bytes(src.read_bytes()[:40])  # corrupt: header promises more bytes
        bad = glb_validate(trunc)
        ok = bad.get("valid") is False and "error" in bad
        # bad magic
        badmagic = Path(td) / "bad.glb"
        data = bytearray(src.read_bytes())
        data[0:4] = b"NOPE"
        badmagic.write_bytes(bytes(data))
        ok = ok and glb_validate(badmagic).get("valid") is False
        print("  glb_validator", "ok" if ok else "FAIL")
        return ok


def test_rollback_guard() -> bool:
    code, out, err = run([sys.executable, str(ROOT / "scripts/install/sync_to_claude.py"),
                          "--rollback", "00000000-000000"])
    ok = code != 0 and "no_manifest" in out
    print("  rollback_guard", "ok" if ok else f"FAIL rc={code} {out[:120]}")
    return ok


def test_resolver_blocks_unknown_license_external() -> bool:
    from asset_resolver import resolve
    r = resolve({"name": "external_tex", "category": "2d-texture",
                 "flags": {"license_known": False, "needs_originality": False}})
    ok = "SOURCE_EXTERNAL" in r["blocked_modes"]
    ok = ok and r["decision"]["mode"] != "SOURCE_EXTERNAL"
    print("  resolver_license_block", "ok" if ok else f"FAIL {r}")
    return ok


def test_vault_rejects_unknown_license() -> bool:
    from asset_vault import Vault
    with tempfile.TemporaryDirectory() as td:
        v = Vault(Path(td) / "v.json", Path(td) / "blobs")
        p = Path(td) / "x.png"
        p.write_bytes(b"fake")
        bad_license = v.add(p, source="internal", license_="made-up-license")
        bad_source = v.add(p, source="made-up-source", license_="cc0")
        ok = (not bad_license["ok"]) and (not bad_source["ok"])
        print("  vault_license_guard", "ok" if ok else "FAIL")
        return ok


def test_routing_mutation() -> bool:
    """A routing coverage gap must fail the routing eval."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("routing_eval", ROOT / "scripts/validate/routing_eval.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.load_cases = lambda: [{"prompt": "do motion design work", "expect": ["11vt-skill-foundry"], "expect_not": []}]
    rc = m.main()
    ok = rc == 1
    print("  routing_mutation", "ok" if ok else "FAIL (gap not detected)")
    return ok


def main() -> int:
    tests = [
        ("pixel_diff", test_pixel_diff_catches_difference),
        ("glb_validator", test_glb_validator_rejects_corrupt),
        ("rollback_guard", test_rollback_guard),
        ("resolver_license_block", test_resolver_blocks_unknown_license_external),
        ("vault_license_guard", test_vault_rejects_unknown_license),
        ("routing_mutation", test_routing_mutation),
    ]
    failures = []
    for name, fn in tests:
        try:
            if not fn():
                failures.append(name)
        except Exception as exc:
            failures.append(name)
            print(f"  {name} ERROR {type(exc).__name__}: {exc}")
    print(f"failure_tests={len(tests)} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
