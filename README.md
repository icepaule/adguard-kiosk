# AdGuard Home Kiosk & Watchdog 🛡️📺

Ein robustes Überwachungssystem für den Raspberry Pi mit 3.5" Touch-Display.

### Features
* **Touch GUI:** 4-Button Steuerung für AdGuard-Dienste direkt am Display.
* **Network Watchdog:** Überwacht die statische IP (.145) und repariert das Interface bei Ausfall.
* **Pushover Alarme:** Benachrichtigung bei IP-Verlust oder neuen/unbekannten Geräten im Netzwerk.
* **Smart Detection:** Erkennt automatisch das aktive Netzwerk-Interface (z.B. `enxb82...`).

### Installation
1. Repository klonen
2. `.env` basierend auf `.env.example` erstellen
3. `python3 preseed_macs.py` ausführen
4. `sudo bash setup.sh`
