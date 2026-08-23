# Phone Command Plane

The founder can text GrowthOS and get real SMS replies (once SMS hardware
exists). The same commercial context is available across the PWA, Gmail, and
SMS.

## Behavior

- Inbound SMS persists (sender, body, device timestamp, gateway message ID,
  received timestamp) **before** agent processing.
- Dedup by gateway message ID.
- The founder number is the only privileged command source; other numbers are
  contacts/prospects and never receive founder privileges.
- Replies are concise and mobile-optimized; multi-message replies are supported
  but minimized.

## Security boundary

SMS alone never authorizes contract acceptance, large discounts, financial
transfer, credential changes, deleting commercial history, or security
configuration. Those require dashboard/PWA confirmation. Lower-risk approvals
may be configurable by SMS. Every SMS-driven action records an `AgentAction`
and an `AuditEvent`.

## Hardware truth

If no Android device + active SIM exists, the bridge is
`SMS BRIDGE — BLOCKED: compatible gateway hardware/SIM required`. Contract
tests still validate the adapter; an end-to-end PASS is only reported after a
real carrier round-trip.
