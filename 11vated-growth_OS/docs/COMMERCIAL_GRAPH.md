# Commercial Intelligence Graph

GrowthOS models commercial reality as a relational graph, not one giant JSON
document. 46 tables span four layers.

## Identity & network

- `person` — real people (dedup by name+email, unique LinkedIn ID)
- `company` — real businesses (dedup by name+domain)
- `person_company` — position links
- `relationship` — directed subject↔object edge with stage, temperature,
  thesis, roles, last meaningful interaction, recommended next move
- `relationship_event` — real interaction history (the only basis for
  relationship strength)

## Evidence & provenance

- `source_evidence` — raw FACT/OBSERVATION (dedup by source-type + content hash)
- `intelligence_claim` — INFERENCE/HYPOTHESIS with confidence + reasoning
- `claim_evidence` — links a claim to its supporting evidence
- `research_observation` — structured research findings tied to evidence
- `learning` — statistically-honest lessons (mandatory sample size)

## Product & market

- `product` — the Product Canon (versioned, truth-tagged claims)
- `product_version` — immutable version history
- `capability` / `capability_evidence` — deliverable capability catalog
- `market`, `market_hypothesis`, `ideal_customer_profile`

## Commercial

- `prospect` — discovered lead (person+company+source evidence)
- `campaign` / `campaign_prospect` — Product → Market → Campaign engine
- `product_prospect_match` — bidirectional product↔prospect fit
- `opportunity` + `opportunity_transition` (state machine) + `opportunity_score`
  (15 factor scores + overall + confidence + classification)
- `offer`, `proposal`, `project`, `revenue_event` (booked/collected)
- `commitment`, `objection`, `referral`

## Communication & operations

- `conversation`, `message` (raw preserved, dedup by external message ID)
- `outreach` (state machine: draft → … → sent → replied / opted out)
- `suppression_record` (consulted by every outbound adapter)
- `founder_inbox_item` (generated only from real events)
- `founder`, `session`, `job`, `audit_event`, `approval`, `agent_action`,
  `model_request`, `integration_account`, `integration_event`, `connector`
