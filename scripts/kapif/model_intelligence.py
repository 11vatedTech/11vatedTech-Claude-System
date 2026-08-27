#!/usr/bin/env python3
"""
KAPIF Model Intelligence Fabric
================================
Role-specific, evidence-based, adaptive multi-model routing via 9Router.

Roles benchmarked for M002.1:
  A. PROFESSIONAL_EXTRACTION
  B. INDEPENDENT_VERIFICATION
  C. EMBEDDING_RETRIEVAL
  D. VISUAL_GROUNDING
  E. PROFESSIONAL_VISUAL_CRITIQUE

Governing principle:
  9Router exists so the Foundry is not limited to one model's intelligence.
  Use the best available intelligence for each role.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
import urllib.request
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "kapif" / "kapif.db"
NINEROUTER_URL = os.environ.get("NINEROUTER_URL", "http://127.0.0.1:20128")
EVIDENCE_PATH = ROOT / "artifacts" / "kapif" / "model-intelligence"
EVIDENCE_PATH.mkdir(parents=True, exist_ok=True)

# ── Model States ──
class ModelState:
    DISCOVERED = "DISCOVERED"
    AVAILABLE = "AVAILABLE"
    PROBED = "PROBED"
    BENCHMARKED = "BENCHMARKED"
    ROLE_PREFERRED = "ROLE_PREFERRED"
    ROLE_BACKUP = "ROLE_BACKUP"
    DEGRADED = "DEGRADED"
    REJECTED = "REJECTED"
    STALE = "STALE"

# ── Roles ──
class Role:
    PROFESSIONAL_EXTRACTION = "PROFESSIONAL_EXTRACTION"
    INDEPENDENT_VERIFICATION = "INDEPENDENT_VERIFICATION"
    EMBEDDING_RETRIEVAL = "EMBEDDING_RETRIEVAL"
    VISUAL_GROUNDING = "VISUAL_GROUNDING"
    PROFESSIONAL_VISUAL_CRITIQUE = "PROFESSIONAL_VISUAL_CRITIQUE"

# ── Independence Levels ──
class Independence:
    SAME_MODEL_SAME_CONTEXT = "SAME_MODEL_SAME_CONTEXT"
    SAME_MODEL_ISOLATED_CONTEXT = "SAME_MODEL_ISOLATED_CONTEXT"
    SAME_FAMILY_DIFFERENT_MODEL = "SAME_FAMILY_DIFFERENT_MODEL"
    DIFFERENT_FAMILY_SAME_PROVIDER = "DIFFERENT_FAMILY_SAME_PROVIDER"
    DIFFERENT_FAMILY_DIFFERENT_PROVIDER = "DIFFERENT_FAMILY_DIFFERENT_PROVIDER"

# ── Access Classes ──
class AccessClass:
    FREE = "FREE"
    FREE_WITH_LIMITS = "FREE_WITH_LIMITS"
    LOCAL = "LOCAL"
    PAID = "PAID"
    UNKNOWN = "UNKNOWN"


def _init_db():
    """Initialize model intelligence tables."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS model_entities (
            model_id TEXT PRIMARY KEY,
            provider TEXT,
            provider_family TEXT,
            model_family TEXT,
            version TEXT,
            discovered_at TEXT,
            last_seen TEXT,
            modalities TEXT DEFAULT '[]',
            context_length INTEGER,
            structured_output INTEGER DEFAULT 0,
            vision_support INTEGER DEFAULT 0,
            embedding_support INTEGER DEFAULT 0,
            local_or_remote TEXT DEFAULT 'remote',
            cost_class TEXT DEFAULT 'UNKNOWN',
            free_status TEXT DEFAULT 'UNKNOWN',
            availability TEXT DEFAULT 'UNKNOWN',
            state TEXT DEFAULT 'DISCOVERED'
        );
        CREATE TABLE IF NOT EXISTS role_benchmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            model_id TEXT NOT NULL,
            benchmark_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            metrics_json TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY (model_id) REFERENCES model_entities(model_id)
        );
        CREATE TABLE IF NOT EXISTS role_preferences (
            role TEXT PRIMARY KEY,
            preferred_model TEXT,
            backup_model TEXT,
            benchmark_id TEXT,
            selection_reason TEXT,
            confidence TEXT,
            last_benchmarked TEXT,
            known_failure_modes TEXT DEFAULT '[]',
            sample_n INTEGER DEFAULT 0,
            preference_confidence TEXT DEFAULT 'LOW'
        );
        CREATE TABLE IF NOT EXISTS routing_decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mission_id TEXT,
            role TEXT NOT NULL,
            candidate_models TEXT NOT NULL,
            selected_model TEXT NOT NULL,
            backup_model TEXT,
            selection_reason TEXT,
            confidence TEXT,
            timestamp TEXT NOT NULL
        );
    """)
    conn.close()

_init_db()


def discover_available_models() -> list[dict]:
    """Probe 9Router and return all currently available models with metadata."""
    try:
        req = urllib.request.Request(f"{NINEROUTER_URL}/v1/models")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        return [{"error": str(e)}]

    models = data.get("data", [])
    result = []
    for m in models:
        mid = m.get("id", "")
        entity = {
            "model_id": mid,
            "provider": mid.split("/")[0] if "/" in mid else "unknown",
            "provider_family": _infer_provider_family(mid),
            "model_family": _infer_model_family(mid),
            "modalities": _infer_modalities(mid),
            "vision_support": _infer_vision(mid),
            "embedding_support": 1 if "embed" in mid.lower() else 0,
            "cost_class": _infer_cost(mid),
            "free_status": "FREE" if (":free" in mid or mid.startswith("kr/")) else "UNKNOWN",
            "state": ModelState.AVAILABLE,
        }
        result.append(entity)

        # Persist to DB
        _upsert_model(entity)

    return result


def _infer_provider_family(mid: str) -> str:
    if mid.startswith("kr/"):
        return "kr"
    if mid.startswith("openrouter/"):
        parts = mid.split("/")
        return f"openrouter/{parts[1]}" if len(parts) > 1 else "openrouter"
    if mid.startswith("gh/"):
        return "github-copilot"
    if mid in ("11", "claude-11"):
        return "anthropic-root"
    return "unknown"


def _infer_model_family(mid: str) -> str:
    ml = mid.lower()
    if "claude" in ml:
        return "claude"
    if "gpt" in ml or "o1" in ml or "o3" in ml:
        return "openai"
    if "deepseek" in ml:
        return "deepseek"
    if "minimax" in ml:
        return "minimax"
    if "glm" in ml:
        return "glm"
    if "qwen" in ml:
        return "qwen"
    if "gemini" in ml or "gemma" in ml:
        return "google"
    if "nemotron" in ml:
        return "nvidia"
    if "llama" in ml:
        return "meta"
    if "mistral" in ml or "mixtral" in ml:
        return "mistral"
    if "laguna" in ml or "poolside" in ml:
        return "poolside"
    if "ling" in ml:
        return "inclusionai"
    return "unknown"


def _infer_modalities(mid: str) -> list[str]:
    modalities = ["text"]
    if _infer_vision(mid):
        modalities.append("vision")
    if "embed" in mid.lower():
        modalities.append("embedding")
    return modalities


def _infer_vision(mid: str) -> int:
    ml = mid.lower()
    # Models known to support vision
    vision_models = ["claude-sonnet-4", "claude-haiku-4.5", "gpt-4o", "gemini", "gemma-4", "nemotron-3-nano-omni"]
    for v in vision_models:
        if v in ml:
            return 1
    # 11 and claude-11 support vision (root model)
    if mid in ("11", "claude-11"):
        return 1
    return 0


def _infer_cost(mid: str) -> str:
    if ":free" in mid or mid.startswith("kr/"):
        return AccessClass.FREE
    if mid.startswith("gh/"):
        return AccessClass.PAID  # requires Copilot subscription
    return AccessClass.UNKNOWN


def _upsert_model(entity: dict):
    """Insert or update a model entity."""
    conn = sqlite3.connect(str(DB_PATH))
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    try:
        conn.execute("""
            INSERT INTO model_entities 
            (model_id, provider, provider_family, model_family, modalities,
             vision_support, embedding_support, cost_class, free_status, 
             availability, state, discovered_at, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(model_id) DO UPDATE SET
                last_seen = excluded.last_seen,
                availability = excluded.availability,
                state = CASE 
                    WHEN model_entities.state IN ('ROLE_PREFERRED', 'ROLE_BACKUP') 
                    THEN model_entities.state 
                    ELSE excluded.state 
                END
        """, (
            entity["model_id"], entity.get("provider", ""),
            entity.get("provider_family", ""), entity.get("model_family", ""),
            json.dumps(entity.get("modalities", [])),
            entity.get("vision_support", 0), entity.get("embedding_support", 0),
            entity.get("cost_class", "UNKNOWN"), entity.get("free_status", "UNKNOWN"),
            "AVAILABLE", entity.get("state", ModelState.AVAILABLE),
            now, now
        ))
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


def chat_completion(model: str, messages: list[dict], max_tokens: int = 2000,
                    temperature: float = 0.0, timeout: int = 60) -> dict:
    """Call 9Router chat completion endpoint. Handles both streaming and non-streaming."""
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{NINEROUTER_URL}/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        start = time.time()
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        latency = time.time() - start

        # Try non-streaming first
        try:
            result = json.loads(raw)
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = result.get("usage", {})
            return {
                "success": True,
                "content": content,
                "model_used": result.get("model", model),
                "latency": round(latency, 3),
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            }
        except (json.JSONDecodeError, KeyError):
            pass

        # Handle SSE streaming format
        content_parts = []
        model_used = model
        for line in raw.split("\n"):
            line = line.strip()
            if not line.startswith("data: "):
                continue
            data_str = line[6:]
            if data_str == "[DONE]":
                break
            try:
                chunk = json.loads(data_str)
                m = chunk.get("model", "")
                if m:
                    model_used = m
                for choice in chunk.get("choices", []):
                    delta = choice.get("delta", {})
                    c = delta.get("content", "")
                    if c:
                        content_parts.append(c)
            except json.JSONDecodeError:
                continue

        content = "".join(content_parts)
        if content:
            return {
                "success": True,
                "content": content,
                "model_used": model_used,
                "latency": round(latency, 3),
                "prompt_tokens": 0,
                "completion_tokens": len(content.split()),
                "total_tokens": 0,
            }
        else:
            return {"success": False, "error": "Empty response", "model": model}
    except Exception as e:
        return {"success": False, "error": str(e), "model": model}


def embed_texts(model: str, texts: list[str], timeout: int = 30) -> dict:
    """Call 9Router embedding endpoint."""
    payload = json.dumps({
        "model": model,
        "input": texts if len(texts) > 1 else texts[0],
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{NINEROUTER_URL}/v1/embeddings",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        start = time.time()
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read())
        latency = time.time() - start
        data = result.get("data", [])
        embeddings = [d["embedding"] for d in data]
        dims = len(embeddings[0]) if embeddings else 0
        return {
            "success": True,
            "embeddings": embeddings,
            "dimensions": dims,
            "model_used": result.get("model", model),
            "latency": round(latency, 3),
            "count": len(embeddings),
        }
    except Exception as e:
        return {"success": False, "error": str(e), "model": model}


def record_benchmark(role: str, model_id: str, benchmark_id: str,
                     metrics: dict, notes: str = ""):
    """Record a benchmark result for a model in a role."""
    conn = sqlite3.connect(str(DB_PATH))
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    conn.execute("""
        INSERT INTO role_benchmarks (role, model_id, benchmark_id, timestamp, metrics_json, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (role, model_id, benchmark_id, now, json.dumps(metrics), notes))
    conn.commit()
    conn.close()


def set_role_preference(role: str, preferred: str, backup: str = None,
                        benchmark_id: str = "", reason: str = "",
                        confidence: str = "PROVISIONAL", sample_n: int = 0):
    """Set a provisional role preference with explicit sample size."""
    conn = sqlite3.connect(str(DB_PATH))
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    columns = {row[1] for row in conn.execute("PRAGMA table_info(role_preferences)").fetchall()}
    for name, definition in (("sample_n", "INTEGER DEFAULT 0"), ("preference_confidence", "TEXT DEFAULT 'LOW'")):
        if name not in columns:
            conn.execute(f"ALTER TABLE role_preferences ADD COLUMN {name} {definition}")
    conn.execute("""
        INSERT INTO role_preferences
        (role, preferred_model, backup_model, benchmark_id, selection_reason,
         confidence, last_benchmarked, sample_n, preference_confidence)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(role) DO UPDATE SET
            preferred_model=excluded.preferred_model,
            backup_model=excluded.backup_model,
            benchmark_id=excluded.benchmark_id,
            selection_reason=excluded.selection_reason,
            confidence=excluded.confidence,
            last_benchmarked=excluded.last_benchmarked,
            sample_n=excluded.sample_n,
            preference_confidence=excluded.preference_confidence
    """, (role, preferred, backup, benchmark_id, reason, confidence, now, sample_n, confidence))
    # Update model states
    conn.execute("UPDATE model_entities SET state = ? WHERE model_id = ?",
                 (ModelState.ROLE_PREFERRED, preferred))
    if backup:
        conn.execute("UPDATE model_entities SET state = ? WHERE model_id = ?",
                     (ModelState.ROLE_BACKUP, backup))
    conn.commit()
    conn.close()


def get_role_preference(role: str) -> Optional[dict]:
    """Get the current preferred model for a role."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM role_preferences WHERE role = ?", (role,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_role_preferences() -> dict:
    """Get all role preferences."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM role_preferences").fetchall()
    conn.close()
    return {row["role"]: dict(row) for row in rows}


