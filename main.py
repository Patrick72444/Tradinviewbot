from flask import Flask, request
import requests

app = Flask(__name__)

# Reemplaza estos valores con los tuyos
TELEGRAM_TOKEN = 'TU_TELEGRAM_TOKEN'
TELEGRAM_CHAT_ID = 'TU_CHAT_ID'

def send_telegram_message(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message
    }
    requests.post(url, data=payload)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if data:
        # Puedes personalizar el mensaje
        message = f"Señal recibida: {data}"
        send_telegram_message(message)
    return '', 200

if __name__ == '__main__':
    app.run()
