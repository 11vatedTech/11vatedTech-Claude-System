# FREE_RUNTIME_POLICY

GrowthOS must refuse to silently activate a billable dependency. The machine-
readable policy is [`FREE_RUNTIME_POLICY.json`](../FREE_RUNTIME_POLICY.json);
the `CostGuard` (`growthos/security/cost_guard.py`) enforces it.

## Rules

1. Core operation requires **no** recurring paid AI/API subscription.
2. Local AI runs on Ollama; cloud inference is never silently enabled.
3. A connector whose policy `allowed` is `false` surfaces
   `BLOCKED_BY_FREE_RUNTIME_POLICY` with an explanation.
4. OAuth credentials for our own accounts (Gmail, LinkedIn) are allowed; they
   are not substitutes for paid AI/API infrastructure.
5. Unknown connectors are blocked by default (fail closed).

## Connector registry

| Provider | Billing | Allowed |
|----------|---------|---------|
| ollama | open | yes |
| postgresql | open | yes |
| gmail_api | free tier (Google quotas) | yes |
| linkedin_api | credential only (official APIs) | yes |
| android_sms_gateway | open (carrier SIM is the transport) | yes |
| tailscale | free tier | yes |
| twilio / vonage / messagebird / sendgrid | billable | **no** |

Every connector record in `connector` carries `free_open_status`, `billing`,
`known_limit`, `billing_possibility`, `policy_allowed`, and
`last_policy_verification`.
