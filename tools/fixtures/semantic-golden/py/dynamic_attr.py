from __future__ import annotations

# Deliberate UNKNOWN case: attributes and callables are resolved at runtime.
def invoke_by_name(obj: object, method: str, value: float) -> str:
    fn = getattr(obj, method)  # dynamic attribute access; static analysis cannot resolve
    return fn(value)


def invoke_dict(d: dict, key: str) -> int:
    return d[key]  # runtime key; no static target