import os
import time
import hmac
import hashlib
import base64
import json
import requests
from flask import Flask, request

app = Flask(__name__)

# Configuración de API
api_key = os.getenv("KUCOIN_API_KEY")
api_secret = os.getenv("KUCOIN_API_SECRET")
api_passphrase = os.getenv("KUCOIN_API_PASSPHRASE")
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")

symbol = "BTCUSDCM"
fixed_size = 0.00019  # Tamaño ajustado
leverage = 1  # Apalancamiento
base_url = "https://api-futures.kucoin.com"

# Función para enviar mensaje a Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    requests.post(url, data=payload)

# Función para hacer firma de seguridad
def sign_request(endpoint, method, body=""):
    now = int(time.time() * 1000)
    str_to_sign = f"{now}{method}{endpoint}{body}"
    signature = base64.b64encode(
        hmac.new(api_secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest()
    )
    passphrase = base64.b64encode(
        hmac.new(api_secret.encode('utf-8'), api_passphrase.encode('utf-8'), hashlib.sha256).digest()
    )

    headers = {
        "KC-API-SIGN": signature,
        "KC-API-TIMESTAMP": str(now),
        "KC-API-KEY": api_key,
        "KC-API-PASSPHRASE": passphrase,
        "KC-API-KEY-VERSION": "2",
        "Content-Type": "application/json"
    }
    return headers

# Función para enviar orden
def send_order(side, size):
    endpoint = "/api/v1/orders"
    url = base_url + endpoint
    body = {
        "clientOid": str(int(time.time() * 1000)),
        "side": side,
        "symbol": symbol,
        "leverage": str(leverage),
        "type": "market",
        "size": str(size),
    }
    body_json = json.dumps(body)
    headers = sign_request(endpoint, "POST", body_json)
    response = requests.post(url, headers=headers, data=body_json)
    if response.status_code == 200:
        send_telegram_message(f"✅ Operación {side.upper()} ejecutada: {size} BTC")
    else:
        send_telegram_message(f"❌ Error enviando orden: {response.text}")

# Webhook de TradingView
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print(f"Alerta recibida: {data}")

    order_type = data.get("order_type")

    if order_type == "long":
        send_order("buy", fixed_size)

    elif order_type == "short":
        send_order("sell", fixed_size)

    else:
        send_telegram_message("❌ Orden no reconocida.")
        return {"code": "invalid order"}

    return {"code": "success"}

# Ejecutar servidor
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)






