import time
import requests
import os
import pygame
import threading
from dotenv import load_dotenv

# --- KONFIGURATION ---
load_dotenv()
# AdGuard & Pushover Zugangsdaten aus .env laden
API_URL = "http://localhost:80/control"
try:
    AUTH = (os.getenv('ADGUARD_USER'), os.getenv('ADGUARD_PASS'))
    PUSH_TOKEN = os.getenv('PUSHOVER_TOKEN')
    PUSH_USER = os.getenv('PUSHOVER_USER')
except:
    print("Fehler: .env Datei nicht korrekt geladen.")
    exit()

# DEINE KRITISCHEN FILTER-IDs (Hier eintragen!)
# 11=URLHaus, 44=HaGeZi Threat, 30/18=Phishing, 55=Badware, 71=Rebind
CRITICAL_FILTER_IDS = [11, 44, 30, 18, 55, 71]

# Globale Variablen für Alarm-Status
alert_active = False
alert_info = {"domain": "", "client": ""}
icon_skull = None # Platzhalter für das Bild

# --- PUSHOVER FUNKTION ---
def send_push(message):
    """Sendet eine kritische Warnung per Pushover"""
    try:
        requests.post("https://api.pushover.net/1/messages.json", data={
            "token": PUSH_TOKEN,
            "user": PUSH_USER,
            "message": message,
            "priority": 1, # Hohe Priorität (rot im Handy)
            "sound": "siren" # Sirenen-Sound
        }, timeout=5)
    except Exception as e:
        print(f"Pushover Fehler: {e}")

# --- THREAT MONITOR (Hintergrund-Thread) ---
def check_adguard_threats():
    """Prüft regelmäßig das AdGuard Log auf kritische Blocks"""
    global alert_active, alert_info
    print("🛡️ Threat-Monitor gestartet.")
    while True:
        try:
            # Letzte 15 Anfragen abrufen
            response = requests.get(f"{API_URL}/querylog", auth=AUTH, params={'limit': 15}, timeout=5)
            if response.status_code == 200:
                data = response.json()
                queries = data.get('data', [])
                
                for query in queries:
                    # Prüfen, ob die Anfrage geblockt wurde
                    if query.get('reason') == 'FilteredBlackList':
                        rules = query.get('rules', [])
                        if rules:
                            # Die ID der Filterliste, die zugeschlagen hat
                            f_id = rules[0].get('filter_list_id')
                            
                            # Wenn die ID auf unserer roten Liste steht UND noch kein Alarm aktiv ist
                            if f_id in CRITICAL_FILTER_IDS and not alert_active:
                                domain = query['question']['name']
                                # Client-Name bevorzugen, fallback auf IP
                                client = query.get('client_name') or query.get('client')
                                
                                print(f"!!! KRITISCHER TREFFER: {domain} von {client} (Filter ID: {f_id}) !!!")
                                
                                # Alarm-Daten setzen
                                alert_info = {"domain": domain, "client": client}
                                alert_active = True
                                
                                # Pushover senden
                                send_push(f"🚨 BEDROHUNG BLOCKIERT!\nDomain: {domain}\nGerät: {client}\nFilter-ID: {f_id}")
                                
                                # Timer starten, um Alarm nach 15s zurückzusetzen
                                threading.Timer(15.0, reset_alert).start()
                                break # Schleife abbrechen, ein Alarm reicht erstmal
            
            time.sleep(5) # Alle 5 Sekunden prüfen
            
        except Exception as e:
            print(f"API/Netzwerk Fehler im Monitor: {e}")
            time.sleep(20) # Bei Fehler länger warten

def reset_alert():
    """Setzt den visuellen Alarm zurück"""
    global alert_active
    print("Alarm-Timer abgelaufen. Reset.")
    alert_active = False

