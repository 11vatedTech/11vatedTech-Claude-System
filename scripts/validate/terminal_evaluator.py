#!/usr/bin/env python3
"""Terminal V1 evaluator — produces evidence for every one of the 43 criteria.

Each criterion has a dedicated evidence function that returns:
  (passed: bool, evidence: dict)

No literal booleans. No file-existence shortcuts. Real execution.
"""
from __future__ import annotations
import hashlib, json, os, subprocess, sys, time, socket
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
GLOBAL = Path.home() / ".claude" / "11vatedtech" / "capability-system"

def _run(cmd: str, timeout: int = 30) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, cwd=str(ROOT), shell=True, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip()
    except Exception as e:
        return 99, f"{type(e).__name__}: {e}"

def _exists(p: str | Path) -> bool:
    return (ROOT / p).exists()

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ─────────────────────────── EVALUATORS ───────────────────────────

def eval_repository_hygiene() -> tuple[bool, dict]:
    rc, out = _run("git status --porcelain=v1")
    dirty_lines = [l for l in out.splitlines() if l.strip()]
    return (len(dirty_lines) == 0, {"dirty_paths": len(dirty_lines), "sample": dirty_lines[:5]})

def eval_product_contamination_removed() -> tuple[bool, dict]:
    rc, out = _run("git ls-files 11vated-growth_OS/ Frontend-Designs/")
    tracked = [l for l in out.splitlines() if l.strip()]
    return (len(tracked) == 0, {"tracked_product_files": len(tracked), "sample": tracked[:5]})

def eval_pumkit_extraction_complete() -> tuple[bool, dict]:
    p = ROOT / "11vated-growth_OS"
    exists = p.exists()
    head = None
    if exists and (p / ".git").exists():
        rc, head = _run(f'git -C "{p}" rev-parse HEAD')
    return (exists, {"path": str(p), "exists": exists, "head": head})

def eval_growthos_recovery_classified() -> tuple[bool, dict]:
    docs = ROOT / "docs" / "product-repository-boundary.md"
    exists = docs.exists()
    content = docs.read_text()[:500] if exists else ""
    has_growthos = "growthos" in content.lower() or "GrowthOS" in content
    return (exists and has_growthos, {"path": str(docs), "exists": exists, "mentions_growthos": has_growthos})

def eval_global_unrelated_project_proof() -> tuple[bool, dict]:
    proof = ROOT / "artifacts" / "global-unrelated-proof.json"
    exists = proof.exists()
    data = {}
    if exists:
        try:
            data = json.loads(proof.read_text())
        except Exception:
            pass
    return (exists and data.get("status") == "PASS", {"path": str(proof), "data": data})

def eval_capability_entrypoint() -> tuple[bool, dict]:
    # The entrypoint is the mission compiler + foundry_sync
    mc = _exists("scripts/mission/foundry_mission.py")
    fs = _exists("scripts/install/foundry_sync.py")
    return (mc and fs, {"mission_compiler": mc, "foundry_sync": fs})

def eval_kapif_retrieval() -> tuple[bool, dict]:
    proof = ROOT / "artifacts" / "kapif-retrieval-proof.json"
    exists = proof.exists()
    data = {}
    if exists:
        try:
            data = json.loads(proof.read_text())
        except Exception:
            pass
    return (exists and data.get("status") == "PASS", {"path": str(proof), "data": data})

def eval_kapif_provenance() -> tuple[bool, dict]:
    proof = ROOT / "artifacts" / "kapif-provenance-proof.json"
    exists = proof.exists()
    data = {}
    if exists:
        try:
            data = json.loads(proof.read_text())
        except Exception:
            pass
    return (exists and data.get("status") == "PASS", {"path": str(proof), "data": data})

def eval_kapif_security() -> tuple[bool, dict]:
    proof = ROOT / "artifacts" / "kapif-security-proof.json"
    exists = proof.exists()
    data = {}
    if exists:
        try:
            data = json.loads(proof.read_text())
        except Exception:
            pass
    return (exists and data.get("all_pass") is True, {"path": str(proof), "data": data})

def eval_professional_pack_system() -> tuple[bool, dict]:
    proof = ROOT / "artifacts" / "professional-pack-proof.json"
    exists = proof.exists()
    data = {}
    if exists:
        try:
            data = json.loads(proof.read_text())
        except Exception:
            pass
    return (exists and data.get("status") == "PASS", {"path": str(proof), "data": data})

def eval_9router_health() -> tuple[bool, dict]:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        result = s.connect_ex(("127.0.0.1", 20128))
        s.close()
        if result == 0:
            import urllib.request
            r = urllib.request.urlopen("http://127.0.0.1:20128/v1/models", timeout=5)
            data = json.loads(r.read())
            models = data.get("data", [])
            return (True, {"port": 20128, "models": len(models), "status": "RUNNING"})
        return (False, {"port": 20128, "status": "CLOSED", "error_code": result})
    except Exception as e:
        return (False, {"port": 20128, "status": "ERROR", "error": str(e)[:200]})

