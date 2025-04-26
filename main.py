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

symbol = "BTCUSDCM"  # Kucoin Futures symbol
contract_size = 0.001  # Tamaño de contrato BTC/USDCM
leverage = 1
base_url = "https://api-futures.kucoin.com"

# Funciones

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    requests.post(url, data=payload)

def sign_request(endpoint, method, body=""):
    now = int(time.time() * 1000)
    str_to_sign = f"{now}{method}{endpoint}{body}"
    signature = base64.b64encode(hmac.new(api_secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest())
    passphrase = base64.b64encode(hmac.new(api_secret.encode('utf-8'), api_passphrase.encode('utf-8'), hashlib.sha256).digest())
    headers = {
        "KC-API-KEY": api_key,
        "KC-API-SIGN": signature.decode(),
        "KC-API-TIMESTAMP": str(now),
        "KC-API-PASSPHRASE": passphrase.decode(),
        "KC-API-KEY-VERSION": "2",
        "Content-Type": "application/json"
    }
    return headers

def get_balance_usdc():
    endpoint = "/api/v1/account-overview"
    params = "?currency=USDC"
    url = base_url + endpoint + params
    headers = sign_request(endpoint + params, "GET")
    response = requests.get(url, headers=headers)
    return float(response.json()['data']['availableBalance'])

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print(f"Señal recibida: {data}")

    order_type = data.get("order_type")
    if order_type not in ["long", "short"]:
        send_telegram_message("❌ Señal desconocida.")
        return {"code": "invalid"}

    # Obtener balance disponible
    usdc_balance = get_balance_usdc()
    if usdc_balance < 5:
        send_telegram_message("⚠️ No hay suficiente balance para operar.")
        return {"code": "no_balance"}

    # Calcular número de contratos
    market_price = get_market_price()
    amount_in_btc = usdc_balance / market_price
    contracts = max(1, round(amount_in_btc / contract_size))  # Siempre al menos 1 contrato

    # Configurar orden
    side = "buy" if order_type == "long" else "sell"
    endpoint = "/api/v1/orders"
    url = base_url + endpoint
    order = {
        "symbol": symbol,
        "side": side,
        "leverage": leverage,
        "type": "market",
        "size": contracts
    }
    body = json.dumps(order)
    headers = sign_request(endpoint, "POST", body)

    response = requests.post(url, headers=headers, data=body)
    result = response.json()

    if result.get("code") == "200000":
        mensaje = f"✅ Operación {side.upper()} ejecutada: {contracts} contratos"
        send_telegram_message(mensaje)
        return {"code": "success"}
    else:
        send_telegram_message(f"❌ Error enviando orden: {result}")
        return {"code": "error", "details": result}

def get_market_price():
    endpoint = f"/api/v1/mark-price/{symbol}/current"
    url = base_url + endpoint
    headers = sign_request(endpoint, "GET")
    response = requests.get(url, headers=headers)
    return float(response.json()['data']['value'])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


