import json
from pathlib import Path
import unreal

THIS = Path(__file__).resolve().parent
REPORT = THIS / "ashwake-vfx-upgrade-report.json"
DEST_DIR = "/Game/Calibration/VFX"
DEST_NAME = "NS_Emberveil_Attune"
DEST_PATH = f"{DEST_DIR}/{DEST_NAME}"

report = {
    "schema_version": 1,
    "kind": "ashwake-vfx-upgrade",
    "status": "STARTED",
    "dest_path": DEST_PATH,
    "strategy": "cook_safe_factory_asset",
    "actions": [],
}

try:
    asset_lib = unreal.EditorAssetLibrary
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    if not asset_lib.does_directory_exist(DEST_DIR):
        asset_lib.make_directory(DEST_DIR)
        report["actions"].append("created_vfx_directory")

    if asset_lib.does_asset_exist(DEST_PATH):
        deleted = asset_lib.delete_asset(DEST_PATH)
        report["actions"].append({"delete_existing": DEST_PATH, "deleted": bool(deleted)})

    factory = unreal.NiagaraSystemFactoryNew()
    system = tools.create_asset(DEST_NAME, DEST_DIR, unreal.NiagaraSystem, factory)
    if not system:
        raise RuntimeError("create_asset failed for cook-safe NiagaraSystem")

    saved = asset_lib.save_loaded_asset(system)
    loaded = unreal.load_asset(f"{DEST_PATH}.{DEST_NAME}") or unreal.load_asset(DEST_PATH)
    report.update({
        "status": "PASS" if loaded and saved else "FAIL",
        "created_path": system.get_path_name(),
        "saved": bool(saved),
        "loaded_after_create": bool(loaded),
        "loaded_class": loaded.get_class().get_name() if loaded else None,
        "note": "Template Niagara systems were not duplicated because packaged runtime hit UNiagaraStatelessEmitter::Serialize assertion in UE 5.8.",
    })
except Exception as exc:
    report.update({"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"})

REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report))
