import json
from pathlib import Path
import unreal

objects = {}
for cls_name in ["NiagaraSystemFactoryNew", "NiagaraEmitterFactoryNew", "NiagaraSystem", "NiagaraEmitter"]:
    cls = getattr(unreal, cls_name, None)
    if cls:
        try: objects[cls_name] = [name for name in dir(cls) if not name.startswith("_")]
        except Exception as exc: objects[cls_name] = [f"ERROR {exc}"]
Path(__file__).with_name("niagara-object-probe.json").write_text(json.dumps(objects, indent=2), encoding="utf-8")
print(json.dumps(objects))
