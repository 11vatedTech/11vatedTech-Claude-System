"""Product intelligence: market map, sales readiness, pricing hypotheses.

Every output is explicitly a HYPOTHESIS until real evidence validates it.
Confidence is low when evidence is lacking — never a fabricated number.
These engines are deterministic structures; the model may enrich them, but the
schema and the "unknown stays unknown" rule are enforced here in software.
"""

from __future__ import annotations

from typing import Any

from growthos.domain.models_product import Product

# Deterministic sales-readiness components with scoring guidance.
SALES_READINESS_COMPONENTS = [
    "problem_clarity",
    "buyer_clarity",
    "value_proposition",
    "maturity",
    "demo_quality",
    "proof",
    "pricing_confidence",
    "market_evidence",
    "differentiation",
    "fulfillment_readiness",
    "support_readiness",
    "marketing_assets",
    "founder_capacity",
]

# Canon fields that count as evidence toward each readiness component.
_EVIDENCE_FIELDS: dict[str, tuple[str, ...]] = {
    "problem_clarity": ("core_problem", "core_insight", "definition"),
    "buyer_clarity": ("buyers", "target_customers"),
    "value_proposition": ("value_propositions", "customer_outcomes"),
    "maturity": ("maturity",),
    "demo_quality": ("marketing_assets", "sales_assets"),
    "proof": ("claims", "proof"),
    "pricing_confidence": ("pricing_hypotheses",),
    "market_evidence": ("target_customers", "industries", "market_evidence"),
    "differentiation": ("technical_differentiators", "creative_differentiators"),
    "fulfillment_readiness": ("delivery_requirements",),
    "support_readiness": ("delivery_requirements", "limitations"),
    "marketing_assets": ("marketing_assets",),
    "founder_capacity": ("founder_involvement",),
}


def _evidence_strength(product: Product, field: str) -> tuple[float, list[str]]:
    """How much real canon content exists for a readiness component."""
    evidence: list[str] = []
    for canon_field in _EVIDENCE_FIELDS.get(field, ()):
        value = getattr(product, canon_field, None)
        if isinstance(value, list):
            if value:
                evidence.append(f"{canon_field}: {len(value)} item(s)")
        elif value:
            evidence.append(f"{canon_field}: present")
    # Any tagged founder claim with high confidence counts as strong evidence.
    claims = product.claims or []
    if claims:
        evidence.append(f"claims: {len(claims)}")
    strength = min(1.0, len(evidence) / 3.0)
    return strength, evidence


def sales_readiness(product: Product) -> dict[str, Any]:
    """Compute evidence-backed sales readiness (0-100 per component)."""
    components: dict[str, Any] = {}
    for name in SALES_READINESS_COMPONENTS:
        strength, evidence = _evidence_strength(product, name)
        # Maturity is a special case: an MVP has real readiness.
        if name == "maturity":
            maturity_rank = {
                "idea": 0.1, "concept": 0.2, "prototype": 0.3,
                "working_prototype": 0.5, "mvp": 0.7, "production": 0.9,
                "scaling": 1.0,
            }
            rank = maturity_rank.get((product.maturity.value if product.maturity else ""), 0.1)
            score = round(rank * 100, 1)
            confidence = 0.9  # maturity is founder-stated
            reasoning = f"Maturity is founder-stated: {product.maturity.value if product.maturity else 'unknown'}"
        else:
            score = round(strength * 100, 1)
            confidence = round(max(0.2, strength), 2)
            reasoning = (
                f"{len(evidence)} canon evidence items"
                if evidence
                else "No canon evidence recorded — unknown remains unknown"
            )
        components[name] = {
            "score": score,
            "confidence": confidence,
            "reasoning": reasoning,
            "evidence": evidence,
        }
    overall = round(sum(c["score"] for c in components.values()) / len(components), 1)
    return {
        "overall": overall,
        "version": "sales-readiness-v1",
        "components": components,
    }


