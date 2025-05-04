import requests
import time
import uuid
import hmac
import base64
from hashlib import sha256

# === TU CONFIGURACIÓN ===
API_KEY = "6817470bc058ba0001f9bc1e"
API_SECRET = "9e041df5-c0db-46f1-abdc-5b85a79e82ae"
API_PASSPHRASE = "147896321"

BASE_URL = "https://api-futures.kucoin.com"
ENDPOINT = "/api/v1/orders"

# === PARÁMETROS DE LA ORDEN ===
client_oid = str(uuid.uuid4())
body = {
    "clientOid": client_oid,
    "side": "sell",
    "symbol": "XBTUSDCM",           # ¡Importante! Asegúrate de usar el símbolo exacto
    "leverage": 5,
    "type": "market",
    "size": 1,
    "marginMode": "ISOLATED"
}

# === FIRMA DE LA SOLICITUD ===
def sign_request(api_key, api_secret, api_passphrase, method, endpoint, body=""):
    now = int(time.time() * 1000)
    str_to_sign = f"{now}{method}{endpoint}{body}"
    signature = base64.b64encode(
        hmac.new(api_secret.encode(), str_to_sign.encode(), sha256).digest()
    ).decode()
    passphrase = base64.b64encode(
        hmac.new(api_secret.encode(), api_passphrase.encode(), sha256).digest()
    ).decode()
    return now, signature, passphrase

# Cuerpo en string JSON
import json
body_str = json.dumps(body)

# Firmamos la petición
timestamp, signature, passphrase = sign_request(API_KEY, API_SECRET, API_PASSPHRASE, "POST", ENDPOINT, body_str)

headers = {
    "KC-API-KEY": API_KEY,
    "KC-API-SIGN": signature,
    "KC-API-TIMESTAMP": str(timestamp),
    "KC-API-PASSPHRASE": passphrase,
    "KC-API-KEY-VERSION": "2",
    "Content-Type": "application/json"
}

# Enviamos la orden
response = requests.post(BASE_URL + ENDPOINT, headers=headers, data=body_str)

# Mostramos el resultado
print("✅ Respuesta de KuCoin:")
print(response.status_code, response.text)

