#!/bin/bash
# setup.sh für IcePaule/adguard-kiosk

echo "🔧 Installiere Abhängigkeiten..."
sudo apt update
sudo apt install -y python3-tk python3-requests python3-pil python3-pil.imagetk \
                    python3-dotenv fping xserver-xorg xinit matchbox-window-manager \
                    x11-xserver-utils unclutter

# Systemd Service anlegen
sudo bash -c "cat <<EOF > /etc/systemd/system/adguard-watchdog.service
[Unit]
Description=AdGuard Watchdog
After=network.target AdGuardHome.service

[Service]
ExecStart=/usr/bin/python3 /home/mpauli/adguard-kiosk/adguard_watchdog.py
WorkingDirectory=/home/mpauli/adguard-kiosk
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF"

# X-Start Konfiguration
cat <<EOF > ~/.xinitrc
#!/bin/bash
xset s off -dpms
matchbox-window-manager -use_titlebar no &
python3 /home/mpauli/adguard-kiosk/adguard_touch.py
EOF
chmod +x ~/.xinitrc

sudo systemctl daemon-reload
sudo systemctl enable adguard-watchdog.service

echo "✅ Fertig. Bitte .env anpassen und mit 'startx' oder Reboot testen."

