import time
import hashlib
import hmac
import base64
import json
import os
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
fixed_size = 0.0001  # Tamaño que quieres usar por trade
leverage = 1  # Apalancamiento
base_url = "https://api-futures.kucoin.com"

# Función para enviar mensaje a Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    requests.post(url, data=payload)

# Función para firmar la petición
def sign_request(endpoint, method, body=""):
    now = int(time.time() * 1000)
    str_to_sign = f"{now}{method}{endpoint}{body}"
    signature = base64.b64encode(
        hmac.new(api_secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest()
    )
    passphrase = base64.b64encode(
        hmac.new(api_secret.encode('utf-8'), api_passphrase.encode('utf-8'), hashlib.sha256).digest()
    )
    return {
        "KC-API-KEY": api_key,
        "KC-API-SIGN": signature.decode(),
        "KC-API-TIMESTAMP": str(now),
        "KC-API-KEY-VERSION": "2",
        "KC-API-PASSPHRASE": passphrase.decode(),
        "Content-Type": "application/json"
    }

# Función para enviar orden
def send_order(side):
    endpoint = "/api/v1/orders"
    url = base_url + endpoint
    order = {
        "clientOid": str(int(time.time() * 1000)),
        "side": side,
        "symbol": symbol,
        "leverage": str(leverage),
        "type": "market",
        "size": fixed_size  # IMPORTANTE: tamaño en número, no en string
    }
    body = json.dumps(order)
    headers = sign_request(endpoint, "POST", body)
    response = requests.post(url, headers=headers, data=body)
    if response.status_code == 200:
        send_telegram_message(f"✅ Operación {side.upper()} ejecutada: {fixed_size} BTC")
    else:
        send_telegram_message(f"❌ Error enviando orden: {response.text}")

# Webhook para recibir alertas de TradingView
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print(f"Alerta recibida: {data}")
    order_type = data.get("order_type")
    
    if order_type == "long":
        send_order("buy")
    elif order_type == "short":
        send_order("sell")
    else:
        send_telegram_message("❌ Orden no reconocida.")
        return {"code": "invalid order"}

    return {"code": "success"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