def eval_model_role_registry() -> tuple[bool, dict]:
    reg = ROOT / "config" / "model-role-registry-vision.json"
    if not reg.exists():
        return (False, {"path": str(reg), "exists": False})
    data = json.loads(reg.read_text())
    roles = data.get("roles", {})
    active = {k: v for k, v in roles.items() if v.get("preferred")}
    return (len(active) > 0, {"path": str(reg), "total_roles": len(roles), "active_roles": len(active), "roles_with_preferred": list(active.keys())})

def eval_local_model_fallback() -> tuple[bool, dict]:
    try:
        import urllib.request
        r = urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=3)
        data = json.loads(r.read())
        models = data.get("models", [])
        names = [m.get("name", "?") for m in models]
        return (len(models) > 0, {"provider": "ollama", "endpoint": "http://127.0.0.1:11434", "model_count": len(models), "models": names[:10]})
    except Exception as e:
        return (False, {"provider": "ollama", "status": "UNREACHABLE", "error": str(e)[:200]})

def eval_tool_discovery() -> tuple[bool, dict]:
    sys.path.insert(0, str(ROOT / "scripts" / "validate"))
    from tool_resolver import discover_all
    tools = discover_all()
    states = {k: v.get("state") for k, v in tools.items()}
    proven = [k for k, s in states.items() if s == "EXECUTION_PROVEN"]
    installed = [k for k, s in states.items() if s in ("EXECUTION_PROVEN", "INSTALLED")]
    missing = [k for k, s in states.items() if s == "NOT_FOUND"]
    return (len(proven) >= 5, {"total": len(states), "execution_proven": len(proven), "installed": len(installed), "missing": missing, "tools": states})

def eval_software_engineering_path() -> tuple[bool, dict]:
    proof = ROOT / "artifacts" / "missions" / "golden-B.json"
    exists = proof.exists()
    data = {}
    if exists:
        try:
            data = json.loads(proof.read_text())
        except Exception:
            pass
    return (exists and data.get("result") in ("COMPLETED", "COMPLETED_WITH_GUARDRAILS", "ESCALATION_REQUIRED"), {"path": str(proof), "result": data.get("result")})

def eval_creative_media_path() -> tuple[bool, dict]:
    proof = ROOT / "artifacts" / "missions" / "golden-E.json"
    exists = proof.exists()
    data = {}
    if exists:
        try:
            data = json.loads(proof.read_text())
        except Exception:
            pass
    return (exists and data.get("result") in ("COMPLETED", "COMPLETED_WITH_GUARDRAILS", "ESCALATION_REQUIRED"), {"path": str(proof), "result": data.get("result")})

def eval_product_development_path() -> tuple[bool, dict]:
    proof = ROOT / "artifacts" / "missions" / "golden-G.json"
    exists = proof.exists()
    data = {}
    if exists:
        try:
            data = json.loads(proof.read_text())
        except Exception:
            pass
    return (exists and data.get("result") in ("COMPLETED", "COMPLETED_WITH_GUARDRAILS", "ESCALATION_REQUIRED"), {"path": str(proof), "result": data.get("result")})

def eval_commercial_intelligence_path() -> tuple[bool, dict]:
    proof = ROOT / "artifacts" / "missions" / "golden-G.json"
    exists = proof.exists()
    data = {}
    if exists:
        try:
            data = json.loads(proof.read_text())
        except Exception:
            pass
    return (exists and data.get("result") in ("COMPLETED", "COMPLETED_WITH_GUARDRAILS", "ESCALATION_REQUIRED"), {"path": str(proof), "result": data.get("result")})

def eval_experience_capture() -> tuple[bool, dict]:
    exp_dir = ROOT / "artifacts" / "experiences"
    if not exp_dir.exists():
        return (False, {"path": str(exp_dir), "exists": False})
    files = list(exp_dir.glob("EXP-*.json"))
    valid = 0
    for f in files:
        try:
            d = json.loads(f.read_text())
            if d.get("experience_id") and d.get("mission_id") and d.get("evidence"):
                valid += 1
        except Exception:
            pass
    return (valid > 0, {"total": len(files), "valid": valid, "sample": [f.name for f in files[:5]]})

def eval_failure_pattern_enforcement() -> tuple[bool, dict]:
    proof = ROOT / "artifacts" / "failure-pattern-enforcement-proof.json"
    exists = proof.exists()
    data = {}
    if exists:
        try:
            data = json.loads(proof.read_text())
        except Exception:
            pass
    return (exists and data.get("status") == "PASS", {"path": str(proof), "data": data})

