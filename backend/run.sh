#!/bin/bash
echo "Starting QUANTA Backend Engine on Port 3002..."
cd "$(dirname "$0")"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt
export PORT=3002
uvicorn app.main:app --host 0.0.0.0 --port 3002 --reload
