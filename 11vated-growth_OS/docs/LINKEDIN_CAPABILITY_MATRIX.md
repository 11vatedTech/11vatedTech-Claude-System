# LinkedIn Capability Matrix

A capability is only claimed IMPLEMENTED when real OAuth grants prove it.

| Capability | Official API | Permission | Access Granted | Implemented | Human Assisted | Unavailable | Evidence |
|-----------|--------------|------------|----------------|-------------|----------------|-------------|----------|
| Sign In with LinkedIn (OpenID Connect) | Yes | r_liteprofile / r_emailaddress | AWAITING | Adapter | — | — | `integrations/linkedin.py` |
| Organization Page publishing | Yes (with approval) | w_organization_social | NOT GRANTED | — | Yes (founder) | — | approval required |
| Connections archive import | Yes (data export) | founder download | AWAITING | CSV importer | — | — | unit-tested import |
| Automated connection requests | No | N/A | — | — | Yes (founder) | — | prohibited automation |
| Bulk direct messages | No | N/A | — | — | Yes (founder) | — | prohibited automation |
| Authenticated page scraping | No | N/A | — | — | — | Unavailable | prohibited |
| Fake engagement / likes/comments | No | N/A | — | — | — | Unavailable | prohibited |
