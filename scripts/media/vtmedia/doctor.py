from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any
from .common import ARTIFACT_ROOT, command_summary, ensure_dir, run, run_shell, system_base, which, write_json

TOOLS = {
    "git": ["git", "--version"],
    "node": ["node", "--version"],
    "npm": ["npm", "--version"],
    "python": ["python", "--version"],
    "ffmpeg": ["ffmpeg", "-version"],
    "ffprobe": ["ffprobe", "-version"],
    "magick": ["magick", "-version"],
    "identify": ["magick", "identify", "-version"],
    "compare": ["magick", "compare", "-version"],
    "composite": ["magick", "composite", "-version"],
    "blender": ["blender", "--version"],
    "inkscape": ["inkscape", "--version"],
    "krita": ["krita", "--version"],
    "gimp": ["gimp", "--version"],
    "kdenlive": ["kdenlive", "--version"],
    "audacity": ["audacity", "--version"],
    "nvidia-smi": ["nvidia-smi"],
    "nvcc": ["nvcc", "--version"],
}

CAPABILITY_TOOLS = {
    "raster_processing": ["magick", "ffmpeg", "python"],
    "raster_painting": ["krita", "gimp"],
    "vector_authoring": ["inkscape"],
    "three_d_modeling": ["blender"],
    "three_d_rendering": ["blender"],
    "shader_authoring": ["blender", "node", "python"],
    "image_generation": ["comfyui", "9router_image"],
    "image_editing": ["comfyui", "gimp", "krita", "magick"],
    "image_upscaling": ["comfyui", "magick"],
    "background_removal": ["comfyui"],
    "video_generation": ["comfyui", "9router_video"],
    "video_editing": ["kdenlive", "ffmpeg"],
    "video_encoding": ["ffmpeg"],
    "video_upscaling": ["ffmpeg", "comfyui"],
    "audio_editing": ["audacity", "ffmpeg"],
    "speech_to_text": ["whisper", "ffmpeg"],
    "text_to_speech": ["piper", "9router_tts"],
    "browser_rendering": ["claude_preview", "node"],
    "browser_capture": ["claude_preview", "node"],
    "visual_diff": ["magick", "ffmpeg", "python"],
    "web_research": ["claude_websearch", "claude_webfetch"],
    "asset_conversion": ["ffmpeg", "magick", "inkscape", "blender"],
    "font_inspection": ["inkscape", "python"],
    "color_management": ["magick", "ffmpeg", "blender"],
}


def parse_first_line(text: str) -> str:
    return next((line.strip() for line in text.splitlines() if line.strip()), "")


def detect_tool(name: str, argv: list[str]) -> dict[str, Any]:
    exe = which(argv[0])
    if not exe:
        return {"tool": name, "availability": "missing", "path": None, "version": None, "health": "MISSING"}
    result = run(argv, timeout=20)
    version = parse_first_line((result.get("stdout") or result.get("stderr") or ""))
    health = "PASS" if result.get("returncode") == 0 else "FAILED"
    return {"tool": name, "availability": "available" if health == "PASS" else "failed", "path": exe, "version": version, "health": health, "check": command_summary(result, 800)}


