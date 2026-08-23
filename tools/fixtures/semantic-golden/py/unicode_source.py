from __future__ import annotations

# Unicode position trap: emoji 🚀, non-BMP astral 𝔘𝔫𝔦𝔠𝔬𝔡𝔢, and accented
# café characters sit on the same lines as the queried symbols, so UTF-16
# column math must be exact.


def measure_café(record: str) -> int:
    return len(record)


def value_check(value: float) -> bool:  # 𝔘𝔫𝔦𝔠𝔬𝔡𝔢 🚀 before symbol
    return value > 0.0