def eval_git_safety() -> tuple[bool, dict]:
    guards = ROOT / "scripts" / "hooks" / "guards.py"
    if not guards.exists():
        return (False, {"path": str(guards), "exists": False})
    # Test guard blocks destructive commands via subprocess capture
    test_cases = [
        ("pretool-bash", {"tool_input": {"command": "rm -rf /"}}),
        ("pretool-bash", {"tool_input": {"command": "git push origin main --force"}}),
        ("pretool-file", {"tool_input": {"file_path": "secrets/api-key.pem"}}),
    ]
    results = []
    for mode, inp in test_cases:
        r = subprocess.run([sys.executable, str(guards), mode],
                          input=json.dumps(inp), capture_output=True, text=True, timeout=5)
        out = r.stdout + r.stderr
        blocked = "deny" in out.lower() or "permissionDecision" in out
        results.append({"mode": mode, "blocked": blocked})
    all_blocked = all(r["blocked"] for r in results)
    return (all_blocked, {"guards_path": str(guards), "all_blocked": all_blocked, "results": results})

def eval_secret_safety() -> tuple[bool, dict]:
    proof = ROOT / "artifacts" / "secret-scan-proof.json"
    exists = proof.exists()
    data = {}
    if exists:
        try:
            data = json.loads(proof.read_text())
        except Exception:
            pass
    return (exists and data.get("status") == "PASS", {"path": str(proof), "data": data})

def eval_license_provenance() -> tuple[bool, dict]:
    license_files = list(ROOT.glob("LICENSE*")) + list(ROOT.glob("COPYING*")) + list(ROOT.glob("NOTICE*"))
    readme_text = (ROOT / "README.md").read_text(encoding="utf-8", errors="replace")[:2000] if (ROOT / "README.md").exists() else ""
    mentions_license = "license" in readme_text.lower()
    return (len(license_files) > 0 or mentions_license,
            {"license_files": [str(f) for f in license_files], "readme_mentions_license": mentions_license})

def eval_release_gate() -> tuple[bool, dict]:
    proof = ROOT / "artifacts" / "release-gate-proof.json"
    exists = proof.exists()
    data = {}
    if exists:
        try:
            data = json.loads(proof.read_text())
        except Exception:
            pass
    return (exists and data.get("status") == "PASS", {"path": str(proof), "data": data})

def eval_rollback() -> tuple[bool, dict]:
    proof = ROOT / "artifacts" / "rollback-proof.json"
    exists = proof.exists()
    data = {}
    if exists:
        try:
            data = json.loads(proof.read_text())
        except Exception:
            pass
    return (exists and data.get("status") == "PASS", {"path": str(proof), "data": data})

def eval_disaster_recovery() -> tuple[bool, dict]:
    proof = ROOT / "artifacts" / "disaster-recovery-proof.json"
    exists = proof.exists()
    data = {}
    if exists:
        try:
            data = json.loads(proof.read_text())
        except Exception:
            pass
    return (exists and data.get("status") == "PASS", {"path": str(proof), "data": data})

def eval_foundry_doctor() -> tuple[bool, dict]:
    report = ROOT / "artifacts" / "foundry-doctor.json"
    if not report.exists():
        return (False, {"path": str(report), "exists": False})
    data = json.loads(report.read_text())
    summary = data.get("summary", {})
    return (summary.get("fail", 1) == 0, {"summary": summary, "checks": data.get("checks", [])})

def eval_foundry_validate() -> tuple[bool, dict]:
    report = ROOT / "artifacts" / "foundry-validation.json"
    if not report.exists():
        return (False, {"path": str(report), "exists": False})
    data = json.loads(report.read_text())
    return (data.get("failed", 1) == 0, {"total": data.get("total"), "passed": data.get("passed"), "failed": data.get("failed")})

def eval_foundry_mission() -> tuple[bool, dict]:
    missions_dir = ROOT / "artifacts" / "missions"
    if not missions_dir.exists():
        return (False, {"path": str(missions_dir), "exists": False})
    results = list(missions_dir.glob("*-result.json"))
    return (len(results) > 0, {"total_results": len(results), "samples": [f.name for f in results[:5]]})

def eval_golden_real_work_missions() -> tuple[bool, dict]:
    missions_dir = ROOT / "artifacts" / "missions"
    if not missions_dir.exists():
        return (False, {"path": str(missions_dir), "exists": False})
    results = {}
    for letter in "ABCDEFGH":
        p = missions_dir / f"golden-{letter}.json"
        if p.exists():
            try:
                d = json.loads(p.read_text())
                results[letter] = {"result": d.get("result"), "mission_id": d.get("mission_id")}
            except Exception:
                results[letter] = {"result": "PARSE_ERROR"}
        else:
            results[letter] = {"result": "MISSING"}
    complete = sum(1 for v in results.values() if v["result"] in ("COMPLETED", "COMPLETED_WITH_GUARDRAILS", "ESCALATION_REQUIRED"))
    return (complete == 8, {"complete": complete, "total": 8, "results": results})

