"""Growth Agent — natural-language commercial command.

The founder can describe a product naturally; this service detects intent,
extracts what is confidently available (unknown stays unknown), persists
Product Canon, and answers context questions from persisted entities — never
from chat memory alone.

Intents handled here:

* PRODUCT_INTAKE_INTENT — “I built a platform that…” → create Product + Canon
* PRODUCT_UPDATE_INTENT  — “It’s production ready now” / “Offer this to agencies”
* MARKET_THIS_INTENT     — “Market this” → create a DRAFT Campaign linked to the product
* CONTEXT_QUESTION_INTENT — “Who should buy this?” / “What is the biggest weakness?”
* AMBIGUOUS              — multiple products, ask/select rather than modify the wrong one
"""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growthos.audit import record_audit
from growthos.domain.enums import ClaimTag, ProductMaturity
from growthos.domain.models_product import Product, ProductVersion
from growthos.services import campaigns as campaign_service
from growthos.services import products as product_service
from growthos.services.product_intelligence import (
    commercial_model_analysis,
    market_map,
    pricing_hypotheses,
    sales_readiness,
)
from growthos.shared.errors import NotFoundError

INTAKE_MARKERS = re.compile(
    r"(i (built|made|created|developed|have|run|own|started|launched)|"
    r"we (built|made|created|developed|have|run|own|started|launched)|"
    r"add (it|this|the product)|create a product|new product|"
    r"my product|our product|a platform|an app|a tool|a service|a product)",
    re.IGNORECASE,
)
MARKET_MARKERS = re.compile(
    r"\b(market this|market it|sell this|sell it|campaign for|create a campaign|"
    r"launch a campaign|go to market|start marketing)\b",
    re.IGNORECASE,
)
UPDATE_MARKERS = re.compile(
    r"\b(change|update|set|remove|drop|add|offer|target|price|pricing|"
    r"production ready|ready now|rename|call it)\b",
    re.IGNORECASE,
)
CONTEXT_QUESTION_MARKERS = re.compile(
    r"\b(who should buy|who would buy|biggest weakness|main weakness|"
    r"can we license|license this|market size|who is the buyer|"
    r"how do we sell|what is the value|find partners|position)\b",
    re.IGNORECASE,
)


class AgentResponse:
    """Structured agent reply with any side effects performed."""

    def __init__(
        self,
        intent: str,
        reply: str,
        product_id: str | None = None,
        campaign_id: str | None = None,
        needs_clarification: bool = False,
        actions: list[dict[str, Any]] | None = None,
    ) -> None:
        self.intent = intent
        self.reply = reply
        self.product_id = product_id
        self.campaign_id = campaign_id
        self.needs_clarification = needs_clarification
        self.actions = actions or []

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "reply": self.reply,
            "product_id": self.product_id,
            "campaign_id": self.campaign_id,
            "needs_clarification": self.needs_clarification,
            "actions": self.actions,
        }


def _detect_intent(message: str) -> str:
    if INTAKE_MARKERS.search(message):
        return "PRODUCT_INTAKE_INTENT"
    if MARKET_MARKERS.search(message):
        return "MARKET_THIS_INTENT"
    if CONTEXT_QUESTION_MARKERS.search(message):
        return "CONTEXT_QUESTION_INTENT"
    if UPDATE_MARKERS.search(message):
        return "PRODUCT_UPDATE_INTENT"
    return "PRODUCT_INTAKE_INTENT" if "product" in message.lower() else "AMBIGUOUS"


async def _resolve_product(
    session: AsyncSession, message: str, product_id: str | None = None
) -> Product | None:
    """Resolve the target product from persisted entities (never chat memory).

    Priority: explicit product_id → name/mention in the message → most recent
    product. Returns None when ambiguous (multiple products, no clear target).
    """
    if product_id:
        try:
            return await product_service.get_product(session, product_id)
        except NotFoundError:
            return None

    products = (await session.execute(select(Product).order_by(Product.created_at.desc()))).scalars().all()
    if not products:
        return None
    if len(products) == 1:
        return products[0]

    # Try to find a mention of a product name.
    lower = message.lower()
    for p in products:
        if p.name.lower() in lower or (p.codename and p.codename.lower() in lower):
            return p
    return None  # ambiguous


