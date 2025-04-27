import os
import time
import hmac
import hashlib
import base64
import requests
from flask import Flask, request, jsonify

# Cargar API KEYS desde las variables de entorno
API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
API_PASSPHRASE = os.getenv('API_PASSPHRASE')
API_BASE_URL = 'https://api-futures.kucoin.com'  # Kucoin Futures URL

# Inicializar Flask
app = Flask(__name__)

def kucoin_headers(method, endpoint, body=""):
    now = int(time.time() * 1000)
    str_to_sign = f"{now}{method}{endpoint}{body}"
    signature = base64.b64encode(hmac.new(API_SECRET.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest())
    passphrase = base64.b64encode(hmac.new(API_SECRET.encode('utf-8'), API_PASSPHRASE.encode('utf-8'), hashlib.sha256).digest())

    headers = {
        "KC-API-SIGN": signature.decode(),
        "KC-API-TIMESTAMP": str(now),
        "KC-API-KEY": API_KEY,
        "KC-API-PASSPHRASE": passphrase.decode(),
        "KC-API-KEY-VERSION": "2",
        "Content-Type": "application/json"
    }
    return headers

def create_market_order(symbol, side, size):
    endpoint = "/api/v1/orders"
    url = API_BASE_URL + endpoint
    data = {
        "clientOid": str(int(time.time()*1000)),
        "side": side,
        "symbol": symbol,
        "type": "market",
        "size": size
    }
    import json
    body = json.dumps(data)
    headers = kucoin_headers("POST", endpoint, body)
    response = requests.post(url, headers=headers, data=body)
    return response.json()

@app.route('/ping', methods=['GET'])
def ping():
    return "Bot online 🚀"

@app.route('/buy', methods=['POST'])
def buy():
    try:
        result = create_market_order("BTCUSDCM", "buy", 0.0001)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/sell', methods=['POST'])
def sell():
    try:
        result = create_market_order("BTCUSDCM", "sell", 0.0001)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

