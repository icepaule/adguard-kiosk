import time
import requests
import os
import threading
from flask import Flask, request, render_template_string
from dotenv import load_dotenv

# Konfiguration
load_dotenv()
GUI_PASSWORD = os.getenv('GUI_PASSWORD')
AUTH = (os.getenv('ADGUARD_USER'), os.getenv('ADGUARD_PASS'))
PUSH_TOKEN = os.getenv('PUSHOVER_TOKEN')
PUSH_USER = os.getenv('PUSHOVER_USER')

ADGUARD_BASE_URL = "http://localhost:80/control/filtering"

app = Flask(__name__)

def send_push(message):
    try:
        requests.post("https://api.pushover.net/1/messages.json", data={
            "token": PUSH_TOKEN,
            "user": PUSH_USER,
            "message": message,
            "priority": 0
        }, timeout=5)
    except:
        pass

def remove_rule_later(domain):
    """Löscht die Regel nach 24 Stunden (86400 Sekunden)"""
    print(f"⏰ Timer gestartet: {domain} wird in 24h wieder gesperrt.")
    time.sleep(86400)
    try:
        # Aktuelle Regeln abrufen
        resp = requests.get(f"{ADGUARD_BASE_URL}/status", auth=AUTH)
        if resp.status_code == 200:
            rules = resp.json().get('user_rules', [])
            target = f"@@||{domain}^$important"
            if target in rules:
                rules.remove(target)
                requests.post(f"{ADGUARD_BASE_URL}/set_rules", auth=AUTH, json={"rules": rules})
                print(f"🔒 24h abgelaufen: {domain} ist wieder im Filter.")
                send_push(f"🔒 Zeitlimit abgelaufen: {domain} ist wieder gesperrt.")
    except Exception as e:
        print(f"Fehler beim Aufräumen: {e}")

@app.route('/', methods=['GET', 'POST'])
def index():
    msg = ""
    client_ip = request.remote_addr
    
    if request.method == 'POST':
        domain = request.form.get('domain').strip().lower()
        password = request.form.get('password')
        
        if password == GUI_PASSWORD:
            try:
                # 1. Aktuelle Regeln holen
                resp = requests.get(f"{ADGUARD_BASE_URL}/status", auth=AUTH)
                rules = resp.json().get('user_rules', [])
                
                # 2. Neue Regel hinzufügen
                new_rule = f"@@||{domain}^$important"
                if new_rule not in rules:
                    rules.append(new_rule)
                    # 3. Regeln zurückschreiben
                    set_resp = requests.post(f"{ADGUARD_BASE_URL}/set_rules", auth=AUTH, json={"rules": rules})
                    
                    if set_resp.status_code == 200:
                        msg = f"✅ Freigabe für {domain} erfolgreich (24h aktiv)!"
                        send_push(f"🔓 UNLOCK: {domain}\nQuelle: {client_ip}\nDauer: 24h")
                        # Timer in separatem Thread starten
                        threading.Thread(target=remove_rule_later, args=(domain,), daemon=True).start()
                    else:
                        msg = "❌ Fehler bei der Kommunikation mit AdGuard."
                else:
                    msg = "ℹ️ Domain ist bereits freigeschaltet."
            except Exception as e:
                msg = f"❌ Systemfehler: {e}"
        else:
            msg = "❌ Falsches Passwort!"
            send_push(f"⚠️ Fehlgeschlagener Unlock-Versuch!\nIP: {client_ip}\nDomain: {domain}")

    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: sans-serif; background: #1a1a1a; color: white; text-align: center; padding: 50px 20px; }
                input { width: 100%; padding: 12px; margin: 10px 0; border-radius: 5px; border: none; box-sizing: border-box; }
                button { background: #008cff; color: white; border: none; padding: 15px; width: 100%; border-radius: 5px; font-weight: bold; }
                .card { background: #2a2a2a; padding: 20px; border-radius: 10px; max-width: 400px; margin: auto; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
                .msg { color: #ffcc00; margin-top: 20px; }
            </style>
        </head>
        <body>
            <div class="card">
                <h2>🛡️ Domain Unlock</h2>
                <p>IP: {{ client_ip }}</p>
                <form method="POST">
                    <input type="text" name="domain" placeholder="z.B. youtube.com" required>
                    <input type="password" name="password" placeholder="GUI Passwort" required>
                    <button type="submit">FÜR 24H FREISCHALTEN</button>
                </form>
                {% if msg %}<div class="msg">{{ msg }}</div>{% endif %}
            </div>
        </body>
        </html>
    ''', msg=msg, client_ip=client_ip)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