def _extract_structured_intake(message: str) -> dict[str, Any]:
    """Deterministic extraction of what is confidently available.

    Unknown stays unknown — we never invent names, prices, or features. The
    name is the hardest field; we use the founder's own phrasing or the first
    quoted/product-like phrase, else we ask.
    """
    data: dict[str, Any] = {}
    # Definition: the clause after the intake verb. Handles both
    # "a platform that X" and "a platform called Name that X".
    match = re.search(
        r"(?:built|made|created|developed|started|launched|have|run|own)\s+"
        r"(?:a|an|the)?\s*(?:platform|app|tool|service|product|business|company)?"
        r"(?:\s+called\s+[A-Z][A-Za-z0-9 _\-]{1,40}?)?\s+that\s+(.+?)(?:[.!?]|$)",
        message,
        re.IGNORECASE,
    )
    if match:
        data["definition"] = match.group(1).strip().strip('"')
    # Name: quoted phrase, or a capitalized name after 'called', else ask.
    name_match = re.search(
        r"[Cc]all(?:ed)?\s+[“\"']?([A-Z][A-Za-z0-9 _\-]{1,40}?)[”\"']?(?=\s+(?:that|which|and|for|to|,|\.|$))",
        message,
    )
    if name_match:
        data["name"] = name_match.group(1).strip()
    else:
        quoted = re.search(r"[“\"']([^”\"']{2,60})[”\"']", message)
        if quoted:
            data["name"] = quoted.group(1).strip()
    if "definition" in data:
        words = data["definition"].split()
        if words:
            data.setdefault("core_problem", "unknown — to be clarified with founder")
            data["core_insight"] = " ".join(words[:24])
    return data


async def _apply_update(
    session: AsyncSession,
    product: Product,
    message: str,
    actor: str,
) -> tuple[Product, ProductVersion, list[str]]:
    """Interpret a natural-language update into structured Canon changes."""
    changes: dict[str, Any] = {}
    notes: list[str] = []
    lower = message.lower()

    if "production ready" in lower or "production-ready" in lower:
        changes["maturity"] = ProductMaturity.PRODUCTION
        notes.append("Maturity set to PRODUCTION (founder statement)")
    elif "mvp" in lower or "minimal viable" in lower:
        changes["maturity"] = ProductMaturity.MVP
        notes.append("Maturity set to MVP (founder statement)")
    elif "prototype" in lower:
        changes["maturity"] = ProductMaturity.PROTOTYPE
        notes.append("Maturity set to PROTOTYPE (founder statement)")

    price_match = re.search(
        r"(?:price|pricing|charge|cost)(?:\s+should)?(?:\s+start|\s+begin)?"
        r"(?:\s+at)?\s*[\\$]?\s*(\d[\d,\.]*)",
        message,
        re.IGNORECASE,
    )
    if price_match:
        raw = price_match.group(1).replace(",", "")
        try:
            price = float(raw)
        except ValueError:
            price = None
        if price:
            hypothesis = {
                "model": "unknown",
                "target_price": price,
                "range": [round(price * 0.8, 2), round(price * 1.2, 2)],
                "floor_hypothesis": None,
                "premium_configuration": None,
                "entry_offer": None,
                "recurring_component": None,
                "confidence": 0.4,
                "label": "PRICING HYPOTHESIS",
                "reasoning": f"Founder-stated target price {price:g}; label stays hypothesis until sales evidence",
            }
            existing = list(product.pricing_hypotheses or [])
            existing = [h for h in existing if h.get("label") != "PRICING HYPOTHESIS"]
            existing.append(hypothesis)
            changes["pricing_hypotheses"] = existing
            notes.append(f"Pricing hypothesis set to {price:g} (founder statement)")

    if "licens" in lower:
        models = list(product.commercial_models or [])
        if "licensing" not in models:
            models.append("licensing")
        changes["commercial_models"] = models
        notes.append("Added licensing as a commercial model hypothesis")

    if "agency" in lower or "agencies" in lower:
        customers = list(product.target_customers or [])
        if "agencies" not in customers:
            customers.append("agencies")
        changes["target_customers"] = customers
        notes.append("Added agencies as a target-customer hypothesis")

    if "restaurant" in lower and ("remove" in lower or "drop" in lower):
        customers = [c for c in (product.target_customers or []) if "restaurant" not in c.lower()]
        changes["target_customers"] = customers
        notes.append("Removed restaurants from target customers (founder instruction)")

    if not changes:
        # Explicit acknowledgment: record as a claim but change nothing.
        claims = list(product.claims or [])
        claims.append(
            {
                "text": message.strip()[:500],
                "tag": ClaimTag.FOUNDER_FACT.value,
                "confidence": 1.0,
            }
        )
        changes["claims"] = claims
        notes.append("Recorded founder statement as a claim; no structured field changed")

    product, version = await product_service.update_product(
        session,
        product_id=product.id,
        changes=changes,
        actor=actor,
        change_summary="; ".join(notes) or "Natural-language product update",
    )
    return product, version, notes


