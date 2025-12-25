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
    # Barracks
    "g": 'g',  # Milicia / Campeón
    "r": 'r',  # Lancero
    "e": 'e',  # Eagle
    "s": 's',  # Espadachín (si aplica)

    # Archery
    "c": 'c',  # Arquero
    "a": 'a',  # Ballesta
    "e_arch": 'e',
    "r_arch": 'r',

    # Stable
    "t": 't',  # Scout
    "c_cav": 'c',
    "n": 'n',

    # Siege
    "r_siege": 'r',
    "c_siege": 'c',
    "a_siege": 'a',
    "n_siege": 'n',

    # Castle
    "r_castle": 'r',
    "t_castle": 't',
    "p_castle": 'p',
}


# =========================
# CONFIG
# =========================
SERVER_URL = "http://192.168.17.1:5000"  # cambia esto
BOT_NAME = "vm1"  # vm1 / vm2 etc

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
