"""LinkedIn integration (official APIs only).

No scraping, no automated connection requests, no bulk DMs. The network graph
is seeded from the founder's official connections archive export, normalized
and deduplicated.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Capability matrix: what LinkedIn's official APIs can actually do. A
# capability is only claimed as IMPLEMENTED when real OAuth grants prove it.
# See docs/integrations/LINKEDIN_CAPABILITY_MATRIX.md.
CAPABILITY_MATRIX: list[dict[str, str]] = [
    {
        "capability": "Sign In with LinkedIn (OpenID Connect)",
        "official_api": "Yes",
        "permission": "r_liteprofile / r_emailaddress",
        "status": "IMPLEMENTED — AWAITING REAL OAUTH",
    },
    {
        "capability": "Organization Page publishing",
        "official_api": "Yes (with approval)",
        "permission": "w_organization_social",
        "status": "NOT CONFIGURED",
    },
    {
        "capability": "Automated connection requests",
        "official_api": "No",
        "permission": "N/A",
        "status": "NOT IMPLEMENTED (prohibited)",
    },
    {
        "capability": "Bulk direct messages",
        "official_api": "No",
        "permission": "N/A",
        "status": "NOT IMPLEMENTED (prohibited)",
    },
    {
        "capability": "Scraping member pages",
        "official_api": "No",
        "permission": "N/A",
        "status": "NOT IMPLEMENTED (prohibited)",
    },
]


@dataclass(frozen=True)
class ConnectionImportRow:
    first_name: str
    last_name: str
    company: str | None
    position: str | None
    connected_at: datetime | None
    email: str | None
    linkedin_url: str | None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


def parse_connections_csv(path: str | Path) -> list[ConnectionImportRow]:
    """Normalize an official LinkedIn connections archive CSV.

    LinkedIn's export column names vary by year; we accept the common variants
    and tolerate missing columns.
    """
    rows: list[ConnectionImportRow] = []
    with Path(path).open(encoding="utf-8", errors="replace", newline="") as fh:
        reader = csv.DictReader(fh)
        for raw in reader:
            first = _pick(raw, "First Name", "FirstName", "first_name")
            last = _pick(raw, "Last Name", "LastName", "last_name")
            if not first and not last:
                continue
            rows.append(
                ConnectionImportRow(
                    first_name=(first or "").strip(),
                    last_name=(last or "").strip(),
                    company=_pick(raw, "Company", "company"),
                    position=_pick(raw, "Position", "Title", "position"),
                    connected_at=_parse_date(
                        _pick(raw, "Connected On", "ConnectedOn", "connected_on")
                    ),
                    email=_pick(raw, "Email Address", "Email", "email"),
                    linkedin_url=_pick(raw, "URL", "Profile URL", "url"),
                )
            )
    return rows


def _pick(row: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        if key in row and row[key]:
            return str(row[key])
    # Case-insensitive fallback.
    lowered = {k.lower(): v for k, v in row.items()}
    for key in keys:
        if key.lower() in lowered and lowered[key.lower()]:
            return str(lowered[key.lower()])
    return None


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ("%d %b %Y", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(value.strip(), fmt).replace(tzinfo=UTC)
        except ValueError:
            continue
    return None
