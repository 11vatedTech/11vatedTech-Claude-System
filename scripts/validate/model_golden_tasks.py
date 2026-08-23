#!/usr/bin/env python3
"""
model_golden_tasks.py — evidence-based model capability evaluation through 9Router.

Runs controlled "golden tasks" through multiple available models (across
providers/families) and records, per model per task:
  model, provider, task, result, structural rubric score, failure mode, latency.

This feeds config/model-capability-registry.json so the capability router can
make role-aware model decisions instead of assuming the most famous model is
best for every role.

Usage:
  python scripts/validate/model_golden_tasks.py \
      [--models kr/glm-5-thinking,kr/deepseek-3.2-thinking,cx/gpt-5.6-luna-review] \
      [--tasks code,debug,repo,visual-critique,research] \
      [--out config/model-capability-registry.json] \
      [--max-tokens 800] [--limit 1]
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def get_auth():
    settings = json.loads((Path.home() / ".claude" / "settings.json").read_text(encoding="utf-8"))
    env = settings.get("env", {})
    base = env.get("ANTHROPIC_BASE_URL", "http://127.0.0.1:20128/v1").removesuffix("/v1")
    token = env.get("ANTHROPIC_AUTH_TOKEN", "")
    return base, token


def chat(base, token, model, messages, max_tokens=600, timeout=120):
    body = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "stream": False,
    }).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(base + "/v1/chat/completions", data=body, headers=headers)
    t0 = time.time()
    # retry with backoff on 429/5xx (router rate limits are common)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.loads(r.read().decode("utf-8", "replace"))
            latency = round(time.time() - t0, 2)
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return content, latency
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < 3:
                time.sleep(5 * (attempt + 1))
                continue
            raise
    raise RuntimeError("unreachable")


# ---- golden tasks: each has a prompt builder and a structural rubric ----

TASKS = {}


def task(name, instructions, rubric):
    TASKS[name] = {"instructions": instructions, "rubric": rubric}


def _check_rubric(text, rubric):
    scored = []
    for key, fn in rubric.items():
        ok = fn(text)
        scored.append({"criterion": key, "ok": ok})
    return scored, all(s["ok"] for s in scored)


task("code", (
    "Write a single Python function `interleave(a, b)` that returns a list "
    "interleaving elements of a and b (a[0], b[0], a[1], b[1], ...), stopping "
    "when either is exhausted. Include a docstring. Output only the code."
), {
    "function defined": lambda t: "def interleave" in t,
    "docstring present": lambda t: '"""' in t or "'''" in t,
    "no analysis prose": lambda t: len(t.splitlines()) <= 20,
})

task("debug", (
    "This function is buggy: it claims to return the sum of a list but "
    "sometimes returns wrong results. Find the bug and fix it, explaining in "
    "one sentence. def total(xs):\\n    s = 0\\n    for i in range(1, len(xs)):\\n"
    "        s += xs[i]\\n    return s"
), {
    "identifies off-by-one": lambda t: "range" in t and ("1," in t or "0" in t),
    "names the bug": lambda t: any(w in t.lower() for w in ["off-by-one", "off by one", "skips", "first element", "index 0"]),
    "fix shown": lambda t: "range(len(xs))" in t or "range(0" in t,
})

task("repo", (
    "In a Python project, a file `scripts/validate/system_regression.py` runs "
    "gates. Which file is most likely to hold the function that checks a GLB "
    "file's structural validity, and what is the single most reliable way to "
    "confirm it without reading every file? Answer in 2 sentences."
), {
    "names a search strategy": lambda t: any(w in t.lower() for w in ["grep", "search", "rg ", "ripgrep", "find", "read"]),
    "names candidate location": lambda t: any(w in t for w in ["blender", "glb", "validate", "asset", "media"]),
})

task("visual-critique", (
    "Critique this composition as a professional art director: a small bronze "
    "bell with a glowing ember core sits on a charcoal plinth, centered in a "
    "dark warm void; 420 additive ember particles rise from the core; a slow "
    "orbit camera with a cool rim light. List the THREE most specific, "
    "actionable weaknesses (not praise) and for each give one concrete fix."
), {
    "three weaknesses": lambda t: len([l for l in t.strip().splitlines() if l.strip()]) >= 3,
    "actionable fixes": lambda t: any(w in t.lower() for w in ["add", "increase", "reduce", "move", "change", "use", "lower", "raise"]),
    "not only praise": lambda t: any(w in t.lower() for w in ["weak", "flat", "lack", "issue", "could", "would"]),
})

task("frontend-design", (
    "Given a dense operations tool for returning analysts, propose three materially different visual directions. "
    "For the selected direction state the hierarchy, typography, density, responsive transformation, and one anti-reference. "
    "Do not default to gradients, glass cards, or generic dashboard grids.",
), {
    "three directions": lambda t: sum(1 for marker in ["direction", "option", "concept"] if marker in t.lower()) >= 2,
    "responsive reasoning": lambda t: any(w in t.lower() for w in ["mobile", "responsive", "breakpoint", "narrow"]),
    "anti-reference": lambda t: any(w in t.lower() for w in ["avoid", "anti", "generic", "glass", "gradient"]),
})

