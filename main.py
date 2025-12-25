from flask import Flask, request
from flask_socketio import SocketIO
import json

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on("register")
def register(data):
    print("🤖 Bot registrado:", data)

@app.route("/event", methods=["POST"])
def event():
    data = request.json
    
    print("Recibio request: " + json.dumps(data))

    socketio.emit("overlay", {
        "user": data["user"],
        "gift": data["gift"],
        "amount": data["amount"]
    })

    # lógica del juego aquí también
    socketio.emit("command", {"action": "aldeano"})

    return {"ok": True}

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