def record_routing_decision(role: str, candidates: list[str], selected: str,
                           backup: str = None, reason: str = "",
                           mission_id: str = "m002.1"):
    """Record a routing decision for audit."""
    conn = sqlite3.connect(str(DB_PATH))
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    conn.execute("""
        INSERT INTO routing_decisions
        (mission_id, role, candidate_models, selected_model, backup_model,
         selection_reason, confidence, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (mission_id, role, json.dumps(candidates), selected, backup, reason, "MEDIUM", now))
    conn.commit()
    conn.close()


def shortlist_candidates(role: str, all_models: list[dict]) -> list[dict]:
    """Filter and shortlist candidates for a specific role."""
    candidates = []
    for m in all_models:
        mid = m.get("model_id", "")
        modalities = m.get("modalities", [])
        if isinstance(modalities, str):
            try:
                modalities = json.loads(modalities)
            except Exception:
                modalities = [modalities]

        eligible = True
        exclusion_reason = None

        if role in (Role.VISUAL_GROUNDING, Role.PROFESSIONAL_VISUAL_CRITIQUE):
            if m.get("vision_support", 0) != 1:
                eligible = False
                exclusion_reason = "no vision support"

        if role == Role.EMBEDDING_RETRIEVAL:
            if m.get("embedding_support", 0) != 1:
                eligible = False
                exclusion_reason = "not an embedding model"

        if role in (Role.PROFESSIONAL_EXTRACTION, Role.INDEPENDENT_VERIFICATION):
            if m.get("embedding_support", 0) == 1:
                eligible = False
                exclusion_reason = "embedding-only model"

        if eligible:
            candidates.append({**m, "exclusion_reason": None})
        else:
            candidates.append({**m, "exclusion_reason": exclusion_reason,
                              "eligible": False})

    return [c for c in candidates if c.get("exclusion_reason") is None]


def get_model_evidence_summary() -> dict:
    """Summarize all model intelligence evidence."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    models = conn.execute("SELECT * FROM model_entities").fetchall()
    benchmarks = conn.execute("SELECT * FROM role_benchmarks ORDER BY timestamp DESC").fetchall()
    prefs = conn.execute("SELECT * FROM role_preferences").fetchall()
    decisions = conn.execute("SELECT * FROM routing_decisions ORDER BY timestamp DESC LIMIT 20").fetchall()
    conn.close()

    return {
        "models": [dict(r) for r in models],
        "benchmarks": [dict(r) for r in benchmarks],
        "role_preferences": {r["role"]: dict(r) for r in prefs},
        "recent_decisions": [dict(r) for r in decisions],
        "total_models": len(models),
        "total_benchmarks": len(benchmarks),
    }


if __name__ == "__main__":
    print("=== Model Intelligence Fabric ===")
    print(f"DB: {DB_PATH}")
    print(f"9Router: {NINEROUTER_URL}")

    # Discover models
    print("\n--- Discovering available models ---")
    models = discover_available_models()
    print(f"Total models discovered: {len(models)}")

    # Shortlist for each role
    for role_name in [Role.PROFESSIONAL_EXTRACTION, Role.INDEPENDENT_VERIFICATION,
                      Role.EMBEDDING_RETRIEVAL, Role.VISUAL_GROUNDING,
                      Role.PROFESSIONAL_VISUAL_CRITIQUE]:
        shortlist = shortlist_candidates(role_name, models)
        print(f"\n{role_name}: {len(shortlist)} candidates")
        for c in shortlist[:8]:
            print(f"  {c['model_id']} ({c.get('model_family', '?')}, {c.get('cost_class', '?')})")

    # Show preferences
    prefs = get_all_role_preferences()
    if prefs:
        print("\n--- Current Role Preferences ---")
        for role, pref in prefs.items():
            print(f"  {role}: {pref.get('preferred_model', 'none')}")
    else:
        print("\n--- No role preferences set yet ---")
