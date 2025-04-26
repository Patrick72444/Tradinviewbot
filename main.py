import os
import time
import hmac
import hashlib
import base64
import json
import requests

# Configura aquí tus credenciales
api_key = os.getenv("KUCOIN_API_KEY")
api_secret = os.getenv("KUCOIN_API_SECRET")
api_passphrase = os.getenv("KUCOIN_API_PASSPHRASE")

# Variables de trading
symbol = "BTCUSDCM"  # par de futuros
side = "buy"  # o "sell"
size = 1  # 1 contrato
leverage = 1
base_url = "https://api-futures.kucoin.com"

# Función para firmar
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
        "KC-API-KEY": api_key,
        "KC-API-SIGN": signature.decode(),
        "KC-API-TIMESTAMP": str(now),
        "KC-API-PASSPHRASE": passphrase.decode(),
        "KC-API-KEY-VERSION": "2",
        "Content-Type": "application/json"
    }
    return headers

# Función para mandar orden
def send_order():
    endpoint = "/api/v1/orders"
    url = base_url + endpoint
    order = {
        "symbol": symbol,
        "side": side,
        "type": "market",
        "size": size,
        "leverage": leverage,
        "reduceOnly": False
    }
    body = json.dumps(order)
    headers = sign_request(endpoint, "POST", body)

    response = requests.post(url, headers=headers, data=body)
    print(response.json())

if __name__ == "__main__":
    send_order()

