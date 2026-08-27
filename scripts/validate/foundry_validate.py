#!/usr/bin/env python3
"""
Foundry Validate — top-level deterministic validation entrypoint.
Orchestrates existing validators. No mutations. Machine + human readable output.
"""
from __future__ import annotations
import json, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

class Gate:
    def __init__(self, name: str, cmd: str, timeout: int = 60):
        self.name = name
        self.cmd = cmd
        self.timeout = timeout
        self.status = "NOT_RUN"
        self.detail = ""
        self.duration = 0.0

    def run(self):
        t0 = time.time()
        try:
            r = subprocess.run(
                self.cmd, shell=True, capture_output=True, text=True,
                timeout=self.timeout, cwd=str(ROOT)
            )
            self.duration = time.time() - t0
            output = (r.stdout + r.stderr).strip()
            if r.returncode == 0:
                self.status = "PASS"
                self.detail = output[-200:] if len(output) > 200 else output
            else:
                self.status = "FAIL"
                self.detail = output[-300:] if len(output) > 300 else output
        except subprocess.TimeoutExpired:
            self.duration = time.time() - t0
            self.status = "TIMEOUT"
            self.detail = f"exceeded {self.timeout}s"
        except Exception as e:
            self.duration = time.time() - t0
            self.status = "ERROR"
            self.detail = str(e)[:200]

def main():
    gates = [
        Gate("closure_gates", "python scripts/kapif/closure_gates_pass06.py", 30),
        Gate("golden_tasks", "python scripts/kapif/golden_tasks_m002.py", 30),
        Gate("behavioral_validation", "python scripts/kapif/behavioral_validation_m0021.py", 30),
        Gate("injection_e2e", "python scripts/kapif/injection_e2e_validation.py", 30),
        Gate("deployment_parity", "python scripts/install/verify_kapif_deployment.py --quiet", 30),
        Gate("sync_dry_run", "python scripts/install/sync_to_claude.py --dry-run", 30),
        Gate("truth_generator", "python scripts/validate/canonical_truth_generator.py", 30),
        Gate("capability_truth_audit", "python scripts/validate/capability_truth_audit.py", 30),
        Gate("env_doctor", "python scripts/doctor/foundry_doctor.py", 30),
    ]

    print("11VATEDTECH FOUNDRY VALIDATE")
    print(f"Running {len(gates)} gates...\n")

    t0 = time.time()
    for g in gates:
        g.run()
        icon = {"PASS":"OK","FAIL":"XX","TIMEOUT":"TT","ERROR":"!!","NOT_RUN":"--"}.get(g.status,"??")
        print(f"  [{icon}] {g.name} ({g.duration:.1f}s): {g.detail[:80]}")

    total = time.time() - t0
    passed = sum(1 for g in gates if g.status == "PASS")
    failed = sum(1 for g in gates if g.status in ("FAIL","TIMEOUT","ERROR"))

    print(f"\n  RESULT: {passed}/{len(gates)} PASS in {total:.1f}s")
    if failed:
        print(f"  FAILED: {', '.join(g.name for g in gates if g.status != 'PASS')}")
    else:
        print("  ALL GATES PASS")

    # Machine-readable output
    result = {
        "validation_time": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total": len(gates),
        "passed": passed,
        "failed": failed,
        "gates": {g.name: {"status": g.status, "duration": round(g.duration, 1)} for g in gates}
    }
    out_path = ROOT / "artifacts" / "foundry-validation.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    print(f"\n  Machine-readable: {out_path}")

    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
