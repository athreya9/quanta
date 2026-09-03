# QUANTA Workspace Directives & Deployment Memory

## ⚠️ STRICT RULE: PROJECT BOUNDARIES & TARGET VPS
- **Project Scope**: **QUANTA – Real-Time Intent Signal Engine** is a completely independent B2B revenue project. It is **100% unrelated to AegisOptions AI or any trading projects**. Never search, reference, or execute any commands related to Aegis.
- **Forbidden IP**: `91.98.226.5` MUST NEVER BE TOUCHED UNDER ANY CIRCUMSTANCES.
- **Target VPS IP**: **`89.167.84.152`**
- **Target Port**: **`3002`**
- **Domain**: `quanta.virtusol.com`
- **GitHub Repository**: `https://github.com/athreya9/quanta`
- **VPS Linux User**: `quanta`
- **VPS Installation Directory**: `/home/quanta/QUANTA`

## 🛠️ DEPLOYMENT BLUEPRINT (89.167.84.152)
1. **GitHub Repository**: [https://github.com/athreya9/quanta](https://github.com/athreya9/quanta) (Main branch fully pushed with production `dist/` build and FastAPI engine).
2. **Nginx Reverse Proxy**: `/etc/nginx/sites-available/quanta.virtusol.com.conf` mapping `quanta.virtusol.com` -> `http://127.0.0.1:3002`.
3. **Systemd Unit File**: `/etc/systemd/system/quanta.service` running `/home/quanta/QUANTA/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 3002`.
