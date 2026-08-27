"""Score V4 runs: exact match against frozen labels, per-property accuracy,
balanced accuracy (mean per-class recall), trivial baselines, delta."""

import json
from pathlib import Path

DS = Path("artifacts/kapif/m002.1/visual-benchmark-v4-dataset.json")
RUNS = Path("artifacts/kapif/m002.1/runs-v4")
OUT = Path("artifacts/kapif/m002.1/visual-benchmark-v4-results.json")


def main():
    ds = json.loads(DS.read_text(encoding="utf-8"))
    samples = {s["sample_id"]: s for s in ds["samples"]}
    props = ds["scoreboard_properties"]
    n = len(samples)

    dist = {p: {} for p in props}
    for s in ds["samples"]:
        for p in props:
            v = s["labels"][p]
            dist[p][v] = dist[p].get(v, 0) + 1
    baselines = {}
    for p in props:
        top = max(dist[p], key=dist[p].get)
        baselines[p] = {"majority_class": top, "accuracy": round(dist[p][top] / n, 4)}

    report = {
        "kind": "visual-grounding-v4-results",
        "dataset_hash": ds["dataset_hash"],
        "label_hash": ds["label_hash"],
        "n_samples": n,
        "scoreboard_properties": props,
        "baselines": baselines,
        "models": {},
    }

    for run in sorted(RUNS.glob("results-*.json")):
        d = json.loads(run.read_text(encoding="utf-8"))
        model = d["model"]
        res = d["results"]
        valid = [v for v in res.values() if v.get("parsed")]
        ok_total = sum(1 for v in res.values() if v.get("status") == "OK")

        per_prop = {}
        for p in props:
            crc = {}
            scored = 0
            correct = 0
            for v in valid:
                truth = samples[v["sample_id"]]["labels"][p]
                pred = v["parsed"][p]
                if pred == "UNCERTAIN":
                    continue
                scored += 1
                crc.setdefault(truth, [0, 0])
                crc[truth][1] += 1
                if pred == truth:
                    correct += 1
                    crc[truth][0] += 1
            acc = round(correct / scored, 4) if scored else None
            recalls = [round(c / nn, 4) for c, nn in crc.values() if nn]
            bal = round(sum(recalls) / len(recalls), 4) if recalls else None
            per_prop[p] = {
                "accuracy": acc,
                "balanced_accuracy": bal,
                "n_scored": scored,
                "per_class": {k: {"correct": c, "n": nn} for k, (c, nn) in crc.items()},
            }

        accs = [v["accuracy"] for v in per_prop.values() if v["accuracy"] is not None]
        macro = round(sum(accs) / len(accs), 4) if accs else None
        bmacro = round(sum(baselines[p]["accuracy"] for p in props) / len(props), 4)
        lats = sorted(v["latency_s"] for v in res.values() if v.get("status") == "OK")
        info = {
            "valid_parsed": len(valid),
            "total_executed": ok_total,
            "schema_valid_rate": round(len(valid) / ok_total, 4) if ok_total else None,
            "per_property": per_prop,
            "macro_accuracy": macro,
            "macro_majority_baseline": bmacro,
            "delta_over_baseline": round(macro - bmacro, 4) if macro is not None else None,
            "latency_median_s": lats[len(lats) // 2] if lats else None,
            "latency_p95_s": lats[min(len(lats) - 1, int(len(lats) * 0.95))] if lats else None,
            "gpu_telemetry": next((r.get("gpu_telemetry") for r in res.values() if r.get("gpu_telemetry")), None),
        }
        report["models"][model] = info

    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("combined written:", OUT)
    for m, info in report["models"].items():
        print(f"{m}: valid={info['valid_parsed']} schema={info['schema_valid_rate']} "
              f"macro={info['macro_accuracy']} baseline={info['macro_majority_baseline']} "
              f"delta={info['delta_over_baseline']} lat_med={info['latency_median_s']}s")


if __name__ == "__main__":
    main()