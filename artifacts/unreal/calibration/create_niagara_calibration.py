import json
from pathlib import Path
import unreal

report = {"schema_version": 1, "status": "STARTED", "assets": []}
try:
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    emitter_factory = unreal.NiagaraEmitterFactoryNew()
    emitter = tools.create_asset("NE_Emberveil_Attune", "/Game/Calibration/VFX", unreal.NiagaraEmitter, emitter_factory)
    report["assets"].append({"kind": "emitter", "path": str(emitter.get_path_name()) if emitter else None})
    system_factory = unreal.NiagaraSystemFactoryNew()
    system = tools.create_asset("NS_Emberveil_Attune", "/Game/Calibration/VFX", unreal.NiagaraSystem, system_factory)
    report["assets"].append({"kind": "system", "path": str(system.get_path_name()) if system else None})
    report["status"] = "PASS" if emitter and system else "FAIL"
except Exception as exc:
    report.update({"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"})
Path(__file__).with_name("niagara-calibration-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report))
