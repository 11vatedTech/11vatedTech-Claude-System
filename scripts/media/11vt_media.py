#!/usr/bin/env python3
from __future__ import annotations

import argparse, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from vtmedia.common import ARTIFACT_ROOT, CONFIG_PATH, ensure_dir, file_record, write_json
from vtmedia.doctor import doctor_json
from vtmedia import ffmpeg_tools, image_tools, vector_tools, blender_bridge
from vtmedia.provenance import manifest, write_manifest


def cmd_doctor(args):
    out = Path(args.out) if args.out else ARTIFACT_ROOT
    data = doctor_json(check_9router=not args.no_9router, out_dir=out)
    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        for name, tool in data["tools"].items(): print(f"{name:14} {tool.get('health')} {tool.get('version') or ''}")
        print("gpu", data.get("gpu", {}).get("health"), data.get("gpu", {}).get("name"))
    return 0


def cmd_registry(args):
    out = Path(args.out) if args.out else CONFIG_PATH
    data = doctor_json(check_9router=True, out_dir=ARTIFACT_ROOT)["registry"]
    write_json(out, data)
    print(out)
    return 0


def cmd_blender_test(args):
    out = Path(args.out) if args.out else ARTIFACT_ROOT / "blender"
    result = blender_bridge.render_test(out, quality=args.quality)
    write_json(out / "blender-test-result.json", result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("health") == "PASS" else 1


def cmd_vector_test(args):
    out = Path(args.out) if args.out else ARTIFACT_ROOT / "vector"
    ensure_dir(out)
    svg = out / "source.svg"
    png = out / "rasterized.png"
    info = vector_tools.make_svg(svg)
    rast = vector_tools.rasterize(svg, png)
    write_json(out / "vector-validation.json", {"svg": info, "rasterize": rast, "outputs": [file_record(svg), file_record(png)]})
    print(json.dumps({"svg": info, "rasterize": rast}, indent=2))
    return 0 if svg.exists() and png.exists() else 1


def cmd_image_test(args):
    out = Path(args.out) if args.out else ARTIFACT_ROOT / "image"
    ensure_dir(out)
    generated = out / "generated.png"
    alpha = out / "alpha.png"
    upscale = out / "upscale.png"
    diff = out / "diff.png"
    r1 = image_tools.make_gradient(generated, 1024, 768)
    r2 = image_tools.alpha_test(alpha)
    r3 = ffmpeg_tools.resize_image(generated, upscale, 2048)
    cmp = image_tools.compare_images(generated, upscale, diff)
    data = {"generated": image_tools.inspect_image(generated), "alpha": image_tools.inspect_image(alpha), "upscale": image_tools.inspect_image(upscale), "commands": [r1, r2, r3], "compare": cmp}
    write_json(out / "image-validation.json", data)
    write_manifest(out / "provenance.json", manifest("image-test", "generate_refine_upscale_alpha", [generated, alpha, upscale, diff if diff.exists() else upscale]))
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0 if generated.exists() and alpha.exists() and upscale.exists() else 1


def cmd_video_test(args):
    out = Path(args.out) if args.out else ARTIFACT_ROOT / "video"
    ensure_dir(out)
    source = out / "generated.mp4"
    final = out / "final.mp4"
    thumb = out / "thumbnail.png"
    sheet = out / "contact-sheet.png"
    ffprobe = out / "ffprobe.json"
    r1 = ffmpeg_tools.make_test_video(source)
    r2 = ffmpeg_tools.transcode(source, final)
    r3 = ffmpeg_tools.thumbnail(final, thumb)
    r4 = ffmpeg_tools.contact_sheet(final, sheet)
    meta = ffmpeg_tools.probe(final, ffprobe)
    data = {"commands": [r1,r2,r3,r4], "probe": meta, "outputs": [file_record(p) for p in [source, final, thumb, sheet, ffprobe]]}
    write_json(out / "video-validation.json", data)
    write_manifest(out / "provenance.json", manifest("video-test", "generate_encode_inspect", [source, final, thumb, sheet, ffprobe]))
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0 if final.exists() and thumb.exists() and sheet.exists() else 1


def cmd_audio_test(args):
    out = Path(args.out) if args.out else ARTIFACT_ROOT / "audio"
    ensure_dir(out)
    source = out / "source.wav"
    norm = out / "normalized.wav"
    wave = out / "waveform.png"
    transcript = out / "transcript.txt"
    tts = out / "tts.wav"
    r1 = ffmpeg_tools.make_test_audio(source)
    r2 = ffmpeg_tools.normalize_audio(source, norm)
    r3 = ffmpeg_tools.waveform(norm, wave)
    # Offline deterministic baseline: synth tone has no speech; transcript records STT gap until local model installed.
    transcript.write_text("STT baseline: no speech sample model installed; deterministic audio pipeline verified.\n", encoding="utf-8")
    tts.write_bytes(source.read_bytes() if source.exists() else b"")
    data = {"commands": [r1,r2,r3], "outputs": [file_record(p) for p in [source, norm, wave, transcript, tts]], "stt": "degraded_no_local_model_yet", "tts": "degraded_tone_placeholder_no_voice_model_yet"}
    write_json(out / "audio-validation.json", data)
    write_manifest(out / "provenance.json", manifest("audio-test", "process_audio_waveform", [source,norm,wave,transcript,tts]))
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0 if source.exists() and norm.exists() and wave.exists() else 1


def cmd_highres(args):
    out = Path(args.out) if args.out else ARTIFACT_ROOT / "highres"
    ensure_dir(out)
    master = out / "master-4k.png"
    r = ffmpeg_tools.highres_test(master)
    data = {"command": r, "output": image_tools.inspect_image(master), "note": "Resolution delivery test only; resolution is not fidelity."}
    write_json(out / "highres-validation.json", data)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0 if master.exists() else 1


def cmd_suite(args):
    failures=[]
    for name, fn in [("image", cmd_image_test),("vector", cmd_vector_test),("video", cmd_video_test),("audio", cmd_audio_test),("highres", cmd_highres)]:
        ns=argparse.Namespace(out=str(ARTIFACT_ROOT / name), quality="preview")
        code=fn(ns)
        if code: failures.append(name)
    if blender_bridge.available():
        code=cmd_blender_test(argparse.Namespace(out=str(ARTIFACT_ROOT/"blender"), quality="preview"))
        if code: failures.append("blender")
    write_json(ARTIFACT_ROOT / "suite-result.json", {"failures": failures, "passed": not failures})
    return 1 if failures else 0


def main():
    p=argparse.ArgumentParser(prog="11vt-media")
    sub=p.add_subparsers(dest="cmd", required=True)
    d=sub.add_parser("doctor"); d.add_argument("--json", action="store_true"); d.add_argument("--no-9router", action="store_true"); d.add_argument("--out")
    r=sub.add_parser("registry"); r.add_argument("--out")
    b=sub.add_parser("blender-test"); b.add_argument("--out"); b.add_argument("--quality", default="preview")
    v=sub.add_parser("vector-test"); v.add_argument("--out")
    i=sub.add_parser("image-test"); i.add_argument("--out")
    vid=sub.add_parser("video-test"); vid.add_argument("--out")
    aud=sub.add_parser("audio-test"); aud.add_argument("--out")
    hi=sub.add_parser("highres-test"); hi.add_argument("--out")
    s=sub.add_parser("suite")
    args=p.parse_args()
    return {"doctor":cmd_doctor,"registry":cmd_registry,"blender-test":cmd_blender_test,"vector-test":cmd_vector_test,"image-test":cmd_image_test,"video-test":cmd_video_test,"audio-test":cmd_audio_test,"highres-test":cmd_highres,"suite":cmd_suite}[args.cmd](args)

if __name__ == "__main__":
    raise SystemExit(main())
