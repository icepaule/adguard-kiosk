import requests
import os
from pathlib import Path
from dotenv import load_dotenv

base_path = Path("/home/mpauli/adguard-kiosk")
load_dotenv(dotenv_path=base_path / ".env")

ADGUARD_URL = os.getenv("ADGUARD_URL")
ADGUARD_AUTH = (os.getenv("ADGUARD_USER"), os.getenv("ADGUARD_PASS"))
KNOWN_MACS_FILE = base_path / "known_macs.txt"

def preseed():
    try:
        r = requests.get(f"{ADGUARD_URL}/dhcp/status", auth=ADGUARD_AUTH, timeout=5)
        if r.status_code == 200:
            leases = r.json().get('leases', [])
            static_leases = r.json().get('static_leases', [])
            
            all_macs = set()
            for l in leases + static_leases:
                if l.get('mac'):
                    all_macs.add(l.get('mac').lower())
            
            with open(KNOWN_MACS_FILE, "w") as f:
                for mac in all_macs:
                    f.write(f"{mac}\n")
            
            print(f"✅ {len(all_macs)} MAC-Adressen erfolgreich vorregistriert.")
    except Exception as e:
        print(f"❌ Fehler: {e}")

if __name__ == "__main__":
    preseed()
