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

def load_VMS():
    VMS = {}

    for name in os.listdir(BASE_DIR):
        if name.startswith("vm") and os.path.isdir(name):
            with open(f"{name}/gift_map.json", encoding="utf-8") as f:
                gift_map = {g["gift"]: g["army"] for g in json.load(f)}

            with open(f"{name}/events_rules.json", encoding="utf-8") as f:
                rules = json.load(f)

            VMS[name] = {
                "gift_map": gift_map,
                "rules": rules,
                "like_buffer": 0
            }

    print(VMS)
    return VMS

VMS = load_VMS()
LIKE_BUFFER = 0

def resolve_vm_for_gift(gift):
    for vm, data in VMS.items():
        army = data["gift_map"].get(gift)
        if army:
            return vm, army
    return None, None

def resolve_vm_for_event(event, key=None):
    for vm, data in VMS.items():
        rules = data["rules"].get(event)
        if not rules:
            continue

        # Caso comment
        if isinstance(rules, dict) and key:
            rule = rules.get(key)
            if rule:
                return vm, rule

        # Caso follow / share
        if key is None and "army" in rules:
            return vm, rules

    return None, None



# ======================
# SOCKET EVENTS
# ======================
@socketio.on("register")
def register(data):
    # data = {"bot": "vm1"}
    vm = None

    if isinstance(data, dict):
        vm = data.get("vm") or data.get("bot")
    else:
        vm = str(data).strip()

    if not vm or vm not in VMS:
        print(f"❌ vm inválido en register: {data}")
        return

    print(f"🤖 Bot registrado en {vm}")
    join_room(vm)

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

    vm, army = resolve_vm_for_gift(gift)

    if not vm:
        print(f"⚠️⚠️ Gift sin mapping global: {gift}")
        return {"ok": True}

    socketio.emit("command", {
        "action": army["action"],
        "unit": army["unit"],
        "amount": amount
    }, room=vm)

    print(f"⚔️ {vm} | {user} → {army['action']} {army['unit']} x{amount}")
    return {"ok": True}


@app.route("/comment", methods=["POST"])
def comment_event():
    data = request.json
    comment = data.get("message", "").lower()

    vm, rule = resolve_vm_for_event("comment", comment)

    if not vm:
        return {"ok": True}

    socketio.emit("command", {
        "action": rule["action"],
        "unit": rule["unit"],
        "amount": 1
    }, room=vm)

    print(f"💬 {vm} → {rule['action']} {rule['unit']}")
    return {"ok": True}



@app.route("/like", methods=["POST"])
def like_event():
    data = request.json
    likes = data.get("likes", 0)

    for vm, vm_data in VMS.items():
        rules = vm_data["rules"].get("likes")
        if not rules:
            continue

        vm_data["like_buffer"] += likes
        threshold = rules["threshold"]

        spawned = vm_data["like_buffer"] // threshold
        vm_data["like_buffer"] %= threshold

        if spawned > 0:
            socketio.emit("command", {
                "action": rules["army"]["action"],
                "unit": rules["army"]["unit"],
                "amount": spawned
            }, room=vm)

            print(f"❤️ {vm} → {spawned} unidades")

        break   # 👈 PRIMER vm QUE LO MANEJA

    return {"ok": True}

@app.route("/follow", methods=["POST"])
def follow_event():
    vm, rules = resolve_vm_for_event("follow")
    if not vm:
        return {"ok": True}

    emit_simple_event(vm, "follow")
    print(f"➕ Follow → {vm}")
    return {"ok": True}


@app.route("/share", methods=["POST"])
def share_event():
    vm, rules = resolve_vm_for_event("share")
    if not vm:
        return {"ok": True}

    emit_simple_event(vm, "share")
    print(f"➕ Share → {vm}")
    return {"ok": True}


def emit_simple_event(vm, event):
    rules = VMS[vm]["rules"][event]
    socketio.emit("command", {
        "action": rules["army"]["action"],
        "unit": rules["army"]["unit"],
        "amount": 1
    }, room=vm)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
