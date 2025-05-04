from flask import Flask, request, jsonify
import requests, json, time, uuid, hmac, base64
from hashlib import sha256

# === CONFIGURACIÓN ===
API_KEY = "6817470bc058ba0001f9bc1e"
API_SECRET = "9e041df5-c0db-46f1-abdc-5b85a79e82ae"
API_PASSPHRASE = "147896321"
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
    try:
        data = res.json()
        if data.get("code") != "200000":
            print("⚠️ Error en respuesta de posición:", data)
            return None
        return data["data"]
    except Exception as e:
        print("❌ Error procesando JSON de posición:", e)
        return None

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
    try:
        print("📨 Webhook recibido")
        print("Contenido crudo:", request.data)

        data = request.get_json(force=True)
        print("✅ JSON recibido:", data)

        action = data.get("order_type")
        if action not in ["long", "short"]:
            print("❌ Acción inválida:", action)
            return jsonify({"error": "invalid order_type"}), 400

        side = "buy" if action == "long" else "sell"
        opposite = "sell" if side == "buy" else "buy"

        # 1. Obtener posición actual
        pos = get_position()
        if not pos or "currentQty" not in pos or "markPrice" not in pos:
            print("❌ No se pudo obtener posición válida:", pos)
            return jsonify({"error": "no position data"}), 500

        current_qty = float(pos["currentQty"])

        if current_qty > 0:
            print("📉 Cerrando posición previa:", current_qty)
            create_market_order(opposite, current_qty, reduce_only=True)

        # 2. Calcular tamaño de nueva posición
        balance = get_available_balance()
        entry_value = balance * LEVERAGE
        price = float(pos["markPrice"])
        size = int(entry_value / price)
        if size == 0:
            print("⚠️ Tamaño calculado demasiado pequeño")
            return jsonify({"error": "size too small"}), 400

        # 3. Ejecutar orden nueva
        create_market_order(side, size, reduce_only=False)

        return jsonify({"status": "ok", "side": side, "size": size})

    except Exception as e:
        print("❌ Error en el webhook:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("🚀 Bot iniciado y esperando webhooks en puerto 10000...")
    app.run(host="0.0.0.0", port=10000)

