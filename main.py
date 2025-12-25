from flask import Flask, request
from flask_socketio import SocketIO
import json

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# ======================
# LOAD GIFT MAP
# ======================
def load_gift_map():
    with open("gift_map.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return {item["gift"]: item["army"] for item in data}

GIFT_MAP = load_gift_map()

def load_event_rules():
    with open("events_rules.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

EVENT_RULES = load_event_rules()
LIKE_BUFFER = 0

# ======================
# SOCKET EVENTS
# ======================
@socketio.on("register")
def register(data):
    print("🤖 Bot registrado:", data)

# ======================
# TIKTOK EVENT
# ======================
@app.route("/event", methods=["POST"])
def event():
    data = request.json

    print("📥 Recibido:", json.dumps(data, ensure_ascii=False))

    user = data["user"]
    gift = data["gift"]
    amount = data.get("amount", 1)

    # Overlay siempre
    socketio.emit("overlay", {
        "user": user,
        "gift": gift,
        "amount": amount
    })

    # Resolver acción
    army = GIFT_MAP.get(gift)

    if not army:
        print(f"⚠️ Gift sin mapping: {gift}")
        return {"ok": True}

    # Emitir comando al BOT
    socketio.emit("command", {
        "action": army["action"],
        "unit": army["unit"],
        "amount": amount
    })

    print(f"⚔️ {user} → {army['action']} {army['unit']} x{amount}")

    return {"ok": True}

@app.route("/like", methods=["POST"])
def like_event():
    global LIKE_BUFFER

    data = request.json
    likes = data.get("likes", 0)

    LIKE_BUFFER += likes

    rules = EVENT_RULES["likes"]
    threshold = rules["threshold"]

    spawned = LIKE_BUFFER // threshold
    LIKE_BUFFER = LIKE_BUFFER % threshold

    if spawned > 0:
        socketio.emit("command", {
            "action": rules["army"]["action"],
            "unit": rules["army"]["unit"],
            "amount": spawned
        })

        print(f"❤️ Likes → {spawned} unidades")

    return {"ok": True}

@app.route("/follow", methods=["POST"])
def follow_event():
    rules = EVENT_RULES["follow"]

    socketio.emit("command", {
        "action": rules["army"]["action"],
        "unit": rules["army"]["unit"],
        "amount": 1
    })

    print("➕ Nuevo follow → unidad siege")

    return {"ok": True}


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
