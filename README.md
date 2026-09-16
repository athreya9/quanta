# QUANTA – Intent Signal Engine & CRM

QUANTA is a mobile-first web app and CRM for capturing buyer intent signals and
inbound leads. As of this pass, the data pipeline is honest end-to-end: **every
record in the CRM either came from a real visitor submission, a real public
API (Greenhouse/Lever job boards, Reddit/Upwork RSS), or a LinkedIn profile a
person manually added and the system verified live.** Nothing is
auto-generated, guessed, or seeded - if a source has no real data, the
corresponding field/signal is simply empty rather than filled with a
plausible-looking placeholder.

---

## What's real right now

- **Inbound lead capture** (`POST /api/v1/leads`): real visitor-submitted form data, real IP→geo lookup (ipapi.co), a transparent scoring heuristic (no artificial floor).
- **LinkedIn ICP tracker**: profiles are added manually with a real URL, which is verified live via HTTP before being saved. No synthetic executive database.
- **QEIC crawler**: polls real public Greenhouse/Lever job board APIs for a watchlist of domains every 10 minutes. Only stores a signal when real job postings were found - no fabricated funding rounds, pricing telemetry, or contact info.
- **Outsourcing crawler**: pulls real `[Hiring]` posts from Reddit r/forhire and Upwork's public RSS feeds.
- **Slack alerts**: real webhook delivery, only fires for non-demo, high-scoring, non-duplicate signals.
- **Chrome extension**: silently detects when a visitor is on a LinkedIn/Greenhouse/Indeed jobs page and reports that as telemetry (not published to the Chrome Web Store yet).

## What's NOT real yet (by design, not by accident)

- **Company enrichment** (tech stack, funding signals, hiring velocity beyond job titles) requires a `HUNTER_API_KEY` and/or `CLEARBIT_API_KEY`. Without one configured, `enrichment_status` reports `NO_EXTERNAL_DATA_AVAILABLE` instead of guessing.
- **Pricing-page dwell time / multi-IP clustering**: only exists if you actually instrument your own site with the extension/pixel and it reports real telemetry. The crawler cannot observe this from outside.
- **Email verification** checks MX records only (does the domain accept mail) - it does not confirm a specific mailbox exists. Labeled `MX_RECORD_FOUND`/`NO_MX_RECORD`, never "deliverable."

---

## Quick Start (Local Development)

### 1. Run Backend (Port 3002)
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
./run.sh
```

### 2. Run Frontend (Port 3000)
```bash
cd frontend
npm install
npm run dev
```

Optional `.env` (see `.env.example`) to enable real enrichment/alerts:
```
SLACK_WEBHOOK_URL=...
HUNTER_API_KEY=...
CLEARBIT_API_KEY=...
```

---

## API Endpoints Summary

- `GET /api/v1/health` – Engine health check
- `POST /api/v1/leads` – Ingest a real lead submission into the CRM
- `GET /api/v1/leads` – Fetch stored leads
- `GET /api/v1/linkedin/profiles` / `POST /api/v1/linkedin/profiles` – List / manually add a real, URL-verified LinkedIn profile
- `GET /api/v1/signals` – Fetch real ingested signals
- `POST /api/v1/crawler/run` – Trigger a QEIC job-board crawl pass
- `POST /api/v1/crawler/outsourcing` – Trigger a Reddit/Upwork RSS crawl pass
- `POST /api/v1/signals/test-alert` – Send a clearly-labeled test Slack ping (uses a "Demo Prospect" placeholder, not real data)

---

## VPS & Linux User Setup (`/home/quanta/`)

See [docs/architecture.md](docs/architecture.md) for VPS deployment instructions under Linux user `quanta` on port 3002.
