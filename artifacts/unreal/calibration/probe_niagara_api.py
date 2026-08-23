import json
from pathlib import Path
import unreal

names = [name for name in dir(unreal) if "Niagara" in name and any(token in name for token in ("Factory", "System", "Emitter", "Script", "Module"))]
report = {"schema_version": 1, "status": "PASS", "niagara_symbols": names, "factories": {name: str(getattr(unreal, name)) for name in names if "Factory" in name}}
Path(__file__).with_name("niagara-api-probe.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report))
