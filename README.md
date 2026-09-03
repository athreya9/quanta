# QUANTA – Real-Time Intent Signal Engine

> *"Intent Happens Fast. QUANTA Happens First."*  
> *"Micro-Signals. Macro-Revenue."*

QUANTA is a mobile-first, production-ready web application and real-time intent signal engine built to capture buyer intent micro-signals, score accounts instantly, and deliver enriched leads directly into its built-in CRM, Slack, and Chrome extensions.

---

## Key Features

- **Mobile-First App Shell**: Responsive design with sticky bottom navigation (Home, Signals, CRM, Settings), PWA readiness, and live alert toasts.
- **Built-In QUANTA CRM**: Automatic lead ingestion with IP address geo-enrichment, user-agent metadata, and dynamic intent scoring.
- **Micro-Signal Firehose**: Real-time signal stream monitoring technographic shifts, executive hires, competitor research, and capital deployment.
- **FastAPI Backend (Port 3002)**: High-performance Python backend with rate-limiting, CORS, and PostgreSQL-ready ORM.
- **Downloadable Branding**: High-resolution, vector infinity logo (`quanta_logo.svg`) with zero watermark or AI branding.
- **Nginx Reverse Proxy Ready**: Configured for `quanta.virtusol.com` -> `http://127.0.0.1:3002` with SSL redirect readiness.

---

## Quick Start (Local Development)

### 1. Run Backend (Port 3002)
```bash
cd backend
chmod +x run.sh
./run.sh
```

### 2. Run Frontend (Port 3000)
```bash
cd frontend
npm install
npm run dev
```

---

## API Endpoints Summary

- `GET /api/v1/health` – Engine health check
- `POST /api/v1/leads` – Ingest lead form & enrich into QUANTA CRM
- `GET /api/v1/leads` – Fetch stored leads from QUANTA CRM
- `GET /api/v1/signals` – Fetch live intent signal firehose
- `POST /api/v1/signals/test-alert` – Trigger test Slack/Chrome alert ping

---

## VPS & Linux User Setup (`/home/quanta/`)

See [docs/architecture.md](file:///Users/datta/QUANTA/docs/architecture.md) for full VPS deployment instructions under Linux user `quanta` on port 3002.
