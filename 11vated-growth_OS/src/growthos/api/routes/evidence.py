"""Evidence and provenance routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from growthos.api.deps import FounderDep, SessionDep
from growthos.domain.enums import TruthClass
from growthos.domain.models_evidence import SourceEvidence
from growthos.intelligence import evidence as evidence_service

router = APIRouter(prefix="/evidence", tags=["evidence"])


class EvidenceIn(BaseModel):
    source_type: str
    content: str
    truth_class: str = "FACT"
    source_ref: str | None = None
    provenance: dict[str, Any] = {}


def _serialize(evidence: SourceEvidence) -> dict[str, Any]:
    return {
        "id": evidence.id,
        "source_type": evidence.source_type,
        "source_ref": evidence.source_ref,
        "content": evidence.content,
        "truth_class": evidence.truth_class.value,
        "captured_at": evidence.captured_at,
        "provenance": evidence.provenance,
    }


@router.get("")
async def list_evidence(session: SessionDep, founder: FounderDep):
    result = await session.execute(
        select(SourceEvidence).order_by(SourceEvidence.captured_at.desc()).limit(100)
    )
    return {"evidence": [_serialize(e) for e in result.scalars().all()]}


@router.post("", status_code=201)
async def create_evidence(
    session: SessionDep, founder: FounderDep, body: EvidenceIn
):
    try:
        truth_class = TruthClass(body.truth_class)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid truth_class") from exc
    try:
        evidence, created = await evidence_service.record_evidence(
            session,
            source_type=body.source_type,
            content=body.content,
            truth_class=truth_class,
            source_ref=body.source_ref,
            provenance=body.provenance,
        )
        return {**_serialize(evidence), "created": created}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=422, detail=str(exc)) from exc
