import os
import time
import hmac
import hashlib
import base64
import requests
import json
from flask import Flask, request, jsonify

# Configuración
API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
API_PASSPHRASE = os.getenv('API_PASSPHRASE')
API_BASE_URL = 'https://api-futures.kucoin.com'

# Iniciar Flask
app = Flask(__name__)

# Función para firmar las peticiones
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

# Función para crear órdenes
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
    body = json.dumps(data)
    headers = kucoin_headers("POST", endpoint, body)
    response = requests.post(url, headers=headers, data=body)
    return response.json()

# 📍 Rutas de Flask
@app.route('/ping', methods=['GET'])
def ping():
    return "Bot online 🚀"

@app.route('/buy', methods=['POST'])
def buy():
    try:
        result = create_market_order("BTCUSDTM", "buy", 1)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/sell', methods=['POST'])
def sell():
    try:
        result = create_market_order("BTCUSDTM", "sell", 1)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/symbols', methods=['GET'])
def symbols():
    try:
        endpoint = "/api/v1/contracts/active"
        url = API_BASE_URL + endpoint
        headers = kucoin_headers("GET", endpoint)
        response = requests.get(url, headers=headers)
        return response.json()
    except Exception as e:
        return jsonify({"error": str(e)})

# Ejecutar servidor
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
