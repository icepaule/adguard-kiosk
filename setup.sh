#!/bin/bash
# setup.sh - Full Kiosk, Security & Log-Management Deployment
# Project: Captive Portal for Security Exceptions
# Maintainer: IcePaule

echo "🚀 Starte finales System-Setup (Compliance-Grade)..."

# 1. System-Abhängigkeiten installieren
sudo apt update
sudo apt install -y xserver-xorg xinit matchbox-window-manager x11-xserver-utils \
                    unclutter python3-pygame python3-flask python3-requests \
                    python3-dotenv fping python3-pil python3-pil.imagetk logrotate

# 2. Logrotate Konfiguration (SD-Karten Schutz)
echo "💾 Konfiguriere Log-Rotation..."
sudo bash -c "cat <<EOF > /etc/logrotate.d/adguard-kiosk
/home/mpauli/adguard-kiosk/*.log {
    daily
    rotate 7
    missingok
    notifempty
    compress
    delaycompress
    size 10M
    copytruncate
}
EOF"

# 3. Journald Limit setzen (Schutz vor volllaufendem System-Log)
echo "🛡️ Härte System-Journal (50MB Limit)..."
sudo sed -i 's/#SystemMaxUse=/SystemMaxUse=50M/' /etc/systemd/journald.conf
sudo systemctl restart systemd-journald

# 4. Xinit-Konfiguration (Kiosk-Mode)
echo "📺 Konfiguriere X11 Kiosk..."
cat <<EOF > ~/.xinitrc
#!/bin/bash
xset s off
xset -dpms
xset s noblank
unclutter -idle 0.1 -root &
matchbox-window-manager -use_titlebar no &
python3 $(pwd)/adguard_watchdog.py
EOF
chmod +x ~/.xinitrc

# 5. Systemd-Service: Watchdog & GUI
sudo bash -c "cat <<EOF > /etc/systemd/system/adguard-watchdog.service
[Unit]
Description=AdGuard Watchdog & Kiosk UI
After=network-online.target AdGuardHome.service
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=$(pwd)
Environment=DISPLAY=:0
ExecStart=/usr/bin/startx $(pwd)/.xinitrc
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF"

# 6. Systemd-Service: Unlock Dashboard (Captive Portal)
sudo bash -c "cat <<EOF > /etc/systemd/system/adguard-unlock.service
[Unit]
Description=AdGuard 24h Unlock Dashboard (Captive Portal)
After=network.target

[Service]
ExecStart=/usr/bin/python3 $(pwd)/unlock_service.py
WorkingDirectory=$(pwd)
Restart=always
User=mpauli

[Install]
WantedBy=multi-user.target
EOF"

# 7. Dienste aktivieren & aufräumen
sudo systemctl daemon-reload
sudo systemctl enable adguard-watchdog.service
sudo systemctl enable adguard-unlock.service

echo "✅ Setup abgeschlossen!"
echo "👉 Starte die Dienste mit: sudo systemctl start adguard-watchdog adguard-unlock"

