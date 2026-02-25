import os

from dotenv import load_dotenv

from flask import Flask, redirect, render_template, request, url_for
from flask_socketio import SocketIO, emit
from vonage import Auth, Vonage
from vonage_messages import Sms

VONAGE_VIRTUAL_NUMBER = 'your-vonage-number-goes-here'

load_dotenv()

APPLICATION_ID = os.getenv('APPLICATION_ID')
PRIVATE_KEY = os.getenv('PRIVATE_KEY')

client = Vonage(Auth(application_id=APPLICATION_ID, private_key=PRIVATE_KEY))


app = Flask(__name__)
socketio = SocketIO(app)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/delivery_receipt/<message_uuid>')
def delivery_receipt(message_uuid):
    return render_template('delivery_receipt.html', message_uuid=message_uuid)


@app.route('/webhooks/message-status', methods=['POST'])
def message_status():
    request_object = request.get_json()
    message_uuid = request_object['message_uuid']
    status = request_object['status']

    print(
        f"Message status for message UUID: {request_object['message_uuid']} ===> {request_object['status']}"
    )

    if 'error' in request_object:
        print(
            f"Error encountered ===> {request_object['error']['title']} : {request_object['error']['detail']}"
        )
        info = (
            f"{request_object['error']['title']} : {request_object['error']['detail']}"
        )
        socketio.emit(
            'status_update',
            {'message_uuid': message_uuid, 'status': status, 'info': info},
        )

    else:
        socketio.emit('status_update', {'message_uuid': message_uuid, 'status': status})

    return '200', 200


@app.route('/send_sms', methods=['POST'])
def send_sms():
    to_number = request.form['to_number']
    print(f"To number is ===> {to_number}")
    message = request.form['message']

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
