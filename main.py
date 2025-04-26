import os
from flask import Flask, request
from kucoin_futures.client import Trade, Account
import requests

app = Flask(__name__)

# Variables de entorno
api_key = os.getenv("KUCOIN_API_KEY")
api_secret = os.getenv("KUCOIN_API_SECRET")
api_passphrase = os.getenv("KUCOIN_API_PASSPHRASE")
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")

# Clientes de KuCoin Futures
trade_client = Trade(api_key, api_secret, api_passphrase, False)
account_client = Account(api_key, api_secret, api_passphrase, False)

# Configuraciones
symbol = "BTCUSDCM"
balance_percentage = 1.0

# Función para enviar mensajes a Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    requests.post(url, data=payload)

# Función para cerrar posición abierta si existe
def close_open_position(symbol):
    try:
        positions = trade_client.get_position_list(symbol=symbol)
        for pos in positions:
            size = float(pos["currentQty"])
            if size != 0:
                side = "sell" if size > 0 else "buy"
                size = abs(size)
                trade_client.create_market_order(symbol=symbol, side=side, size=size)
                send_telegram_message(f"⚡ Posición existente CERRADA ({side.upper()}) de {size} contratos")
    except Exception as e:
        send_telegram_message(f"❗ Error cerrando posición: {e}")

# Webhook de TradingView
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print(f"Alerta recibida: {data}")

    order_type = data.get("order_type")

    # ✅ Obtener balance USDC correctamente
    balances = account_client.get_account_overview(currency="USDC")
    usdc_balance = float(balances["availableBalance"])

    # ✅ Obtener precio actual
    ticker = trade_client.get_mark_price(symbol)
    price = float(ticker["value"])

    # ✅ Cerrar posición si existe
    close_open_position(symbol)

    # ✅ Calcular tamaño de orden
    amount_to_use = usdc_balance * balance_percentage
    size = round(amount_to_use / price, 3)

    if size <= 0:
        send_telegram_message("⚠️ No hay suficiente USDC para operar.")
        return {"code": "no balance"}

    if order_type == "long":
        trade_client.create_market_order(symbol=symbol, side="buy", size=size)
        send_telegram_message(f"🟢 NUEVO LONG ejecutado: {size} BTC a {price} USDC")

    elif order_type == "short":
        trade_client.create_market_order(symbol=symbol, side="sell", size=size)
        send_telegram_message(f"🔴 NUEVO SHORT ejecutado: {size} BTC a {price} USDC")

    else:
        send_telegram_message("❌ Orden no reconocida.")
        return {"code": "invalid order"}

    return {"code": "success"}

# Ejecutar el servidor
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)



