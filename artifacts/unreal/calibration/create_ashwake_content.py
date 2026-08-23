import json
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parents[3]
THIS = Path(__file__).resolve().parent
REPORT = THIS / "ashwake-content-import-report.json"
AUDIO_ROOT = THIS / "source_audio"

report = {
    "schema_version": 1,
    "status": "STARTED",
    "assets": [],
    "errors": [],
    "vfx_design": {
        "purpose": "Reliquary aura communicates current gameplay read: ember breathing in Reading, gold alignment in SafeWindow, red pressure in Hostile, blue cooling in Success.",
        "shape_language": "Concentric ember orbit, vertical ash lift, ring-alignment pulse, hostile compression flare.",
        "spawn_behavior": "CPU sprite system with state-driven user parameters consumed by runtime component; low bounded density for calibration scene.",
        "motion": "Slow lift and orbit for Reading; synchronized ring pulse for SafeWindow; sharp strobing/pressure for Hostile; low drift for Cooled.",
        "energy": "StateColor, State, SpawnRate, Energy, and Pulse driven by AFoundryRelicActor.",
        "timing": "2s read, 3s safe window, 1.5s hostile loop; instant attune success/failure feedback.",
        "color": "Reading ember umber, SafeWindow gold, Hostile hot red, Success cooled cyan.",
        "dissipation": "Small upward fade, no screen-filling bursts.",
        "lighting_interaction": "Point light mirrors Niagara state for gameplay-readable glow.",
        "screen_space_density": "Three relics remain readable at third-person camera distance without hiding HUD or player.",
        "performance_budget": "CPU Niagara, <=3 active systems, <=100 nominal spawned particles per relic per second."
    },
    "audio_design": {
        "architecture": "Imported generated SoundWave cues, played spatially at reliquary location on state transition and interaction outcome.",
        "ambient_world_sound": "Deferred to later slice pass; not claimed yet.",
        "idle_state": "Visual pulse only for now, avoids repetitive audio fatigue.",
        "state_transition_feedback": "SafeWindow and Hostile cues play once per transition.",
        "danger_feedback": "Hostile cue plus red light/VFX state.",
        "success_feedback": "AttuneSuccess cue on accepted interaction.",
        "player_action_feedback": "AttuneReject cue on unsafe interaction."
    },
    "animation_design": {
        "idle": "emberveil-canonical11vt_float_Emberveil_root",
        "state_change": "emberveil-canonical11vt_rotate_brass_band",
        "hostile": "emberveil-canonical11vt_pulse_ember_core",
        "success_signature": "emberveil-canonical11vt_rotate_filigree_arc"
    }
}

def add_asset(kind, path, status="PASS"):
    report["assets"].append({"kind": kind, "path": path, "status": status})

try:
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    asset_lib = unreal.EditorAssetLibrary
    if not asset_lib.does_directory_exist("/Game/Calibration/VFX"):
        asset_lib.make_directory("/Game/Calibration/VFX")
    if not asset_lib.does_directory_exist("/Game/Calibration/Audio"):
        asset_lib.make_directory("/Game/Calibration/Audio")

    emitter_factory = unreal.NiagaraEmitterFactoryNew()
    emitter = tools.create_asset("NE_Emberveil_Attune", "/Game/Calibration/VFX", unreal.NiagaraEmitter, emitter_factory)
    add_asset("NiagaraEmitter", emitter.get_path_name() if emitter else None, "PASS" if emitter else "FAIL")

    system_factory = unreal.NiagaraSystemFactoryNew()
    system = tools.create_asset("NS_Emberveil_Attune", "/Game/Calibration/VFX", unreal.NiagaraSystem, system_factory)
    add_asset("NiagaraSystem", system.get_path_name() if system else None, "PASS" if system else "FAIL")

    for asset in [emitter, system]:
        if asset:
            asset_lib.save_loaded_asset(asset)

    audio_files = [
        "S_Ashwake_SafeWindow.wav",
        "S_Ashwake_Hostile.wav",
        "S_Ashwake_AttuneSuccess.wav",
        "S_Ashwake_AttuneReject.wav",
    ]
    tasks = []
    for filename in audio_files:
        task = unreal.AssetImportTask()
        task.filename = str(AUDIO_ROOT / filename)
        task.destination_path = "/Game/Calibration/Audio"
        task.destination_name = Path(filename).stem
        task.automated = True
        task.replace_existing = True
        task.save = True
        tasks.append(task)
    tools.import_asset_tasks(tasks)
    for task in tasks:
        paths = list(getattr(task, "imported_object_paths", []) or [])
        status = "PASS" if paths else "FAIL"
        if not paths:
            report["errors"].extend([str(e) for e in list(getattr(task, "errors", []) or [])])
        for path in paths or [f"/Game/Calibration/Audio/{task.destination_name}.{task.destination_name}"]:
            add_asset("SoundWave", path, status)
            loaded = unreal.load_asset(path)
            if loaded:
                asset_lib.save_loaded_asset(loaded)

    expected = [
        "/Game/Calibration/VFX/NS_Emberveil_Attune.NS_Emberveil_Attune",
        "/Game/Calibration/Audio/S_Ashwake_SafeWindow.S_Ashwake_SafeWindow",
        "/Game/Calibration/Audio/S_Ashwake_Hostile.S_Ashwake_Hostile",
        "/Game/Calibration/Audio/S_Ashwake_AttuneSuccess.S_Ashwake_AttuneSuccess",
        "/Game/Calibration/Audio/S_Ashwake_AttuneReject.S_Ashwake_AttuneReject",
    ]
    missing = [path for path in expected if not unreal.load_asset(path)]
    report["runtime_expected_assets"] = expected
    report["missing_after_create"] = missing
    report["status"] = "PASS" if not missing and not any(a.get("status") == "FAIL" for a in report["assets"]) else "FAIL"
except Exception as exc:
    report["status"] = "FAIL"
    report["errors"].append(f"{type(exc).__name__}: {exc}")

REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report))