def market_map(product: Product) -> dict[str, Any]:
    """Generate structured market hypotheses from persisted canon."""
    target_customers = product.target_customers or []
    industries = product.industries or []
    buyers = product.buyers or []
    use_cases = product.use_cases or []

    primary = industries[0] if industries else (target_customers[0] if target_customers else None)
    secondary = industries[1:] if len(industries) > 1 else []
    icps = (
        [f"{c} (in {i})" for c, i in zip(target_customers, industries, strict=False)]
        if target_customers and industries
        else list(target_customers)
    )

    return {
        "primary_market_hypothesis": primary,
        "secondary_markets": secondary,
        "emerging_applications": use_cases,
        "ideal_customer_profiles": icps,
        "buyer_roles": buyers,
        "users_vs_buyers": "unknown until real conversations validate",
        "pain_points": [],
        "trigger_events": [],
        "channel_partners": [],
        "referral_sources": [],
        "potential_enterprise_buyers": [],
        "potential_early_adopters": [],
        "truth_class": "HYPOTHESIS",
        "evidence_gap_note": (
            "All market conclusions are hypotheses until validated by real "
            "discovery, outreach responses, or founder confirmation."
        ),
    }


def pricing_hypotheses(product: Product) -> dict[str, Any]:
    """Generate pricing hypotheses from canon, labeled as hypotheses."""
    existing = product.pricing_hypotheses or []
    models = product.commercial_models or []
    hypotheses: list[dict[str, Any]] = list(existing)

    if not hypotheses:
        # Seed from commercial models if stated; otherwise an honest unknown.
        for m in models:
            hypotheses.append(
                {
                    "model": m,
                    "target_price": None,
                    "range": None,
                    "floor_hypothesis": None,
                    "premium_configuration": None,
                    "entry_offer": None,
                    "recurring_component": None,
                    "confidence": 0.2,
                    "label": "PRICING HYPOTHESIS",
                    "reasoning": "Derived from founder-stated commercial model; price requires real sales evidence",
                }
            )
        if not hypotheses:
            hypotheses.append(
                {
                    "model": "unknown",
                    "target_price": None,
                    "range": None,
                    "floor_hypothesis": None,
                    "premium_configuration": None,
                    "entry_offer": None,
                    "recurring_component": None,
                    "confidence": 0.0,
                    "label": "PRICING HYPOTHESIS",
                    "reasoning": "No commercial model or price evidence yet — pricing stays a hypothesis until founder input",
                }
            )
    return {
        "hypotheses": hypotheses,
        "truth_class": "PRICING HYPOTHESIS",
        "final_price_requires_founder_approval": True,
        "note": (
            "Prices are labeled PRICING HYPOTHESIS until real sales evidence "
            "exists. The externally communicated price requires founder approval."
        ),
    }


def commercial_model_analysis(product: Product) -> dict[str, Any]:
    """Reason about viable commercial models without defaulting to SaaS."""
    stated = product.commercial_models or []
    return {
        "stated_models": stated,
        "analysis": [
            {
                "model": "project_based_implementation",
                "fit": "Strong for custom delivery; matches founder involvement and delivery requirements.",
                "notes": "Consider if delivery is bespoke per client.",
            },
            {
                "model": "productized_service",
                "fit": "Good if the product can be delivered repeatably with limited customization.",
                "notes": "Higher margin potential; requires packaging.",
            },
            {
                "model": "subscription",
                "fit": "Only if the product has ongoing recurring value and support costs.",
                "notes": "Do not default to SaaS; validate willingness to pay recurring.",
            },
            {
                "model": "licensing",
                "fit": "Relevant if the product can be embedded or white-labeled by partners.",
                "notes": "Investigate partner/channel demand first.",
            },
            {
                "model": "hybrid",
                "fit": "Consider implementation fee + recurring support or license.",
                "notes": "Often best for agency-style delivery with ongoing relationships.",
            },
        ],
        "truth_class": "HYPOTHESIS",
        "optimization_rule": "Choose based on actual buyer behavior and 11vatedTech delivery economics, not defaults.",
    }
