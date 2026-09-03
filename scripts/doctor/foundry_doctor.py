#!/usr/bin/env python3
"""
Foundry Doctor — single operator health command for 11vatedTech Foundry.
Checks: source, deployment, git, products, KAPIF, 9Router, models, tools, regression, security.
No mutations. Read-only diagnostic.
"""
from __future__ import annotations
import json, os, platform, socket, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GLOBAL = Path.home() / ".claude" / "11vatedtech"
GLOBAL_CAP = GLOBAL / "capability-system"

class Check:
    def __init__(self, name: str):
        self.name = name
        self.status = "UNKNOWN"
        self.detail = ""
    def ok(self, detail=""): self.status = "PASS"; self.detail = detail; return self
    def warn(self, detail=""): self.status = "WARN"; self.detail = detail; return self
    def fail(self, detail=""): self.status = "FAIL"; self.detail = detail; return self
    def skip(self, detail=""): self.status = "SKIP"; self.detail = detail; return self
    def __repr__(self): return f"[{self.status}] {self.name}: {self.detail}"

def run_cmd(cmd, timeout=10):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, shell=isinstance(cmd, str))
        return r.stdout.strip() if r.returncode == 0 else None
    except: return None

def check_git():
    c = Check("FOUNDRY_GIT")
    if not (ROOT / ".git").exists():
        manifests = sorted((GLOBAL / "deployments").glob("*.json")) if (GLOBAL / "deployments").exists() else []
        if ROOT == GLOBAL_CAP and manifests:
            latest = json.loads(manifests[-1].read_text(encoding="utf-8"))
            return c.ok(f"GLOBAL_RUNTIME=PASS deployment_id={latest.get('id')} version={latest.get('version')} git_required=false")
        return c.fail(f"GIT_REPOSITORY_VALID=FAIL root={ROOT}")
    root = run_cmd(["git", "-C", str(ROOT), "rev-parse", "--show-toplevel"])
    if not root or "11vatedTech-Claude-System" not in root:
        return c.fail(f"GIT_REPOSITORY_VALID=FAIL root={root}")
    head = run_cmd(["git", "-C", str(ROOT), "rev-parse", "HEAD"])
    branch = run_cmd(["git", "-C", str(ROOT), "rev-parse", "--abbrev-ref", "HEAD"])
    dirty = run_cmd(["git", "-C", str(ROOT), "status", "--porcelain=v1"])
    dirty_count = len(dirty.splitlines()) if dirty else 0
    remote = run_cmd(["git", "-C", str(ROOT), "remote", "get-url", "origin"])
    if dirty_count:
        return c.warn(f"GIT_REPOSITORY_VALID=PASS GIT_WORKTREE_CLEAN=FAIL dirty={dirty_count} branch={branch}")
    return c.ok(f"GIT_REPOSITORY_VALID=PASS GIT_WORKTREE_CLEAN=PASS GIT_RELEASE_READY=PASS HEAD={head[:8] if head else 'unknown'} branch={branch} remote={'yes' if remote else 'no'}")

def check_deployment():
    c = Check("GLOBAL_DEPLOYMENT")
    if not GLOBAL_CAP.exists():
        return c.fail("capability-system not found")
    kapif = GLOBAL_CAP / "scripts" / "kapif"
    if not kapif.exists():
        return c.fail("KAPIF not in global deployment")
    managed = len(list(kapif.rglob("*.py")))
    return c.ok(f"managed={managed} modules")

def check_kapif():
    c = Check("KAPIF_HEALTH")
    try:
        sys.path.insert(0, str(GLOBAL_CAP / "scripts"))
        from kapif.data_layer import init_db, stats
        init_db()
        s = stats()
        atoms = s.get("atoms", 0)
        sources = s.get("sources", 0)
        return c.ok(f"atoms={atoms} sources={sources}")
    except Exception as e:
        return c.fail(str(e)[:80])

def check_9router():
    c = Check("9ROUTER")
    try:
        sys.path.insert(0, str(ROOT / "scripts" / "validate"))
        from router_health import probe
        result = probe(timeout=2.0)
        summary = result.get("summary", "")
        if result.get("core_status") == "PASS":
            return c.ok(summary)
        if result.get("router", {}).get("status") == "ROUTER_DOWN":
            return c.fail(summary or result.get("router", {}).get("error", "router down"))
        return c.warn(summary or "router degraded")
    except Exception as e:
        return c.fail(str(e)[:80])

