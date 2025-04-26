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

# Variables de trading
symbol = "BTCUSDCM"  # Muy importante, BTC Perpetual/USDC
fixed_size = "0.0001"  # Debe ser string
leverage = 1
base_url = "https://api-futures.kucoin.com"

# Funcion para enviar mensajes a Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    requests.post(url, data=payload)

# Funcion para firmar las solicitudes
def sign_request(endpoint, method, body=""):
    now = int(time.time() * 1000)
    str_to_sign = f"{str(now)}{method}{endpoint}{body}"
    signature = base64.b64encode(hmac.new(api_secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest())
    passphrase = base64.b64encode(hmac.new(api_secret.encode('utf-8'), api_passphrase.encode('utf-8'), hashlib.sha256).digest())
    headers = {
        "KC-API-KEY": api_key,
        "KC-API-SIGN": signature,
        "KC-API-TIMESTAMP": str(now),
        "KC-API-KEY-VERSION": "2",
        "KC-API-PASSPHRASE": passphrase,
        "Content-Type": "application/json"
    }
    return headers

# Funcion para enviar la solicitud firmada
def send_request(method, endpoint, body=None):
    url = base_url + endpoint
    headers = sign_request(endpoint, method, json.dumps(body) if body else "")
    if method == "POST":
        response = requests.post(url, headers=headers, json=body)
    else:
        response = requests.get(url, headers=headers)
    return response.json()

# Funcion para crear orden de mercado
def create_market_order(side):
    endpoint = "/api/v1/orders"
    order = {
        "symbol": symbol,
        "side": side,
        "type": "market",
        "size": fixed_size,
        "leverage": leverage,
        "reduceOnly": False
    }
    return send_request("POST", endpoint, body=order)

# Webhook para TradingView
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print(f"Alerta recibida: {data}")

    order_type = data.get("order_type")

    if order_type == "long":
        response = create_market_order("buy")
        if "orderId" in response:
            send_telegram_message(f"\ud83d\udc9a Operación BUY ejecutada: {fixed_size} BTC")
        else:
            send_telegram_message(f"\u274c Error enviando orden: {response}")

    elif order_type == "short":
        response = create_market_order("sell")
        if "orderId" in response:
            send_telegram_message(f"\ud83d\udd34 Operación SELL ejecutada: {fixed_size} BTC")
        else:
            send_telegram_message(f"\u274c Error enviando orden: {response}")

    else:
        send_telegram_message("\u274c Se recibió un tipo de orden no válido.")

    return {"code": "success"}

# Ejecutar servidor
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
