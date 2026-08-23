from __future__ import annotations

# Documentation-only claim (class F): bulk_export is described in the spec
# (see EXPORT_SPEC) but has no implementation. Lexical search finds the token
# in this comment; the semantic provider must report no definition.

EXPORT_SPEC = "bulk_export(project_id: str, fmt: str) -> Path  -- planned"