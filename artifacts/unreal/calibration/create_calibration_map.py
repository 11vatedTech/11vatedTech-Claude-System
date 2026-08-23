import json
from pathlib import Path
import unreal

path = "/Game/Calibration/Maps/EmberveilCalibration"
report_path = Path(__file__).with_name("map-authoring-report.json")
report = {"schema_version": 1, "map": path, "status": "STARTED"}
try:
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        world = level_editor.load_level(path)
        saved = bool(world)
    else:
        world = level_editor.new_level(path)
        saved = level_editor.save_current_level()
    report.update({"status": "PASS" if world and saved else "FAIL", "saved": bool(saved), "world": str(world)})
except Exception as exc:
    report.update({"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"})
report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report))
