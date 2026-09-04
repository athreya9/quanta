#!/bin/bash
# QUANTA Automated VPS Deployment Script for 89.167.84.152

set -e
echo "=== QUANTA Deployment Automation Started ==="

# 1. Add SSH Key & Enable Password Authentication
mkdir -p /root/.ssh && chmod 700 /root/.ssh
cat << 'EOF' >> /root/.ssh/authorized_keys
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFZHjknXtp2hCwyzxhzvqYuO9Tg0s2whCPUlMxgdAM1o kvnkelly9@gmail.com
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDUc71wFkOK6ztwmnlD3h9P+QrBd9Zb2MEAo1NY1L7dMTK92OZGrPDr+cBzpzi0wVdPxIyfx7M0TI7oCC22qC46ITFqOEVgQKQxlKQ3UAFS7q0t7jx/6RegIuhkfmQzysmo2NLXT92f496SXa1vziHYcRPSMQ30mee+bTfL67qh6iMZBlTHpIsjJoIs6ulkzEYwyTYlsB+kYavGkdZBZ3rb1oNuhfXazxzf/9OzmGf8aOjptk+W89Tt0yLP3zkiAEAEBt4IOQ1mH5vII7Q4TS4BpEp4SuycRzx9Qfspwjlf82d7IsJbAtcvHbGE06vkcKiu488iF2YZ43qLsZ+1tv38xyGEU7RFSU1LtCZjmkNyA5aotD1ab4Zr2z30FiVd/TUG+plodAd5wnS4kX5osahr5+v1+8zF7MzqerPKBQ6uxGoU3TkX7A9OAPbB4TNUVzOAPsSLPLxk29lVmBvghrEtrVgjkdJMYye1FhdHfOXeOjjuPwLxROR7+Kg1EfcIa1UK8UiON05cKQ6XCZTHXorOzyfVWvtJTjD2JaM+U51JatOvShCrBTTqMF68bIogjKYZEHBAT2SUruWox8+Bj9w2tJ7hd8nitsZ/1v72E5L0LYeCbQPhFnVPUFaiXOM3suKL/9pbQHTwxvrPGRvkw2ybMdzDbI+5I+yczKu0zNlt2w== datta@Dattas-MacBook-Air.local
EOF
chmod 600 /root/.ssh/authorized_keys

# 2. Create linux user quanta if not present
id -u quanta &>/dev/null || useradd -m -s /bin/bash quanta

# 3. Setup codebase
rm -rf /home/quanta/QUANTA
git clone https://github.com/athreya9/quanta.git /home/quanta/QUANTA
chown -R quanta:quanta /home/quanta/QUANTA

# 4. Setup Python Virtual Environment
cd /home/quanta/QUANTA/backend
python3 -m venv --without-pip venv || python3 -m venv venv
if [ -f "get-pip.py" ]; then
    ./venv/bin/python get-pip.py || true
fi
./venv/bin/pip install --upgrade pip || true
./venv/bin/pip install -r requirements.txt

# 5. Setup Systemd Service for Port 3002
cat << 'EOF' > /etc/systemd/system/quanta.service
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

# 6. Setup Nginx Reverse Proxy for quanta.virtusol.com
cat << 'EOF' > /etc/nginx/sites-available/quanta.virtusol.com.conf
server {
    listen 80;
    server_name quanta.virtusol.com;

    location / {
        proxy_pass http://127.0.0.1:3002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /assets/ {
        proxy_pass http://127.0.0.1:3002/assets/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
}
EOF

ln -sf /etc/nginx/sites-available/quanta.virtusol.com.conf /etc/nginx/sites-enabled/

# 7. Reload & start services
systemctl daemon-reload
systemctl restart quanta
systemctl enable quanta
nginx -t && systemctl reload nginx
service ssh restart || systemctl restart sshd || true

echo "=== QUANTA Deployment Completed Successfully on Port 3002 ==="
