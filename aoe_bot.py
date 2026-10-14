import os
import time

import socketio
from pynput.keyboard import Controller, Key

# =========================
# HOTKEY MAPS
# =========================

BUILDINGS = {
    "barracks": [Key.ctrl, 'b'],
    "archery": [Key.ctrl, 'a'],
    "stable": [Key.ctrl, 'l'],
    "siege": [Key.ctrl, 'k'],
    "castle": [Key.ctrl, 'v'],
}

UNITS = {
    # barracks
    "s": 's',  # Campeon
    "e": 'e',  # Albarero
    "r": 'r',  # Lancero
    "g": 'g',  # Guerrero Elite

    # archery
    "a": 'a',  # Ballesta
    "r_arch": 'r', #Guerrillero Elite
    "c": 'c',  # Caballeria Arquero
    "e_arch": 'e', #Artillero

    # stable
    "t": 't',  # Usar
    "n": 'n', #Paladin
    "c_cav": 'c', #Camello

    # siege
    "r_siege": 'r', #Ariete
    "a_siege": 'a', #Onagro
    "n_siege": 'n', #Escorpion
    "c_siege": 'c', #Cañon

    # castle
    "t_castle": 't', 
    "r_castle": 'r', #Lanza Piedras 
    "p_castle": 'p', #Petardo
}


# =========================
# CONFIG
# =========================
SERVER_URL = os.getenv("AOE_SERVER_URL", "http://localhost:5000")
BOT_NAME = os.getenv("AOE_BOT_NAME", "vm1")  # vm1 / vm2 etc

kb = Controller()
sio = socketio.Client()

# =========================
# UTIL
# =========================
def press(keys, delay=0.05):
    """
    keys: lista de teclas, ej ['h'] o [Key.ctrl, '1']
    """
    for k in keys:
        kb.press(k)
    time.sleep(delay)
    for k in reversed(keys):
        kb.release(k)

# =========================
# ACTIONS
# =========================
def producir(building, unit_key, amount=1):
    print(f"{building} -> {unit_key} x{amount}")

    # Seleccionar edificio
    press(BUILDINGS[building])
    time.sleep(0.1)

    # Crear unidades
    for _ in range(amount):
        press([unit_key])
        time.sleep(0.05)

# =========================
# SOCKET EVENTS
# =========================
@sio.event
def connect():
    print(f"Conectado al server como {BOT_NAME}")
    sio.emit("register", {"bot": BOT_NAME})

@sio.event
def disconnect():
    print("Desconectado del server")

@sio.on("command")
def on_command(data):
    """
    Ejemplo:
    {
      "action": "barracks",
      "unit": "g",
      "amount": 5
    }
    """
    action = data.get("action")
    unit = data.get("unit")
    amount = data.get("amount", 1)

    print("Comando recibido:", data)

    if action in BUILDINGS and unit:
        producir(action, unit, amount)


# =========================
# START
# =========================
if __name__ == "__main__":
    print("Bot AoE iniciado")
    print("URL" + SERVER_URL)
    sio.connect(SERVER_URL)
    sio.wait()
