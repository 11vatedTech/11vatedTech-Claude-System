"""Growth Agent route — natural-language commercial command."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from growthos.api.deps import FounderDep, SessionDep
from growthos.services.agent import handle_agent_message
from growthos.services.product_intelligence import (
    commercial_model_analysis,
    market_map,
    pricing_hypotheses,
    sales_readiness,
)
from growthos.services.products import get_product

router = APIRouter(prefix="/agent", tags=["agent"])


class AgentMessageIn(BaseModel):
    message: str
    product_id: str | None = None


@router.post("/message")
async def agent_message(
    session: SessionDep, founder: FounderDep, body: AgentMessageIn
):
    response = await handle_agent_message(
        session,
        founder_email=founder.email,
        message=body.message,
        product_id=body.product_id,
    )
    return response.to_dict()


@router.get("/products/{product_id}/intelligence")
async def product_intelligence(session: SessionDep, founder: FounderDep, product_id: str):
    product = await get_product(session, product_id)
    return {
        "market_map": market_map(product),
        "sales_readiness": sales_readiness(product),
        "pricing": pricing_hypotheses(product),
        "commercial_models": commercial_model_analysis(product),
        "product": {
            "id": product.id,
            "name": product.name,
            "maturity": product.maturity.value if product.maturity else None,
        },
    }
