# Discovery Engine

A pluggable engine for public business discovery. LinkedIn is never the only
source, and authenticated scraping/botting is never used.

## Candidate sources

business websites, public company directories, OpenStreetMap/Overpass, public
chamber/business directories where permitted, government/open datasets, public
RSS/news, company press pages, public job postings, public portfolios,
founder-supplied URLs, referrals, Gmail, and the LinkedIn connections export.

## Website reconnaissance

For legitimate public sites: mobile responsiveness, navigation architecture,
conversion paths, calls to action, accessibility signals, performance
indicators, booking/contact flows, visual quality, content structure, broken
links, missing functionality, customer journey, and obvious manual workflows —
each captured as reproducible evidence.

Example: OBSERVATION "booking requires four page transitions" → INFERENCE
"friction may reduce mobile conversion" → HYPOTHESIS "11vatedTech could
redesign the booking acquisition experience". No unsupported revenue claims.

## Ethics & compliance

Respect robots.txt, site terms, rate limits, access controls, and authentication
boundaries. Playwright is used only for ordinary public-web browsing where
automation is permitted. CAPTCHAs and anti-bot protections are never
circumvented. Inability to scrape a site is not permission to bypass it.

## Live source policy (2026-08-21)

- **Overpass/OpenStreetMap:** active, bounded to a maximum 50 km radius; the
  persistent `scout_discovery_cache` prevents identical requests within the
  cache window, and 429/502/503/504 responses use `Retry-After` or capped
  exponential backoff. The public endpoint is a community service, not owned
  infrastructure.
- **Official website audit:** active for bounded public GET requests. It stores
  the URL, timestamp, method, raw source-evidence summary, individual
  `ResearchObservation` rows, truth class, and confidence. It does not infer
  customer loss from visual or technical signals.
- **Founder import, Gmail, and official LinkedIn connection export:** supported
  through existing provenance boundaries. LinkedIn scraping and automated
  actions remain prohibited.
- **Government/open-data and chamber-directory adapters:** roadmap only until
  source terms, attribution, rate limits, and deduplication rules are reviewed.

A discovered organization is an identity record, not a sales opportunity. Only
reconnaissance-backed problem evidence, a claimable Capability Canon entry, a
separate offer, and a provenance-backed contact route can advance the Scout
funnel.
