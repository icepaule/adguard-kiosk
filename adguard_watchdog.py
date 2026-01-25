import time
import requests
import os
import pygame
import threading
from dotenv import load_dotenv

# Konfiguration laden
load_dotenv()
API_URL = "http://localhost:80/control"
AUTH = (os.getenv('ADGUARD_USER'), os.getenv('ADGUARD_PASS'))
PUSH_TOKEN = os.getenv('PUSHOVER_TOKEN')
PUSH_USER = os.getenv('PUSHOVER_USER')

# DEINE KRITISCHEN FILTER-IDs (Extrahiert aus deinen URLs)
CRITICAL_FILTER_IDS = [11, 44, 30, 18, 55, 71, 10]

# Globale Variablen
alert_active = False
alert_info = {"domain": "", "client": ""}

def send_push(message):
    try:
        requests.post("https://api.pushover.net/1/messages.json", data={
            "token": PUSH_TOKEN,
            "user": PUSH_USER,
            "message": message,
            "priority": 1,
            "sound": "siren"
        })
    except:
        pass

def check_adguard_threats():
    global alert_active, alert_info
    while True:
        try:
            # Letzte Anfragen abrufen
            response = requests.get(f"{API_URL}/querylog", auth=AUTH, params={'limit': 10})
            if response.status_code == 200:
                queries = response.json().get('data', [])
                for query in queries:
                    # Wenn geblockt durch Filterliste
                    if query.get('reason') == 'FilteredBlackList':
                        rules = query.get('rules', [])
                        if rules:
                            f_id = rules[0].get('filter_list_id')
                            
                            # Prüfen ob ID in unserer "Roten Liste"
                            if f_id in CRITICAL_FILTER_IDS and not alert_active:
                                domain = query['question']['name']
                                client = query.get('client_name') or query.get('client')
                                
                                alert_info = {"domain": domain, "client": client}
                                alert_active = True
                                
                                send_push(f"🚨 BEDROHUNG BLOCKIERT!\nDomain: {domain}\nGerät: {client}")
                                
                                # Timer für 15 Sekunden
                                threading.Timer(15.0, reset_alert).start()
                                break 
            time.sleep(5) # Schneller Check alle 5 Sekunden
        except Exception as e:
            print(f"Fehler: {e}")
            time.sleep(20)

def reset_alert():
    global alert_active
    alert_active = False

def draw_gui():
    pygame.init()
    # Cursor verstecken für Kiosk-Mode
    pygame.mouse.set_visible(False)
    screen = pygame.display.set_mode((480, 320))
    font_big = pygame.font.SysFont("Arial", 35, bold=True)
    font_mid = pygame.font.SysFont("Arial", 24, bold=True)
    font_small = pygame.font.SysFont("Arial", 18)

    # Threat-Monitor Thread starten
    threading.Thread(target=check_adguard_threats, daemon=True).start()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if alert_active:
            # ALARM SCREEN (ROT)
            screen.fill((200, 0, 0))
            pygame.draw.rect(screen, (255, 255, 255), (10, 10, 460, 300), 4)
            
            lbl_warn = font_big.render("MALWARE BLOCKED", True, (255, 255, 255))
            lbl_dom = font_mid.render(f"Target: {alert_info['domain'][:30]}", True, (255, 255, 255))
            lbl_src = font_mid.render(f"From: {alert_info['client']}", True, (255, 255, 255))
            lbl_timer = font_small.render("Closing Alert in 15s...", True, (255, 200, 200))

            screen.blit(lbl_warn, (65, 60))
            screen.blit(lbl_dom, (30, 140))
            screen.blit(lbl_src, (30, 190))
            screen.blit(lbl_timer, (150, 270))
        else:
            # NORMALER SCREEN (DUNKELGRÜN/GRAU)
            screen.fill((20, 20, 20))
            # Hier deine Buttons einfügen
            pygame.draw.circle(screen, (0, 150, 0), (240, 160), 80, 5)
            status_txt = font_mid.render("SYSTEM PROTECTED", True, (0, 200, 0))
            screen.blit(status_txt, (140, 150))

        pygame.display.flip()
        time.sleep(0.1)

if __name__ == "__main__":
    draw_gui()

