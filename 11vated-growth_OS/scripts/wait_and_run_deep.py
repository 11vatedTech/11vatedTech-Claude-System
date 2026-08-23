#!/usr/bin/env python3
"""Wait for GitHub rate limit reset, then run portfolio deep evidence pass."""
import subprocess
import sys
import time
import httpx
import datetime


def check_rate_limit():
    try:
        resp = httpx.get(
            "https://api.github.com/rate_limit",
            headers={"Accept": "application/vnd.github+json", "User-Agent": "GrowthOS/0.1"},
            timeout=10,
        )
        core = resp.json()["resources"]["core"]
        now = int(time.time())
        return core["remaining"], max(0, core["reset"] - now)
    except Exception:
        return 0, 60


def main():
    remaining, secs = check_rate_limit()
    print(f"[{datetime.datetime.now():%H:%M:%S}] Rate limit: {remaining}/60, reset in {secs//60}m{secs%60}s", flush=True)

    if remaining < 15:
        wait = secs + 10
        print(f"[{datetime.datetime.now():%H:%M:%S}] Sleeping {wait//60}m{wait%60}s...", flush=True)
        time.sleep(wait)
        remaining, _ = check_rate_limit()
        print(f"[{datetime.datetime.now():%H:%M:%S}] After wait: {remaining}/60", flush=True)

    print(f"[{datetime.datetime.now():%H:%M:%S}] Running deep evidence pass...", flush=True)
    result = subprocess.run(
        [sys.executable, "-m", "growthos.cli.main", "portfolio-deep-evidence", "--run"],
        capture_output=True, text=True, timeout=300,
        cwd=r"C:\Users\11vat\OneDrive\Desktop\11vatedTech-Claude-System\11vated-growth_OS",
    )
    print(result.stdout, flush=True)
    if result.stderr:
        print("STDERR:", flush=True)
        print(result.stderr, flush=True)
    print(f"[{datetime.datetime.now():%H:%M:%S}] Exit: {result.returncode}", flush=True)


if __name__ == "__main__":
    main()