task("ux-critique", (
    "A checkout form passes automated accessibility scans but users abandon it on mobile. "
    "Give a causal diagnosis across information architecture, interaction, content, responsive behavior, and manual evidence. "
    "Name the first two tests you would run.",
), {
    "multiple ux axes": lambda t: sum(1 for w in ["hierarchy", "interaction", "content", "responsive", "mobile", "keyboard"] if w in t.lower()) >= 3,
    "causal diagnosis": lambda t: any(w in t.lower() for w in ["because", "cause", "likely", "due to"]),
    "tests named": lambda t: any(w in t.lower() for w in ["test", "observe", "interview", "playtest"]),
})

task("game-design", (
    "Design a one-room game mechanic for a player who must decide when to expose a fragile light source. "
    "State the player fantasy, verbs, core loop, feedback, challenge escalation, failure/recovery, and what a playtest would falsify."
), {
    "player fantasy": lambda t: "fantasy" in t.lower(),
    "core loop": lambda t: "loop" in t.lower(),
    "playtest falsifier": lambda t: any(w in t.lower() for w in ["playtest", "falsify", "observe", "if players"]),
})

task("art-direction", (
    "As an art director, critique a technically valid dark prop render. Explain how silhouette, value, material response, "
    "lighting motivation, and negative space affect readability. Give one controlled study before production."
), {
    "causal visual vocabulary": lambda t: sum(1 for w in ["silhouette", "value", "material", "lighting", "negative space"] if w in t.lower()) >= 4,
    "controlled study": lambda t: any(w in t.lower() for w in ["study", "render", "key light", "grayscale", "neutral"]),
    "actionable repair": lambda t: any(w in t.lower() for w in ["add", "reduce", "separate", "raise", "lower", "reframe"]),
})

task("research", (
    "Synthesize what is known about automated foot-slide detection in game "
    "animation QA. Give: (1) the mechanical method, (2) one alternative "
    "approach, (3) a confidence statement distinguishing fact from inference. "
    "Keep under 150 words."
), {
    "mechanical method": lambda t: any(w in t.lower() for w in ["velocity", "speed", "position", "bone", "contact", "slide"]),
    "alternative given": lambda t: any(w in t.lower() for w in ["or", "alternative", "another", "machine", "learn", "ik", "heuristic"]),
    "confidence stated": lambda t: any(w in t.lower() for w in ["confidence", "fact", "inference", "assum", "likely", "uncertain"]),
})


def run(args):
    base, token = get_auth()
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    names = [t.strip() for t in args.tasks.split(",") if t.strip()]
    tasks = {n: TASKS[n] for n in names if n in TASKS}
    if len(tasks) != len(names):
        unknown = [n for n in names if n not in TASKS]
        print(f"unknown tasks: {unknown}", file=sys.stderr)
        return 1

    registry_path = Path(args.out)
    registry = {}
    if registry_path.exists():
        registry = json.loads(registry_path.read_text(encoding="utf-8"))

    results = []
    for model in models:
        provider = model.split("/")[0] if "/" in model else "default"
        for name, spec in tasks.items():
            try:
                content, latency = chat(base, token, model,
                                        [{"role": "user", "content": spec["instructions"]}],
                                        max_tokens=args.max_tokens)
            except urllib.error.HTTPError as e:
                results.append({
                    "model": model, "provider": provider, "task": name,
                    "passed": False, "rubric": [], "latency_s": None,
                    "failure_mode": [f"http_{e.code}"],
                    "output_excerpt": "",
                })
                print(f"{model} | {name} | FAIL | http {e.code} (recorded, continuing)")
                continue
            scored, passed = _check_rubric(content, spec["rubric"])
            rec = {
                "model": model,
                "provider": provider,
                "task": name,
                "passed": passed,
                "rubric": scored,
                "latency_s": latency,
                "failure_mode": None if passed else [s["criterion"] for s in scored if not s["ok"]],
                "output_excerpt": content[:400],
            }
            results.append(rec)
            print(f"{model} | {name} | {'PASS' if passed else 'FAIL'} | {latency}s")

    # fold into registry: per model, per task, keep latest
    for rec in results:
        registry.setdefault(rec["model"], {})[rec["task"]] = {
            "passed": rec["passed"],
            "rubric": rec["rubric"],
            "latency_s": rec["latency_s"],
            "failure_mode": rec["failure_mode"],
            "run": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
    registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    print(f"\nregistry written: {registry_path} ({len(registry)} models)")
    return 0 if all(r["passed"] for r in results) else 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="kr/glm-5-thinking,kr/deepseek-3.2-thinking")
    ap.add_argument("--tasks", default="code,debug,repo,visual-critique,research")
    ap.add_argument("--out", default=str(REPO / "config" / "model-capability-registry.json"))
    ap.add_argument("--max-tokens", type=int, default=800)
    args = ap.parse_args()
    sys.exit(run(args))


if __name__ == "__main__":
    main()
