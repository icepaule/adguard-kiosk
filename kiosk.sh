#!/bin/bash
# Cursor verstecken
unclutter -idle 0.1 -root &

# Bildschirmschoner und Energiesparen initial deaktivieren
xset s off
xset s noblank
xset -dpms

# Fenstermanager starten (erzwingt Vollbild für Python)
matchbox-window-manager -use_titlebar no &

# Dein Python Skript starten
python3 /home/mpauli/adguard_touch.py

