import json
from pathlib import Path
import unreal

names = [name for name in dir(unreal) if "Niagara" in name or "Fx" in name or "FX" in name]
objects = {}
for cls_name in names:
    cls = getattr(unreal, cls_name, None)
    try:
        attrs = [name for name in dir(cls) if not name.startswith("_")]
    except Exception:
        attrs = []
    interesting = [a for a in attrs if any(token.lower() in a.lower() for token in ["emitter", "module", "script", "system", "renderer", "create", "add", "stack", "parameter"])]
    if interesting:
        objects[cls_name] = interesting[:120]
report = {"schema_version": 1, "status": "PASS", "classes": objects}
out = Path(__file__).with_name("niagara-editor-api-probe.json")
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report))