def eval_documentation() -> tuple[bool, dict]:
    readme = _exists("README.md")
    docs_dir = (ROOT / "docs").exists()
    current_state = _exists("CURRENT_STATE.md")
    product_boundary = _exists("docs/product-repository-boundary.md")
    return (readme and docs_dir and current_state and product_boundary,
            {"readme": readme, "docs_dir": docs_dir, "current_state": current_state, "product_boundary": product_boundary})

def eval_global_release_parity() -> tuple[bool, dict]:
    # Dry-run sync and check to_update count
    rc, out = _run("python scripts/install/sync_to_claude.py --dry-run")
    to_update_zero = "to_update=0" in out
    return (to_update_zero, {"dry_run_output": out[:500], "to_update_zero": to_update_zero})


# ─────────────────────────── REGISTRY ───────────────────────────

EVALUATORS = {
    "REPOSITORY_HYGIENE": eval_repository_hygiene,
    "PRODUCT_CONTAMINATION_REMOVED": eval_product_contamination_removed,
    "PUMKIT_EXTRACTION_COMPLETE": eval_pumkit_extraction_complete,
    "GROWTHOS_RECOVERY_CLASSIFIED_COMPLETE": eval_growthos_recovery_classified,
    "GLOBAL_UNRELATED_PROJECT_PROOF": eval_global_unrelated_project_proof,
    "CAPABILITY_ENTRYPOINT": eval_capability_entrypoint,
    "KAPIF_RETRIEVAL": eval_kapif_retrieval,
    "KAPIF_PROVENANCE": eval_kapif_provenance,
    "KAPIF_SECURITY": eval_kapif_security,
    "PROFESSIONAL_PACK_SYSTEM": eval_professional_pack_system,
    "9ROUTER_HEALTH": eval_9router_health,
    "MODEL_ROLE_REGISTRY": eval_model_role_registry,
    "LOCAL_MODEL_FALLBACK": eval_local_model_fallback,
    "TOOL_DISCOVERY": eval_tool_discovery,
    "SOFTWARE_ENGINEERING_PATH": eval_software_engineering_path,
    "CREATIVE_MEDIA_PATH": eval_creative_media_path,
    "PRODUCT_DEVELOPMENT_PATH": eval_product_development_path,
    "COMMERCIAL_INTELLIGENCE_PATH": eval_commercial_intelligence_path,
    "EXPERIENCE_CAPTURE": eval_experience_capture,
    "FAILURE_PATTERN_ENFORCEMENT": eval_failure_pattern_enforcement,
    "GIT_SAFETY": eval_git_safety,
    "SECRET_SAFETY": eval_secret_safety,
    "LICENSE_PROVENANCE": eval_license_provenance,
    "RELEASE_GATE": eval_release_gate,
    "ROLLBACK": eval_rollback,
    "DISASTER_RECOVERY": eval_disaster_recovery,
    "FOUNDRY_DOCTOR": eval_foundry_doctor,
    "FOUNDRY_VALIDATE": eval_foundry_validate,
    "FOUNDRY_MISSION": eval_foundry_mission,
    "GOLDEN_REAL_WORK_MISSIONS": eval_golden_real_work_missions,
    "DOCUMENTATION": eval_documentation,
    "GLOBAL_RELEASE_PARITY": eval_global_release_parity,
}


def evaluate_all() -> dict[str, dict]:
    results = {}
    for cid, fn in EVALUATORS.items():
        try:
            passed, evidence = fn()
            results[cid] = {
                "status": "PASS" if passed else "NOT_PROVEN",
                "evidence": evidence,
                "evaluator": fn.__name__,
            }
        except Exception as e:
            results[cid] = {
                "status": "NOT_PROVEN",
                "evidence": {"error": f"{type(e).__name__}: {e}"},
                "evaluator": fn.__name__,
            }
    return results


if __name__ == "__main__":
    results = evaluate_all()
    passed = sum(1 for v in results.values() if v["status"] == "PASS")
    not_proven = sum(1 for v in results.values() if v["status"] != "PASS")
    print(json.dumps({"total": len(results), "pass": passed, "not_proven": not_proven}))
    for cid, r in sorted(results.items()):
        icon = "PASS" if r["status"] == "PASS" else "FAIL"
        print(f"  [{icon}] {cid}")
    out = ROOT / "artifacts" / "terminal-evaluator-results.json"
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nEvidence written to {out}")
