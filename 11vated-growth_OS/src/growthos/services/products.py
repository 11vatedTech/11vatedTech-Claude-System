"""Product intake and versioned updates.

The founder can describe a product naturally; this service persists a
structured Product Canon and records every change as a ProductVersion. History
is never silently overwritten.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from growthos.audit import record_audit
from growthos.domain.enums import ProductMaturity
from growthos.domain.models_product import Product, ProductVersion
from growthos.shared.errors import NotFoundError
from growthos.shared.ids import new_id

# Fields allowed on intake/update (scalar + list canon fields).
CANON_SCALAR_FIELDS = {
    "name",
    "codename",
    "definition",
    "description",
    "core_problem",
    "core_insight",
    "maturity",
    "status",
    "positioning",
    "founder_involvement",
}
CANON_LIST_FIELDS = {
    "roadmap",
    "features",
    "capabilities",
    "technical_differentiators",
    "creative_differentiators",
    "value_propositions",
    "customer_outcomes",
    "use_cases",
    "target_customers",
    "buyers",
    "partners",
    "industries",
    "commercial_models",
    "pricing_hypotheses",
    "competitive_alternatives",
    "delivery_requirements",
    "marketing_assets",
    "sales_assets",
    "objections",
    "faq",
    "revenue_opportunities",
    "limitations",
    "risks",
    "claims",
}


def _snapshot(product: Product) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for field in CANON_SCALAR_FIELDS | CANON_LIST_FIELDS:
        value = getattr(product, field, None)
        if isinstance(value, list):
            data[field] = list(value)
        elif value is not None and hasattr(value, "value"):
            data[field] = value.value
        else:
            data[field] = value
    return data


async def get_product(session: AsyncSession, product_id: str) -> Product:
    result = await session.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    if product is None:
        raise NotFoundError(f"Product {product_id!r} not found")
    return product


async def intake_product(
    session: AsyncSession,
    *,
    name: str,
    actor: str = "founder",
    **fields: Any,
) -> Product:
    """Create a Product Canon record plus its first version snapshot."""
    if not name.strip():
        raise ValueError("Product name is required")

    maturity = fields.pop("maturity", None)
    if isinstance(maturity, str):
        maturity = ProductMaturity(maturity)

    product = Product(
        id=new_id(),
        name=name.strip(),
        codename=fields.pop("codename", None),
        definition=fields.pop("definition", None),
        description=fields.pop("description", None),
        core_problem=fields.pop("core_problem", None),
        core_insight=fields.pop("core_insight", None),
        maturity=maturity or ProductMaturity.IDEA,
        status=fields.pop("status", "active"),
        positioning=fields.pop("positioning", None),
        founder_involvement=fields.pop("founder_involvement", None),
    )
    for list_field in CANON_LIST_FIELDS:
        value = fields.pop(list_field, None)
        if value is not None:
            setattr(product, list_field, list(value) if isinstance(value, list) else [value])
    session.add(product)
    await session.flush()

    session.add(
        ProductVersion(
            id=new_id(),
            product_id=product.id,
            version=1,
            change_summary="Initial product intake",
            snapshot=_snapshot(product),
            created_by=actor,
        )
    )
    await record_audit(
        session,
        actor=actor,
        action="product.intake",
        entity_type="product",
        entity_id=product.id,
        new_state=_snapshot(product),
    )
    await session.flush()
    return product


async def update_product(
    session: AsyncSession,
    *,
    product_id: str,
    changes: dict[str, Any],
    actor: str = "founder",
    change_summary: str = "Product update",
) -> tuple[Product, ProductVersion]:
    """Apply a structured update and record a new version snapshot."""
    product = await get_product(session, product_id)
    previous = _snapshot(product)

    for field, value in changes.items():
        if field in CANON_SCALAR_FIELDS:
            if field == "maturity" and isinstance(value, str):
                value = ProductMaturity(value)
            setattr(product, field, value)
        elif field in CANON_LIST_FIELDS:
            if isinstance(value, list):
                setattr(product, field, list(value))
            else:
                setattr(product, field, [value])
        else:
            raise ValueError(f"Unknown product field: {field!r}")

    latest = await session.execute(
        select(func.max(ProductVersion.version)).where(
            ProductVersion.product_id == product_id
        )
    )
    next_version = (latest.scalar() or 0) + 1

    version = ProductVersion(
        id=new_id(),
        product_id=product_id,
        version=next_version,
        change_summary=change_summary,
        snapshot=_snapshot(product),
        created_by=actor,
    )
    session.add(version)
    await record_audit(
        session,
        actor=actor,
        action="product.update",
        entity_type="product",
        entity_id=product_id,
        previous_state=previous,
        new_state=_snapshot(product),
    )
    await session.flush()
    return product, version
