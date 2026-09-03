#!/bin/bash
# VPS Setup Automation Script for QUANTA
# Run as root or user with sudo access

set -e

echo "=== QUANTA Deployment Setup ==="

# 1. Create quanta user if not exists
if ! id "quanta" &>/dev/null; then
    echo "Creating linux user 'quanta'..."
    sudo useradd -m -s /bin/bash quanta
fi

# 2. Setup Systemd Service
echo "Creating systemd service /etc/systemd/system/quanta.service..."
cat << 'EOF' | sudo tee /etc/systemd/system/quanta.service
[Unit]
Description=QUANTA Intent Engine & WebApp (Port 3002)
After=network.target

[Service]
User=quanta
WorkingDirectory=/home/quanta/QUANTA/backend
ExecStart=/home/quanta/QUANTA/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 3002
Restart=always
Environment=PORT=3002

[Install]
WantedBy=multi-user.target
EOF

# 3. Reload systemd
sudo systemctl daemon-reload
echo "QUANTA systemd service created successfully."
echo "Deploy code to /home/quanta/QUANTA and run: sudo systemctl enable --now quanta"