def detect_gpu() -> dict[str, Any]:
    if not which("nvidia-smi"):
        return {"availability": "missing", "health": "MISSING"}
    query = run(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader,nounits"], timeout=20)
    full = run(["nvidia-smi"], timeout=20)
    gpu = {"availability": "available", "health": "PASS", "query": command_summary(query), "smi": command_summary(full, 1600)}
    if query.get("stdout"):
        parts = [p.strip() for p in query["stdout"].splitlines()[0].split(",")]
        if len(parts) >= 3:
            gpu.update({"name": parts[0], "vram_mb": int(parts[1]) if parts[1].isdigit() else parts[1], "driver": parts[2]})
    return gpu


def detect_system() -> dict[str, Any]:
    out = system_base()
    ps = run_shell('powershell -NoProfile -Command "Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors | ConvertTo-Json -Compress; Get-CimInstance Win32_ComputerSystem | Select-Object TotalPhysicalMemory | ConvertTo-Json -Compress; Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber | ConvertTo-Json -Compress; Get-PSDrive -PSProvider FileSystem | Select-Object Name,Free,Used | ConvertTo-Json -Compress"', timeout=60)
    out["powershell_inventory"] = command_summary(ps, 6000)
    return out


def nine_router() -> dict[str, Any]:
    import urllib.request
    base = os.environ.get("NINEROUTER_URL") or "http://127.0.0.1:20128"
    base = base.removesuffix("/v1")
    result: dict[str, Any] = {"base": base, "health": "UNKNOWN", "categories": {}}
    for path in ["/api/health", "/v1/models", "/v1/models/image", "/v1/models/tts", "/v1/models/embedding", "/v1/models/web", "/v1/models/stt", "/v1/models/image-to-text"]:
        try:
            with urllib.request.urlopen(base + path, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8", "replace"))
            if path == "/api/health":
                result["health"] = "PASS" if data.get("ok") else "FAILED"
            else:
                result["categories"][path] = len(data.get("data", []))
        except Exception as exc:
            result["categories"][path] = "ERROR " + type(exc).__name__
    return result


def build_registry(report: dict[str, Any]) -> dict[str, Any]:
    tools = report["tools"]
    capabilities = {}
    for cap, candidates in CAPABILITY_TOOLS.items():
        providers = []
        for cand in candidates:
            if cand in tools:
                t = tools[cand]
                if t.get("availability") == "available":
                    providers.append({"provider": cand, "executable": t.get("path"), "version": t.get("version"), "availability": "available"})
            elif cand == "claude_preview":
                providers.append({"provider": cand, "automation_method": "Claude Browser preview tools", "availability": "available_in_session"})
            elif cand in ("claude_websearch", "claude_webfetch"):
                providers.append({"provider": cand, "automation_method": "Claude web tools", "availability": "available_in_session"})
            elif cand.startswith("9router"):
                cats = report.get("9router", {}).get("categories", {})
                key = {"9router_image":"/v1/models/image","9router_tts":"/v1/models/tts","9router_video":"/v1/models/video"}.get(cand)
                count = cats.get(key, 0) if key else 0
                providers.append({"provider": cand, "automation_method": "9Router API", "availability": "available" if isinstance(count,int) and count>0 else "missing_or_untested", "cost_policy": "optional_not_default"})
            elif cand in ("comfyui", "whisper", "piper"):
                providers.append({"provider": cand, "availability": "not_installed", "cost_policy": "local_free_required"})
        health = "PASS" if any(p.get("availability") in ("available","available_in_session") for p in providers) else "MISSING"
        capabilities[cap] = {"availability": "available" if health == "PASS" else "missing", "providers": providers, "cost_policy": "free_local_default", "license": "varies_by_provider", "health": health}
    return {"schema_version": 1, "registry_id": "11vt-creative-toolchain", "updated_at_note": "generated by 11vt_media doctor", "capabilities": capabilities, "tools": tools, "gpu": report.get("gpu"), "9router": report.get("9router"), "policies": {"paid_generation_default": "forbidden", "public_services_default": "localhost_only", "license_manifest_required": True, "provenance_required": True}}


def doctor_json(check_9router: bool = True, out_dir: Path | None = None) -> dict[str, Any]:
    report = {"system": detect_system(), "tools": {}, "gpu": detect_gpu()}
    for name, argv in TOOLS.items():
        report["tools"][name] = detect_tool(name, argv)
    if check_9router:
        report["9router"] = nine_router()
    report["registry"] = build_registry(report)
    if out_dir:
        ensure_dir(out_dir)
        write_json(out_dir / "environment-report.json", report)
        write_json(out_dir / "capability-registry.json", report["registry"])
    return report
