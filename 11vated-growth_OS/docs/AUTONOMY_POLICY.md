# Autonomy Policy

The default policy is deterministic software in
`growthos/security/permissions.py`.

| Action | Default |
|--------|---------|
| research, analyze_public_website, classify, summarize | AUTO |
| analyze_product, market_hypothesis, opportunity_recommendation | AUTO |
| draft_email, draft_sms, draft_linkedin_message | AUTO |
| update_low_risk_intelligence | AUTO |
| send_prospect_email, send_client_sms | APPROVAL |
| communicate_final_price, discount, commit_scope | APPROVAL |
| promise_delivery_date, send_proposal | APPROVAL |
| publish_linkedin_content, contractual_statement | APPROVAL |
| accept_contract, financial_transfer, credential_change | APPROVAL (dashboard-only) |
| delete_commercial_history, security_configuration | APPROVAL (dashboard-only) |
| circumvent_anti_bot, auto_connection_request, auto_bulk_dm | DENY |
| fake_engagement, bypass_robots_txt | DENY |
| anything not listed | DENY (fail closed) |

Dashboard-only actions are denied outright when the request arrives via SMS or
another non-dashboard channel. Every decision is recorded in `agent_action` and
`audit_event`. Approval requests surface in the Founder Inbox.
