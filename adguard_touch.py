import tkinter as tk
from tkinter import messagebox
import os
import requests
import time
from pathlib import Path
from dotenv import load_dotenv

# Pfad-Management für .env
base_path = Path(__file__).parent
load_dotenv(dotenv_path=base_path / ".env")

ADGUARD_URL = os.getenv("ADGUARD_URL")
ADGUARD_USER = os.getenv("ADGUARD_USER")
ADGUARD_PASS = os.getenv("ADGUARD_PASS")
GUI_PW = os.getenv("GUI_PASSWORD")

class AdGuardKiosk:
    def __init__(self, root):
        self.root = root
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg='#2c3e50')
        self.create_widgets()

    def api_post(self, path, data):
        try:
            requests.post(f"{ADGUARD_URL}{path}", json=data, auth=(ADGUARD_USER, ADGUARD_PASS), timeout=3)
        except:
            messagebox.showerror("Fehler", "AdGuard API Error")

    def restart_service(self):
        os.system(f"sudo ip addr add {os.getenv('STATIC_IP')} dev {os.getenv('INTERFACE')}")
        os.system("sudo systemctl restart AdGuardHome")
        messagebox.showinfo("System", "Service & IP wurden resettet.")

    def show_dhcp_status(self):
        url = ADGUARD_URL
        if url and not url.startswith('http'):
            url = f"http://{url}"
        try:
            r = requests.get(f"{url}/dhcp/status", auth=(ADGUARD_USER, ADGUARD_PASS), timeout=3)
            leases = r.json().get('leases', [])
            last = "\n".join([f"- {l.get('hostname')}" for l in leases[-3:]])
            messagebox.showinfo("DHCP Status", f"Leases aktiv: {len(leases)}\n\nLetzte:\n{last}")
        except Exception as e:
            messagebox.showerror("Fehler", f"API nicht erreichbar\n{str(e)}")

    def toggle_blocking(self):
        # Hier war vermutlich der Fehler - ein try ohne except
        try:
            # Beispiel-Logik für Toggle
            messagebox.showinfo("AdBlock", "Status-Toggle gesendet.")
        except Exception as e:
            messagebox.showerror("Fehler", str(e))

    def create_widgets(self):
        # Fullscreen erzwingen für Kiosk-Mode
        self.root.attributes('-fullscreen', True)
        self.root.geometry("480x320")

        # Stil für große, gut bedienbare Buttons
        btn_style = {"font": ("Arial", 16, "bold"), "fg": "white", "borderwidth": 3}

        # GRID-GEWICHTUNG
        # Spalten 0 und 1 teilen sich die Breite (50/50)
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)
        
        # Zeilen 0 und 1 teilen sich die Höhe der Buttons
        self.root.rowconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        
        # Zeile 2 (Statusbar) bekommt kein Gewicht, damit sie schmal bleibt
        self.root.rowconfigure(2, weight=0)

        # BUTTONS (sticky="nsew" sorgt für die Dehnung in alle Richtungen)
        tk.Button(self.root, text="RESTART\nDHCP/IP", bg="#c0392b",
                  command=self.restart_service, **btn_style).grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        tk.Button(self.root, text="STATUS\nCLIENTS", bg="#2980b9",
                  command=self.show_dhcp_status, **btn_style).grid(row=0, column=1, sticky="nsew", padx=2, pady=2)

        tk.Button(self.root, text="AD-BLOCK\nTOGGLE", bg="#27ae60",
                  command=self.toggle_blocking, **btn_style).grid(row=1, column=0, sticky="nsew", padx=2, pady=2)

        tk.Button(self.root, text="QUIT\nKIOSK", bg="#7f8c8d",
                  command=self.root.destroy, **btn_style).grid(row=1, column=1, sticky="nsew", padx=2, pady=2)

        # STATUSBAR UNTEN
        status_text = f"IP: 192.168.178.145  |  IF: {os.getenv('INTERFACE', 'eth0')}"
        tk.Label(self.root, text=status_text, bg="#2c3e50", fg="#bdc3c7", 
                 font=("Arial", 9), pady=2).grid(row=2, column=0, columnspan=2, sticky="we")

if __name__ == "__main__":
    root = tk.Tk()
    app = AdGuardKiosk(root)
    root.mainloop()

