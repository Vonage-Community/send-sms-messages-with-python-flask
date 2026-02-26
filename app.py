import os

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, url_for
from flask_socketio import SocketIO
from vonage import Auth, Vonage
from vonage_messages import Sms

load_dotenv()

APPLICATION_ID = os.getenv("APPLICATION_ID")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
VONAGE_VIRTUAL_NUMBER = os.getenv("VONAGE_VIRTUAL_NUMBER")

if not APPLICATION_ID or not PRIVATE_KEY or not VONAGE_VIRTUAL_NUMBER:
    raise RuntimeError("Missing APPLICATION_ID, PRIVATE_KEY, or VONAGE_VIRTUAL_NUMBER env vars")

client = Vonage(Auth(application_id=APPLICATION_ID, private_key=PRIVATE_KEY))

app = Flask(__name__)
socketio = SocketIO(app)


@app.route('/')
def index():
    return render_template('index.html')


@app.route("/delivery_receipt/<message_uuid>")
def delivery_receipt(message_uuid):
    return render_template("delivery_receipt.html", message_uuid=message_uuid)


@app.route("/webhooks/message-status", methods=["POST"])
def message_status():
    data = request.get_json(silent=True) or {}
    message_uuid = data.get("message_uuid")
    status = data.get("status")

    if not message_uuid or not status:
        return {"error": "missing message_uuid/status"}, 400

    payload = {"message_uuid": message_uuid, "status": status}

    err = data.get("error")
    if isinstance(err, dict):
        payload["info"] = f"{err.get('title', 'Error')} : {err.get('detail', '')}"

    print("Status update uuid=%s status=%s", message_uuid, status)

    socketio.emit("status_update", payload)

    return "200", 200

@app.route("/send_sms", methods=["POST"])
def send_sms():
    to_number = (request.form.get("to_number") or "").strip()
    message = (request.form.get("message") or "").strip()

    print(f"To number is ===> {to_number}")

    if not to_number or not message:
        return {"error": "to_number and message are required"}, 400

    response = client.messages.send(
        Sms(
            from_=VONAGE_VIRTUAL_NUMBER,
            to=to_number,
            text=message,
        )
    )

    message_uuid = response.message_uuid
    print(f"Message UUID is ===> {message_uuid}")

    return redirect(url_for('delivery_receipt', message_uuid=message_uuid))


if __name__ == '__main__':
    socketio.run(app)