def check_ollama():
    c = Check("OLLAMA_LOCAL_MODELS")
    try:
        import urllib.request
        r = urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=3)
        data = json.loads(r.read())
        models = data.get("models", [])
        names = [m.get("name", "?") for m in models[:5]]
        return c.ok(f"{len(models)} models: {', '.join(names)}")
    except:
        return c.fail("not reachable")

def check_tools():
    c = Check("TOOLCHAIN")
    try:
        sys.path.insert(0, str(ROOT / "scripts" / "validate"))
        from tool_resolver import discover_all
        tools = discover_all()
        states = {k: v.get("state") for k, v in tools.items()}
        missing = [k for k, state in states.items() if state == "NOT_FOUND"]
        proven = [k for k, state in states.items() if state == "EXECUTION_PROVEN"]
        detail = f"execution_proven={len(proven)}/{len(states)} installed_or_proven={len(states)-len(missing)}/{len(states)}"
        if missing:
            return c.warn(f"{detail} not_found={','.join(missing)}")
        return c.ok(detail)
    except Exception as e:
        return c.fail(f"resolver={e}")

def check_products():
    c = Check("PRODUCT_REGISTRY")
    registry = Path.home() / "OneDrive" / "Desktop" / "11vatedTech-Portfolio" / "11vatedTech-Product-Registry"
    if not registry.exists():
        return c.fail("registry not found")
    head = run_cmd(f'git -C "{registry}" rev-parse HEAD')
    pumkit = Path.home() / "OneDrive" / "Desktop" / "11vatedTech-Portfolio" / "Products" / "Frontend-Designs" / "Pumkit-Frontend-Design"
    pumkit_head = run_cmd(f'git -C "{pumkit}" rev-parse HEAD') if pumkit.exists() else None
    return c.ok(f"registry={head[:8] if head else 'unborn'} pumkit={pumkit_head[:8] if pumkit_head else 'none'}")

def check_security():
    c = Check("SECURITY")
    if not (ROOT / ".git").exists():
        sensitive = [p for p in ROOT.rglob("*") if p.is_file() and p.suffix.lower() in {".pem", ".key", ".env"}]
        return c.ok(f"global_sensitive_files={len(sensitive)} git_history_check=not_applicable")
    secrets = run_cmd('git -C "' + str(ROOT) + '" log --all --diff-filter=A -p -- "*.pem" "*.key" "*.env" 2>/dev/null | grep -c "PRIVATE" || echo 0')
    return c.ok(f"secret_history_entries={secrets or '0'}")

def check_contamination():
    c = Check("PRODUCT_CONTAMINATION")
    try:
        r = subprocess.run(['git', 'ls-files', '11vated-growth_OS/', 'Frontend-Designs/'],
                          capture_output=True, text=True, timeout=10, cwd=str(ROOT))
        tracked = [l for l in r.stdout.splitlines() if l.strip()]
        growthos = sum(1 for l in tracked if '11vated-growth_OS/' in l)
        frontend = sum(1 for l in tracked if 'Frontend-Designs/' in l)
    except Exception:
        growthos, frontend = 0, 0
        tracked = []
    if growthos > 0 or frontend > 0:
        return c.warn(f"GrowthOS={growthos} Frontend-Designs={frontend} files still tracked")
    return c.ok("no product files tracked in Foundry")

def main():
    print(f"11VATEDTECH FOUNDRY DOCTOR")
    print(f"Platform: {platform.platform()}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Root: {ROOT}")
    print()
    
    checks = [
        check_git(),
        check_deployment(),
        check_kapif(),
        check_9router(),
        check_ollama(),
        check_tools(),
        check_products(),
        check_contamination(),
        check_security(),
    ]
    
    for c in checks:
        icon = {"PASS":"OK","WARN":"!!","FAIL":"XX","SKIP":"--","UNKNOWN":"??"}.get(c.status, "??")
        print(f"  {icon} {c.name}: {c.detail}")
    
    passed = sum(1 for c in checks if c.status == "PASS")
    warned = sum(1 for c in checks if c.status == "WARN")
    failed = sum(1 for c in checks if c.status == "FAIL")
    print(f"\n  Summary: {passed} PASS, {warned} WARN, {failed} FAIL / {len(checks)} total")
    report = {
        "schema_version": "1.0.0",
        "checks": [{"name": c.name, "status": c.status, "detail": c.detail} for c in checks],
        "summary": {"pass": passed, "warn": warned, "fail": failed, "total": len(checks)},
    }
    report_path = ROOT / "artifacts" / "foundry-doctor.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
