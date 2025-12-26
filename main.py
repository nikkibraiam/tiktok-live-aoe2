from flask import Flask, request
from flask_socketio import SocketIO, join_room
import json
import os

app = Flask(__name__)
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading"
)

# ======================
# LOAD GIFT MAP
# ======================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_mvs():
    mvs = {}

    for name in os.listdir(BASE_DIR):
        if name.startswith("MV") and os.path.isdir(name):
            with open(f"{name}/gift_map.json", encoding="utf-8") as f:
                gift_map = {g["gift"]: g["army"] for g in json.load(f)}

            with open(f"{name}/events_rules.json", encoding="utf-8") as f:
                rules = json.load(f)

            mvs[name] = {
                "gift_map": gift_map,
                "rules": rules,
                "like_buffer": 0
            }

    return mvs

MVS = load_mvs()
LIKE_BUFFER = 0

def resolve_mv_for_gift(gift):
    for mv, data in MVS.items():
        army = data["gift_map"].get(gift)
        if army:
            return mv, army
    return None, None

def resolve_mv_for_event(event, key=None):
    for mv, data in MVS.items():
        rules = data["rules"].get(event)
        if not rules:
            continue

        # Caso comment
        if isinstance(rules, dict) and key:
            rule = rules.get(key)
            if rule:
                return mv, rule

        # Caso follow / share
        if key is None and "army" in rules:
            return mv, rules

    return None, None



# ======================
# SOCKET EVENTS
# ======================
@socketio.on("register")
def register(data):
    mv = data.strip()

    if mv not in MVS:
        print(f"❌ MV inválido: {mv}")
        return

    join_room(mv)
    print(f"🤖 Bot registrado en {mv}")

# ======================
# TIKTOK EVENT
# ======================
@app.route("/gift", methods=["POST"])
def gift_event():
    data = request.json
    user = data["user"]
    gift = data["gift"]
    amount = data.get("amount", 1)

    socketio.emit("overlay", {
        "user": user,
        "gift": gift,
        "amount": amount
    })

    mv, army = resolve_mv_for_gift(gift)

    if not mv:
        print(f"⚠️⚠️ Gift sin mapping global: {gift}")
        return {"ok": True}

    socketio.emit("command", {
        "action": army["action"],
        "unit": army["unit"],
        "amount": amount
    }, room=mv)

    print(f"⚔️ {mv} | {user} → {army['action']} {army['unit']} x{amount}")
    return {"ok": True}


@app.route("/comment", methods=["POST"])
def comment_event():
    data = request.json
    comment = data.get("message", "").lower()

    mv, rule = resolve_mv_for_event("comment", comment)

    if not mv:
        return {"ok": True}

    socketio.emit("command", {
        "action": rule["action"],
        "unit": rule["unit"],
        "amount": 1
    }, room=mv)

    print(f"💬 {mv} → {rule['action']} {rule['unit']}")
    return {"ok": True}



@app.route("/like", methods=["POST"])
def like_event():
    data = request.json
    likes = data.get("likes", 0)

    for mv, mv_data in MVS.items():
        rules = mv_data["rules"].get("likes")
        if not rules:
            continue

        mv_data["like_buffer"] += likes
        threshold = rules["threshold"]

        spawned = mv_data["like_buffer"] // threshold
        mv_data["like_buffer"] %= threshold

        if spawned > 0:
            socketio.emit("command", {
                "action": rules["army"]["action"],
                "unit": rules["army"]["unit"],
                "amount": spawned
            }, room=mv)

            print(f"❤️ {mv} → {spawned} unidades")

        break   # 👈 PRIMER MV QUE LO MANEJA

    return {"ok": True}

@app.route("/follow", methods=["POST"])
def follow_event():
    mv, rules = resolve_mv_for_event("follow")
    if not mv:
        return {"ok": True}

    emit_simple_event(mv, "follow")
    print(f"➕ Follow → {mv}")
    return {"ok": True}


@app.route("/share", methods=["POST"])
def share_event():
    mv, rules = resolve_mv_for_event("share")
    if not mv:
        return {"ok": True}

    emit_simple_event(mv, "share")
    print(f"➕ Share → {mv}")
    return {"ok": True}


def emit_simple_event(mv, event):
    rules = MVS[mv]["rules"][event]
    socketio.emit("command", {
        "action": rules["army"]["action"],
        "unit": rules["army"]["unit"],
        "amount": 1
    }, room=mv)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
