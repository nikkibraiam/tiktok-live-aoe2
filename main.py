from flask import Flask, request, send_from_directory
from flask_socketio import SocketIO, join_room
import json
import os

app = Flask(__name__)
socketio = SocketIO(
    app,
    cors_allowed_origins="*"
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
                "like_buffer": {}  # ✅ DICT por usuario
            }

    return VMS


VMS = load_VMS()

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

@app.after_request
def no_cache(resp):
    resp.headers["Cache-Control"] = "no-store"
    return resp

@app.route("/overlay")
def overlay_index():
    return send_from_directory(
        os.path.join(BASE_DIR, "overlay"),
        "index.html"
    )


@app.route("/overlay/<path:filename>")
def overlay_files(filename):
    return send_from_directory(
        os.path.join(BASE_DIR, "overlay"),
        filename
    )

@app.route("/vm1/<path:filename>")
def vm1_files(filename):
    return send_from_directory(
        os.path.join(BASE_DIR, "vm1"),
        filename
    )

@app.route("/vm2/<path:filename>")
def vm2_files(filename):
    return send_from_directory(
        os.path.join(BASE_DIR, "vm2"),
        filename
    )

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
    avatar = data.get("avatar")
    diamonds = data.get("diamonds")

    socketio.emit("overlay", {
        "user": user,
        "gift": gift,
        "amount": amount,
        "avatar": avatar,
        "diamonds": diamonds,
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
    user = data["user"]
    comment = data.get("message", "").lower()
    avatar = data.get("avatar")

    vm, rule = resolve_vm_for_event("comment", comment)

    if not vm:
        return {"ok": True}

    socketio.emit("command", {
        "action": rule["action"],
        "unit": rule["unit"],
        "amount": 1
    }, room=vm)

    socketio.emit("overlay", {
        "type": "comment",
        "vm": vm,
        "user": user,
        "avatar": avatar,
        "diamonds": 1,
        "action": rule["action"],
        "unit": rule["unit"],
        "amount": 1
    })

    print(f"💬 {vm} → {rule['action']} {rule['unit']}")
    return {"ok": True}



@app.route("/like", methods=["POST"])
def like_event():
    data = request.json
    likes = data.get("likes", 0)
    user = data["user"]
    avatar = data.get("avatar")

    for vm, vm_data in VMS.items():
        rules = vm_data["rules"].get("likes")
        if not rules:
            continue

        threshold = rules["threshold"]

        # 🔹 buffer POR USUARIO
        user_buffer = vm_data["like_buffer"].get(user, 0)
        user_buffer += likes

        spawned = user_buffer // threshold
        user_buffer %= threshold  # 👈 RESTA LOS 20 LIKES CONSUMIDOS

        vm_data["like_buffer"][user] = user_buffer

        print(f"[LIKE BUFFER] {vm} | {user} = {vm_data['like_buffer'][user]}")

        if spawned > 0:
            # VM command
            socketio.emit("command", {
                "action": rules["army"]["action"],
                "unit": rules["army"]["unit"],
                "amount": spawned
            }, room=vm)

            # Overlay (consume likes correctamente)
            socketio.emit("overlay", {
                "vm": vm,
                "user": user,
                "avatar": avatar,
                "action": rules["army"]["action"],
                "unit": rules["army"]["unit"],
                "diamonds": 1,
                "amount": spawned
            })

            print(f"❤️ {vm} | {user} → {spawned} unidades")

        break  # 👈 primer VM que maneja likes

    return {"ok": True}


@app.route("/follow", methods=["POST"])
def follow_event():
    vm, rules = resolve_vm_for_event("follow")

    data = request.json
    avatar = data.get("avatar")
    user = data.get("user")
    if not vm:
        return {"ok": True}

    emit_simple_event(vm, "follow")

    socketio.emit("overlay", {
        "type": "follow",
        "vm": vm,
        "user": user,
        "avatar": avatar,
        "action": rules["army"]["action"],
        "unit": rules["army"]["unit"],
        "diamonds":1,
        "amount": 1
    })


    print(f"➕ Follow → {vm}")
    return {"ok": True}


@app.route("/share", methods=["POST"])
def share_event():
    vm, rules = resolve_vm_for_event("share")

    data = request.json
    user = data.get("user")
    avatar = data.get("avatar")

    if not vm:
        return {"ok": True}

    emit_simple_event(vm, "share")

    socketio.emit("overlay", {
        "type": "share",
        "vm": vm,
        "user": user,
        "avatar": avatar,
        "action": rules["army"]["action"],
        "unit": rules["army"]["unit"],
        "diamonds":1,
        "amount": 1
    })

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
