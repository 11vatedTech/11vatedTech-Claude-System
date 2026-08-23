# SMS Gateway Setup

Status: **BLOCKED — compatible gateway hardware/SIM required**

## Hardware truth

Real two-way SMS requires an Android device with SMS capability and an active
SIM acting as the modem. If none is available, SMS is reported BLOCKED — never
"operational".

## Preferred architecture

```
Founder phone → carrier SMS → Android SMS Gateway device + SIM
                              → authenticated local/private API
                              → GrowthOS SMS bridge → Growth Intelligence Agent
```

An iPhone founder simply texts the Android gateway's number. No Twilio.

## Implementation

- `integrations/sms.py` — contract logic: normalize/classify sender, founder
  number allowlist, dedup by gateway message ID, reply composition.
- `integrations/sms_gateway.py` — adapter for the self-hosted
  `capcom6/android-sms-gateway` server (Bearer-token API key in OS keychain).

## Founder actions required

1. Provision an Android device + active SIM.
2. Install and configure the gateway app + self-hosted server on the private
   network only.
3. Store the gateway API key via `growthos setup sms`.
4. Allowlist the founder number.

## Acceptance (not yet claimed)

A real carrier SMS is sent and received end-to-end: founder → gateway →
GrowthOS persist → agent process → real reply → founder receives it. No mocked
gateway counts as PASS.
