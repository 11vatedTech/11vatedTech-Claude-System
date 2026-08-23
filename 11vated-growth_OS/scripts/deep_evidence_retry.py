#!/usr/bin/env python3
"""Wait for GitHub rate limit reset, then run the portfolio deep evidence pass."""
import subprocess
import sys
import time
import httpx
import datetime


def check_rate_limit() -> tuple[int, int]:
    """Return (remaining, seconds_until_reset)."""
    try:
        resp = httpx.get(
            "https://api.github.com/rate_limit",
            headers={"Accept": "application/vnd.github+json", "User-Agent": "GrowthOS/0.1"},
            timeout=10,
        )
        data = resp.json()
        core = data["resources"]["core"]
        remaining = core["remaining"]
        reset_ts = core["reset"]
        now_ts = int(time.time())
        seconds_left = max(0, reset_ts - now_ts)
        return remaining, seconds_left
    except Exception:
        return 0, 60


def main() -> None:
    remaining, seconds_left = check_rate_limit()
    print(f"[{datetime.datetime.now():%H:%M:%S}] GitHub rate limit: {remaining}/60 remaining, resets in {seconds_left // 60}m {seconds_left % 60}s")

    if remaining < 10:
        wait_time = seconds_left + 10  # add 10s buffer
        print(f"[{datetime.datetime.now():%H:%M:%S}] Waiting {wait_time // 60}m {wait_time % 60}s for rate limit reset...")
        time.sleep(wait_time)
        remaining, _ = check_rate_limit()
        print(f"[{datetime.datetime.now():%H:%M:%S}] Rate limit after wait: {remaining}/60")

    print(f"[{datetime.datetime.now():%H:%M:%S}] Running portfolio deep evidence pass...")
    result = subprocess.run(
        [sys.executable, "-m", "growthos.cli.main", "portfolio-deep-evidence", "--run"],
        capture_output=True,
        text=True,
        timeout=300,
    )
    print("STDOUT:")
    print(result.stdout)
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    print(f"Exit code: {result.returncode}")


if __name__ == "__main__":
    main()
