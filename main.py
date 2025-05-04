from flask import Flask, request, jsonify
import requests, json, time, uuid, hmac, base64
from hashlib import sha256

# === CONFIG ===
API_KEY = "TU_API_KEY"
API_SECRET = "TU_API_SECRET"
API_PASSPHRASE = "TU_API_PASSPHRASE"
BASE_URL = "https://api-futures.kucoin.com"
SYMBOL = "XBTUSDCM"
LEVERAGE = 5

app = Flask(__name__)

def sign_request(method, endpoint, body=""):
    now = str(int(time.time() * 1000))
    str_to_sign = f"{now}{method}{endpoint}{body}"
    signature = base64.b64encode(hmac.new(API_SECRET.encode(), str_to_sign.encode(), sha256).digest()).decode()
    passphrase = base64.b64encode(hmac.new(API_SECRET.encode(), API_PASSPHRASE.encode(), sha256).digest()).decode()
    headers = {
        "KC-API-KEY": API_KEY,
        "KC-API-SIGN": signature,
        "KC-API-TIMESTAMP": now,
        "KC-API-PASSPHRASE": passphrase,
        "KC-API-KEY-VERSION": "2",
        "Content-Type": "application/json"
    }
    return headers

def get_position():
    endpoint = f"/api/v1/position?symbol={SYMBOL}"
    headers = sign_request("GET", endpoint)
    res = requests.get(BASE_URL + endpoint, headers=headers)
    return res.json()["data"]

def get_available_balance():
    endpoint = "/api/v1/account-overview?currency=USDC"
    headers = sign_request("GET", endpoint)
    res = requests.get(BASE_URL + endpoint, headers=headers)
    return float(res.json()["data"]["availableBalance"])

def create_market_order(side, size, reduce_only=False):
    endpoint = "/api/v1/orders"
    body = {
        "clientOid": str(uuid.uuid4()),
        "side": side,
        "symbol": SYMBOL,
        "leverage": LEVERAGE,
        "type": "market",
        "size": int(size),
        "reduceOnly": reduce_only,
        "marginMode": "ISOLATED"
    }
    body_str = json.dumps(body)
    headers = sign_request("POST", endpoint, body_str)
    res = requests.post(BASE_URL + endpoint, headers=headers, data=body_str)
    print(f"✅ Orden {side.upper()} enviada. ReduceOnly={reduce_only}. Respuesta:", res.status_code, res.text)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    action = data.get("order_type")  # "long" o "short"
    if action not in ["long", "short"]:
        return jsonify({"error": "invalid order_type"}), 400

    side = "buy" if action == "long" else "sell"
    opposite_side = "sell" if side == "buy" else "buy"

    try:
        # 1. Obtener tamaño actual y cerrar posición si hay
        pos = get_position()
        current_qty = float(pos["currentQty"])
        if current_qty > 0:
            print("📉 Cerrando posición actual:", pos["currentQty"])
            create_market_order(opposite_side, current_qty, reduce_only=True)

        # 2. Obtener balance y calcular tamaño de entrada
        balance = get_available_balance()
        entry_value = balance * LEVERAGE
        # Tamaño = valor / precio actual
        price = float(pos["markPrice"])
        size = int(entry_value / price)
        if size == 0:
            return jsonify({"error": "size too small"}), 400

        # 3. Ejecutar nueva orden
        create_market_order(side, size, reduce_only=False)

        return jsonify({"status": "ok", "side": side, "size": size})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)


