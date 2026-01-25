import os, time, subprocess, requests
from pathlib import Path
from dotenv import load_dotenv

# 1. Pfade & Laden
base_path = Path("/home/mpauli/adguard-kiosk")
load_dotenv(dotenv_path=base_path / ".env")

# 2. Funktionen definieren
def get_active_interface():
    cmd = "ip route get 1.1.1.1 | grep -oP 'dev \K\S+'"
    try:
        return subprocess.check_output(cmd, shell=True).decode().strip()
    except:
        return os.getenv("INTERFACE") or "enxb827eb31260b"

def send_push(message):
    try:
        requests.post("https://api.pushover.net/1/messages.json", data={
            "token": os.getenv("PUSHOVER_TOKEN"), 
            "user": os.getenv("PUSHOVER_USER"), 
            "message": message, 
            "title": "AdGuard Watchdog"
        }, timeout=5)
    except: pass

# 3. Variablen initialisieren
IFACE = get_active_interface()
STATIC_IP = os.getenv("STATIC_IP") or "192.168.178.145/24"
ADGUARD_URL = os.getenv("ADGUARD_URL") or "http://127.0.0.1/control"
ADGUARD_AUTH = (os.getenv("ADGUARD_USER"), os.getenv("ADGUARD_PASS"))
KNOWN_MACS_FILE = base_path / "known_macs.txt"

KNOWN_MACS_FILE = base_path / "known_macs.txt"

def check_logic():
    # ... (IP Check bleibt gleich)

    # DHCP Check für neue Geräte
    try:
        r = requests.get(f"{ADGUARD_URL}/dhcp/status", auth=ADGUARD_AUTH, timeout=5)
        if r.status_code == 200:
            leases = r.json().get('leases', [])
            
            # Bekannte MACs laden
            if not KNOWN_MACS_FILE.exists():
                KNOWN_MACS_FILE.touch()
            with open(KNOWN_MACS_FILE, "r") as f:
                known_macs = f.read().splitlines()

            for l in leases:
                mac = l.get('mac')
                if mac and mac not in known_macs:
                    send_push(f"📱 Neues Gerät: {l.get('hostname')} ({mac})")
                    with open(KNOWN_MACS_FILE, "a") as f:
                        f.write(f"{mac}\n")
    except:
        pass

# 4. Hauptprogramm
if __name__ == "__main__":
    # Einmalige Meldung beim Start/Reboot
    time.sleep(10) # Kurz warten, bis das Netzwerk sicher da ist
    send_push("🚀 AdGuard System wurde neu gestartet. Watchdog ist aktiv!")
    
    while True:
        try:
            check_logic()
        except Exception as e:
            print(f"Fehler im Loop: {e}")
        time.sleep(60)