async def handle_agent_message(
    session: AsyncSession,
    *,
    founder_email: str,
    message: str,
    product_id: str | None = None,
) -> AgentResponse:
    """Process one founder message. Returns an AgentResponse."""
    intent = _detect_intent(message)

    # ---- Product intake -----------------------------------------------------
    if intent == "PRODUCT_INTAKE_INTENT":
        existing = (await session.execute(select(Product))).scalars().all()
        extracted = _extract_structured_intake(message)
        if not extracted.get("name"):
            return AgentResponse(
                intent=intent,
                reply=(
                    "**Ready for first product intake.** I heard you describe something — "
                    "what should we call it? (a short name is enough; I'll keep unknowns as unknown)"
                ),
                needs_clarification=True,
            )
        if existing:
            # Only create if the founder is clearly describing a NEW product,
            # not talking about an existing one.
            for p in existing:
                if p.name.lower() in message.lower():
                    return AgentResponse(
                        intent="PRODUCT_UPDATE_INTENT",
                        reply=(
                            f"You already have **{p.name}** in the Product Canon. "
                            "Did you mean to update it? If so, tell me what changed — "
                            "e.g. \"It's production ready now\"."
                        ),
                        product_id=p.id,
                        needs_clarification=True,
                    )
        product = await product_service.intake_product(
            session,
            name=extracted["name"],
            actor=founder_email,
            **{k: v for k, v in extracted.items() if k != "name"},
        )
        await record_audit(
            session,
            actor=founder_email,
            action="agent.product_intake",
            entity_type="product",
            entity_id=product.id,
            reason=f"Natural-language intake: {message[:200]}",
        )
        await session.flush()
        return AgentResponse(
            intent=intent,
            reply=(
                f"Added **{product.name}** to the Product Canon. "
                "Unknown fields (pricing, buyers, markets) stay **unknown** until "
                "you tell me or real evidence arrives. What do you want to do next — "
                "market it, refine pricing, or dig into the market map?"
            ),
            product_id=product.id,
            actions=[{"action": "product.created", "product_id": product.id}],
        )

    # ---- Context resolution: find the target product ------------------------
    target: Product | None = await _resolve_product(session, message, product_id)

    if intent == "MARKET_THIS_INTENT":
        if target is None:
            products = (await session.execute(select(Product))).scalars().all()
            if not products:
                return AgentResponse(
                    intent=intent,
                    reply="There's no product in the Canon yet — describe what you built and I'll add it first.",
                    needs_clarification=True,
                )
            return AgentResponse(
                intent=intent,
                reply=(
                    "Which product should I market? "
                    + " · ".join(p.name for p in products)
                ),
                needs_clarification=True,
            )
        mm = market_map(target)
        ph = pricing_hypotheses(target)
        sm = sales_readiness(target)
        campaign = await campaign_service.create_campaign(
            session,
            product_id=target.id,
            name=f"{target.name} — Market Validation",
            actor=founder_email,
            objective=(
                f"Validate the market for {target.name} with real discovery "
                "and outreach responses."
            ),
            buyer=",".join(mm["buyer_roles"]) or None,
            offer=target.definition or None,
            pricing_hypothesis=(
                str(ph["hypotheses"][0].get("target_price"))
                if ph["hypotheses"] and ph["hypotheses"][0].get("target_price")
                else None
            ),
            channels=["email"],
            prospect_criteria={
                "icps": mm["ideal_customer_profiles"],
                "markets": mm["primary_market_hypothesis"],
                "evidence_required": "real discovery and outreach responses",
            },
            messaging_strategy=(
                f"Position around {target.core_problem or 'the core problem'} "
                "and validate the value proposition with real buyers."
            ),
            proof_assets=[],
            validation_goals=[
                "Confirm or reject the primary market hypothesis",
                "Collect real buyer response evidence",
                "Validate pricing hypothesis",
            ],
            success_metrics=[
                "Response rate from real outreach",
                "Qualified conversations started",
                "Pricing feedback",
            ],
            stop_conditions=[
                "No real response evidence after N attempts",
                "Wrong audience confirmed",
                "Weak positioning",
            ],
        )
        await record_audit(
            session,
            actor=founder_email,
            action="agent.market_this",
            entity_type="campaign",
            entity_id=campaign.id,
            reason=f"Market-this intent for product {target.id}",
        )
        await session.flush()
        return AgentResponse(
            intent=intent,
            reply=(
                f"Created campaign **{campaign.name}** (DRAFT) linked to **{target.name}**. "
                "It starts with **0 real prospects** — no fabricated targets. "
                "Next step: define prospect criteria from real discovery, then draft "
                "outreach for your approval. Everything here is hypothesis until real "
                "response evidence arrives."
            ),
            product_id=target.id,
            campaign_id=campaign.id,
            actions=[
                {"action": "campaign.created", "campaign_id": campaign.id, "product_id": target.id}
            ],
        )

    if intent == "CONTEXT_QUESTION_INTENT":
        if target is None:
            return AgentResponse(
                intent=intent,
                reply="I need a product in the Canon to answer that. Describe what you built first.",
                needs_clarification=True,
            )
        mm = market_map(target)
        sm = sales_readiness(target)
        ph = pricing_hypotheses(target)
        cm = commercial_model_analysis(target)
        lowest = min(sm["components"].items(), key=lambda kv: kv[1]["score"])
        reply = (
            f"**{target.name}** — from persisted Product Canon (not chat memory):\n\n"
            f"**Who should buy this?** {mm['primary_market_hypothesis'] or 'Unknown — market hypothesis not stated yet.'} "
            f"Buyer roles: {', '.join(mm['buyer_roles']) or 'unknown'}.\n\n"
            f"**Biggest weakness (lowest readiness):** {lowest[0]} at {lowest[1]['score']}/100 "
            f"({lowest[1]['reasoning']}).\n\n"
            f"**Pricing:** {str(ph['hypotheses'][0].get('target_price')) if ph['hypotheses'] and ph['hypotheses'][0].get('target_price') else 'no price hypothesis yet — all pricing is hypothesis until sales evidence'}.\n\n"
            f"**Commercial models under consideration:** "
            + ", ".join(f"{a['model']} ({a['fit'][:40]}…)" for a in cm["analysis"])
        )
        return AgentResponse(
            intent=intent,
            reply=reply,
            product_id=target.id,
        )

    # ---- Product update -----------------------------------------------------
    if intent == "PRODUCT_UPDATE_INTENT":
        if target is None:
            return AgentResponse(
                intent=intent,
                reply="Which product do you mean? I'll ask rather than guess: ",
                needs_clarification=True,
            )
        updated, version, notes = await _apply_update(session, target, message, founder_email)
        await session.flush()
        return AgentResponse(
            intent=intent,
            reply=(
                f"Updated **{updated.name}** (version {version.version}). "
                + " ".join(notes)
                + " History preserved — previous values are in the version log."
            ),
            product_id=updated.id,
            actions=[{"action": "product.updated", "product_id": updated.id, "version": version.version}],
        )

    # ---- Ambiguous ----------------------------------------------------------
    products = (await session.execute(select(Product))).scalars().all()
    if products:
        return AgentResponse(
            intent="AMBIGUOUS",
            reply=(
                "I'm not sure what you'd like to do. I can: add a product "
                "(“I built a platform that…”), update one (tell me what changed), "
                "market one (“Market this”), or answer context questions "
                "(“Who should buy this?”). Which?"
            ),
            needs_clarification=True,
        )
    return AgentResponse(
        intent="AMBIGUOUS",
        reply=(
            "**Ready for first product intake.** Describe what you built — "
            "e.g. “I built a platform that turns short stories into cinematic "
            "full-screen experiences. Add it as a product and help me understand "
            "how we can sell it.”"
        ),
        needs_clarification=True,
    )
