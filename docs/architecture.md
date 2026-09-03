# QUANTA – Real-Time Intent Signal Engine & CRM Architecture

This document provides a technical blueprint of QUANTA's architecture, API contracts, CRM data flow, and VPS deployment instructions under a dedicated Linux user `/home/quanta/`.

---

## Technical Overview

- **Port Allocation**: `3002` (FastAPI Server + Served Vite PWA App Shell)
- **Domain Mapping**: `quanta.virtusol.com` → `http://127.0.0.1:3002`
- **Database**: SQLite (`db/quanta_crm.db`) for MVP, ORM engineered using SQLAlchemy `declarative_base` for seamless PostgreSQL migration via `DATABASE_URL`.
- **Frontend Stack**: Vite + React, Vanilla Custom CSS Design System (`#0B1020` base, `#2F7BFF` electric blue, `#F5B544` amber gold accents), Lucide Icons, Service Worker for PWA.
- **Backend Stack**: Python FastAPI, Pydantic v2, Slowapi rate limiter, HTTPX for IP geo-resolution.

---

## Repository Structure

```
/Users/datta/QUANTA  (Or /home/quanta/QUANTA on VPS)
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entrypoint (Port 3002)
│   │   ├── crm.py               # Database connection & lead CRUD
│   │   ├── signals.py           # Signal firehose & test ping simulator
│   │   └── models.py            # Pydantic & SQLAlchemy models
│   ├── db/
│   │   └── quanta_crm.db        # SQLite CRM database file
│   ├── requirements.txt
│   └── run.sh
├── frontend/
│   ├── public/
│   │   ├── quanta_logo.svg      # Clean infinity logo
│   │   ├── favicon.svg          # Favicon emblem
│   │   ├── manifest.json        # PWA Web manifest
│   │   └── sw.js                # Service Worker
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── styles/main.css      # B2B custom design system
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── nginx/
│   └── quanta.virtusol.com.conf # Nginx config
├── setup_vps.sh                 # VPS setup script for user 'quanta'
└── docs/
    └── architecture.md
```

---

## Data Flow & API Contracts

### 1. Lead Submission (`POST /api/v1/leads`)
- Client sends JSON payload (`name`, `email`, `company`, `role`, `website`, `country`, `struggle`).
- Backend extracts client IP (`X-Forwarded-For`) and User-Agent.
- `resolve_ip_geo` queries geo-telemetry to resolve city & country.
- `calculate_intent_score` scores the lead from 70 to 99 based on role metrics and problem length.
- Record stored in `leads` table and returned with status HTTP 201.

### 2. CRM Fetch (`GET /api/v1/leads`)
- Returns array of leads sorted by creation timestamp descending.

### 3. Intent Signals Stream (`GET /api/v1/signals`)
- Returns real-time micro-signals firehose for the live stream dashboard.

---

## VPS Deployment Guide (`/home/quanta/`)

To deploy on VPS `91.98.226.5` under isolated user `quanta`:

1. **Create Linux User `quanta`**:
   ```bash
   sudo useradd -m -s /bin/bash quanta
   sudo passwd quanta
   ```

2. **Clone & Setup Codebase**:
   ```bash
   sudo su - quanta
   git clone <repo-url> /home/quanta/QUANTA
   cd /home/quanta/QUANTA/frontend
   npm install && npm run build
   cd /home/quanta/QUANTA/backend
   python3 -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Systemd Service (`/etc/systemd/system/quanta.service`)**:
   ```ini
   [Unit]
   Description=QUANTA Intent Engine & WebApp (Port 3002)
   After=network.target

   [Service]
   User=quanta
   WorkingDirectory=/home/quanta/QUANTA/backend
   ExecStart=/home/quanta/QUANTA/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 3002
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

4. **Nginx & SSL Configuration**:
   ```bash
   sudo cp /home/quanta/QUANTA/nginx/quanta.virtusol.com.conf /etc/nginx/sites-available/
   sudo ln -s /etc/nginx/sites-available/quanta.virtusol.com.conf /etc/nginx/sites-enabled/
   sudo nginx -t && sudo systemctl reload nginx
   sudo certbot --nginx -d quanta.virtusol.com
   ```

---

## Future Feature Modules

1. **PostgreSQL Migration**:
   Update `DATABASE_URL` in `.env`:
   `DATABASE_URL=postgresql://quanta_user:password@localhost:5432/quanta_db`
2. **Slack Bot Integration**:
   Hook into `app/signals.py` via `httpx.post(SLACK_WEBHOOK_URL, json=payload)`.
3. **Chrome Extension Overlay**:
   Consumes `/api/v1/signals` and `/api/v1/leads` via WebSockets for real-time rep pings.
