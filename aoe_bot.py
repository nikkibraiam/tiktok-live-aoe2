import time
import socketio
from pynput.keyboard import Controller, Key

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
def crear_aldeano():
    print("Seleccionando Town Center (H)")
    press(['h'])
    time.sleep(0.1)

    print("Creando aldeano (C)")
    press(['c'])

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
    data ejemplo:
    {
      "action": "aldeano"
    }
    """
    action = data.get("action")

    print(f"Comando recibido: {action}")

    if action == "aldeano":
        crear_aldeano()

# =========================
# START
# =========================
if __name__ == "__main__":
    print("Bot AoE iniciado")
    print("URL" + SERVER_URL)
    sio.connect(SERVER_URL)
    sio.wait()
