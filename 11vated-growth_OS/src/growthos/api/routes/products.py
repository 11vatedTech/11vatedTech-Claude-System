"""Product Canon routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from growthos.api.deps import FounderDep, SessionDep
from growthos.domain.models_product import Product, ProductVersion
from growthos.services import products as product_service

router = APIRouter(prefix="/products", tags=["products"])


class ProductIntakeIn(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    codename: str | None = None
    definition: str | None = None
    description: str | None = None
    core_problem: str | None = None
    core_insight: str | None = None
    maturity: str | None = None
    positioning: str | None = None
    features: list[str] = []
    capabilities: list[str] = []
    value_propositions: list[str] = []
    target_customers: list[str] = []
    industries: list[str] = []
    use_cases: list[str] = []


class ProductUpdateIn(BaseModel):
    changes: dict[str, Any]
    change_summary: str = "Product update"


def _serialize(product: Product) -> dict[str, Any]:
    canon = {}
    for field in (
        "roadmap", "features", "capabilities", "technical_differentiators",
        "creative_differentiators", "value_propositions", "customer_outcomes",
        "use_cases", "target_customers", "buyers", "partners", "industries",
        "commercial_models", "pricing_hypotheses", "competitive_alternatives",
        "delivery_requirements", "marketing_assets", "sales_assets",
        "objections", "faq", "revenue_opportunities", "limitations", "risks",
        "claims",
    ):
        canon[field] = getattr(product, field, None)
    return {
        "id": product.id,
        "name": product.name,
        "codename": product.codename,
        "definition": product.definition,
        "description": product.description,
        "core_problem": product.core_problem,
        "core_insight": product.core_insight,
        "maturity": product.maturity.value if product.maturity else None,
        "status": product.status,
        "positioning": product.positioning,
        "founder_involvement": product.founder_involvement,
        "created_at": product.created_at,
        "updated_at": product.updated_at,
        "canon": canon,
    }


@router.get("")
async def list_products(session: SessionDep, founder: FounderDep):
    result = await session.execute(select(Product).order_by(Product.created_at))
    return {"products": [_serialize(p) for p in result.scalars().all()]}


@router.post("", status_code=201)
async def create_product(
    session: SessionDep, founder: FounderDep, body: ProductIntakeIn
):
    try:
        product = await product_service.intake_product(
            session,
            name=body.name,
            actor=founder.email,
            codename=body.codename,
            definition=body.definition,
            description=body.description,
            core_problem=body.core_problem,
            core_insight=body.core_insight,
            maturity=body.maturity,
            positioning=body.positioning,
            features=body.features,
            capabilities=body.capabilities,
            value_propositions=body.value_propositions,
            target_customers=body.target_customers,
            industries=body.industries,
            use_cases=body.use_cases,
        )
        return _serialize(product)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{product_id}")
async def get_product(session: SessionDep, founder: FounderDep, product_id: str):
    try:
        product = await product_service.get_product(session, product_id)
        return _serialize(product)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=404, detail="Product not found") from exc


@router.patch("/{product_id}")
async def update_product(
    session: SessionDep,
    founder: FounderDep,
    product_id: str,
    body: ProductUpdateIn,
):
    try:
        product, version = await product_service.update_product(
            session,
            product_id=product_id,
            changes=body.changes,
            actor=founder.email,
            change_summary=body.change_summary,
        )
        return {"product": _serialize(product), "version": version.version}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{product_id}/versions")
async def product_versions(
    session: SessionDep, founder: FounderDep, product_id: str
):
    result = await session.execute(
        select(ProductVersion)
        .where(ProductVersion.product_id == product_id)
        .order_by(ProductVersion.version.desc())
    )
    return {
        "versions": [
            {
                "version": v.version,
                "change_summary": v.change_summary,
                "created_by": v.created_by,
                "created_at": v.created_at,
            }
            for v in result.scalars().all()
        ]
    }
