"""Internal probe used by unreal_intelligence import-glb.

This is not the public abstraction: the public operation validates paths,
provenance destination, lifecycle, timeout, and returns structured evidence.
"""
import json
import os
from pathlib import Path
import unreal

source = Path(os.environ["FOUNDRY_IMPORT_SOURCE"])
report_path = Path(os.environ["FOUNDRY_IMPORT_REPORT"])
destination = os.environ["FOUNDRY_IMPORT_DEST"]
report = {"schema_version": 1, "source": str(source), "destination": destination, "status": "STARTED"}
try:
    if not source.exists() or source.suffix.lower() != ".glb":
        raise ValueError("source must be an existing GLB")
    task = unreal.AssetImportTask()
    task.filename = str(source)
    task.destination_path = destination
    task.automated = True
    task.replace_existing = True
    task.save = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    imported = list(getattr(task, "imported_object_paths", []) or [])
    report.update({"status": "PASS" if imported else "FAIL", "imported_object_paths": imported, "errors": list(getattr(task, "errors", []) or [])})
except Exception as exc:
    report.update({"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"})
report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report))
