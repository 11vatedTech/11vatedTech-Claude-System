"""BLOCKER 3: ACE-Step 1.5 music generation via REST API.
Uses /release_task (submit) + /query_result (poll) flow.
Generates 3 cues: atmospheric, action, menu/theme.
"""
import os, sys, json, time, subprocess, urllib.request, urllib.error, shutil

VENV = os.path.expanduser("~/.acestep-venv")
ACE_DIR = os.path.expanduser("~/ACE-Step-1.5")
PYTHON = os.path.join(VENV, "Scripts", "python.exe")
OUT = os.path.abspath(os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..",
    "artifacts", "visual", "audio"))
os.makedirs(OUT, exist_ok=True)
API = "http://127.0.0.1:8001"
REPORT = {"model": "ACE-Step 1.5 (2B turbo + 0.6B LM, MIT license)"}

def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(os.path.join(OUT, "acestep_run.log"), "a", encoding="utf-8") as f:
        f.write(line + "\n")

CUES = [
    {"name": "A_atmospheric",
     "prompt": "Dark fantasy atmospheric ambient, deep resonant drone, distant crystalline chimes, sub-bass pulse, ethereal choir pads, mysterious cavern reverb, slow tempo, instrumental, no vocals",
     "duration": 30, "bpm": 60, "key_scale": "D minor"},
    {"name": "B_action",
     "prompt": "Intense dark fantasy combat music, driving orchestral strings, heavy percussion hits, brass stabs, urgent rhythm, dramatic tension, epic battle energy, instrumental",
     "duration": 30, "bpm": 140, "key_scale": "E minor"},
    {"name": "C_menu",
     "prompt": "Elegant dark fantasy menu theme, haunting piano melody, soft strings, crystal bell motif, mysterious and inviting, game main menu mood, instrumental",
     "duration": 30, "bpm": 75, "key_scale": "A minor"},
]

def wait_for_api(timeout=600):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with urllib.request.urlopen(f"{API}/health", timeout=5) as r:
                if r.status == 200:
                    log("API is ready.")
                    return True
        except Exception:
            pass
        time.sleep(5)
    return False

def submit_cue(cue):
    payload = json.dumps({
        "prompt": cue["prompt"],
        "bpm": cue["bpm"],
        "key_scale": cue["key_scale"],
        "audio_duration": cue["duration"],
        "thinking": True,
        "task_type": "text2music",
        "inference_steps": 8,
        "guidance_scale": 7.0,
        "use_random_seed": False,
        "seed": 42,
        "vocal_language": "en",
    }).encode()
    req = urllib.request.Request(f"{API}/release_task", data=payload,
                                 headers={"Content-Type": "application/json"})
    log(f"Submitting cue {cue['name']}...")
    with urllib.request.urlopen(req, timeout=30) as r:
        result = json.loads(r.read())
    task_id = result.get("data", {}).get("task_id") or result.get("task_id")
    log(f"  Queued: task_id={task_id}")
    return task_id

def poll_result(task_id, timeout=600):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            payload = json.dumps({"task_id": task_id}).encode()
            req = urllib.request.Request(f"{API}/query_result", data=payload,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                result = json.loads(r.read())
            data = result.get("data", result)
            status = data.get("status", "")
            if status in ("completed", "success", "done"):
                return data
            if status in ("failed", "error"):
                log(f"  Job failed: {data.get('error','')}")
                return None
            log(f"  Polling: status={status} ({int(time.time()-t0)}s)")
        except Exception as e:
            log(f"  Poll error: {e}")
        time.sleep(10)
    log("  Timeout waiting for result.")
    return None

def main():
    log("Launching ACE-Step API server...")
    subprocess.run(["powershell.exe", "-Command",
                    "Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue | "
                    "ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }"],
                   capture_output=True)
    time.sleep(3)
    env = dict(os.environ)
    env["ACESTEP_CONFIG_PATH"] = "acestep-v15-turbo"
    env["ACESTEP_LM_MODEL_PATH"] = "acestep-5Hz-lm-0.6B"
    env["LANGUAGE"] = "en"
    env["ACESTEP_INIT_LLM"] = "true"
    proc = subprocess.Popen([PYTHON, "-m", "acestep.api_server",
                             "--host", "127.0.0.1", "--port", "8001",
                             "--lm-model-path", "acestep-5Hz-lm-0.6B",
                             "--init-llm"],
                            cwd=ACE_DIR, env=env,
                            stdout=open(os.path.join(OUT, "acestep_server.log"), "w"),
                            stderr=subprocess.STDOUT)
    log(f"Server PID={proc.pid}. Waiting for API...")
    if not wait_for_api(600):
        log("API did not come up. Check server log.")
        REPORT["status"] = "API_TIMEOUT"
        with open(os.path.join(OUT, "acestep_report.json"), "w") as f:
            json.dump(REPORT, f, indent=2)
        return
    results = {}
    for cue in CUES:
        try:
            task_id = submit_cue(cue)
            if not task_id:
                results[cue["name"]] = {"error": "no task_id"}
                continue
            t1 = time.time()
            data = poll_result(task_id, timeout=600)
            elapsed = time.time() - t1
            if data:
                results[cue["name"]] = {"elapsed_s": round(elapsed, 1), "status": "ok"}
                # Find audio output path
                audio_paths = data.get("audio_paths") or data.get("result", {}).get("audio_paths", [])
                if audio_paths:
                    src = audio_paths[0]
                    if os.path.exists(src):
                        dst = os.path.join(OUT, f"acestep_{cue['name']}.wav")
                        shutil.copy2(src, dst)
                        results[cue["name"]]["copied_to"] = dst
                        log(f"  Copied to {dst}")
                    else:
                        results[cue["name"]]["source_path"] = src
                        log(f"  Source: {src} (not found locally)")
                else:
                    log(f"  No audio_paths in response: {str(data)[:200]}")
            else:
                results[cue["name"]] = {"error": "timeout or failure"}
        except Exception as e:
            log(f"  FAILED: {e}")
            results[cue["name"]] = {"error": str(e)}
    REPORT["cues"] = results
    REPORT["status"] = "SUCCESS" if any("copied_to" in v for v in results.values()) else "PARTIAL"
    proc.terminate()
    with open(os.path.join(OUT, "acestep_report.json"), "w") as f:
        json.dump(REPORT, f, indent=2)
    log(f"Report: status={REPORT['status']}")

if __name__ == "__main__":
    main()
