import json
from pathlib import Path
import unreal

source = Path(__file__).resolve().parents[3] / "artifacts/creative-stack-validation/audio/source.wav"
report_path = Path(__file__).with_name("audio-import-report.json")
report = {"schema_version": 1, "source": str(source), "destination": "/Game/Calibration/Audio", "status": "STARTED", "provenance": {"license": "generated-local", "source": "ffmpeg sine 550Hz", "record": "artifacts/creative-stack-validation/audio/provenance.json"}}
try:
    task = unreal.AssetImportTask(); task.filename = str(source); task.destination_path = "/Game/Calibration/Audio"; task.automated = True; task.replace_existing = True; task.save = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    paths = list(getattr(task, "imported_object_paths", []) or [])
    report.update({"status": "PASS" if paths else "FAIL", "imported_object_paths": paths, "errors": list(getattr(task, "errors", []) or [])})
except Exception as exc:
    report.update({"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"})
report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report))