# --- GUI / DISPLAY (Main Thread) ---
def draw_gui():
    global icon_skull
    pygame.init()
    
    # Mauszeiger verstecken für Kiosk-Modus
    pygame.mouse.set_visible(False)
    
    # Display einrichten (3.5" Auflösung)
    screen = pygame.display.set_mode((480, 320))
    pygame.display.set_caption("AdGuard Kiosk Defender")
    
    # Schriften laden
    font_big = pygame.font.SysFont("Arial", 36, bold=True)
    font_mid = pygame.font.SysFont("Arial", 22, bold=True)
    font_small = pygame.font.SysFont("Arial", 18)

    # --- TOTENKOPF LADEN ---
    try:
        # Bild laden
        img_raw = pygame.image.load("skull.png")
        # Skalieren auf 100x100 Pixel
        icon_skull = pygame.transform.scale(img_raw, (100, 100))
        print("Skull-Icon erfolgreich geladen.")
    except Exception as e:
        print(f"Warnung: skull.png konnte nicht geladen werden: {e}")
        icon_skull = None # Fallback, falls Bild fehlt

    # Monitor-Thread im Hintergrund starten
    monitor_thread = threading.Thread(target=check_adguard_threats, daemon=True)
    monitor_thread.start()

    print("Display-Schleife gestartet.")
    running = True
    while running:
        # Event-Handling (z.B. um Programm sauber zu beenden)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # --- ZEICHNEN ---
        if alert_active:
            # === ALARM SCREEN (ROT) ===
            screen.fill((180, 0, 0)) # Dunkelrot als Hintergrund
            # Weißer Rahmen
            pygame.draw.rect(screen, (255, 255, 255), (5, 5, 470, 310), 3)
            
            # Totenkopf zeichnen (wenn vorhanden), mittig oben
            if icon_skull:
                # Zentriert: (Bildschirmbreite - Bildbreite) / 2
                screen.blit(icon_skull, (190, 20)) 

            # Warntexte (etwas nach unten verschoben wegen des Icons)
            lbl_warn = font_big.render("MALWARE BLOCKED", True, (255, 255, 255))
            # Text auch zentrieren
            warn_x = (480 - lbl_warn.get_width()) // 2
            screen.blit(lbl_warn, (warn_x, 130))
            
            # Details zur Bedrohung
            domain_short = alert_info['domain'][:35] # Domain kürzen falls zu lang
            lbl_dom = font_mid.render(f"Target: {domain_short}", True, (255, 200, 200))
            lbl_src = font_mid.render(f"Source: {alert_info['client']}", True, (255, 200, 200))
            
            screen.blit(lbl_dom, (30, 180))
            screen.blit(lbl_src, (30, 220))
            
            # Timer-Hinweis unten
            lbl_timer = font_small.render("Closing Alert in 15s...", True, (200, 200, 200))
            screen.blit(lbl_timer, (150, 280))
            
        else:
            # === NORMALER SCREEN (STATUS OK) ===
            screen.fill((30, 30, 30)) # Dunkelgrauer Hintergrund
            
            # Grüner Kreis in der Mitte
            pygame.draw.circle(screen, (0, 100, 0), (240, 160), 90) # Füllung
            pygame.draw.circle(screen, (0, 255, 0), (240, 160), 90, 4) # Heller Rand
            
            status_txt = font_big.render("SYSTEM SECURE", True, (255, 255, 255))
            status_x = (480 - status_txt.get_width()) // 2
            screen.blit(status_txt, (status_x, 135))
            
            sub_txt = font_small.render("Monitoring Active Network Threats", True, (150, 150, 150))
            sub_x = (480 - sub_txt.get_width()) // 2
            screen.blit(sub_txt, (sub_x, 185))

        # Display aktualisieren
        pygame.display.flip()
        # Framerate begrenzen um CPU zu sparen
        time.sleep(0.1)

    print("Beende Programm.")
    pygame.quit()

if __name__ == "__main__":
    # Optional: Kurze Pushover beim Start
    # send_push("🚀 Kiosk-Defender mit grafischer Warnung gestartet.")
    draw_gui()

