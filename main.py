import os
from flask import Flask, request
from binance.spot import Spot
import requests

app = Flask(__name__)

# Variables de entorno
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")

# Cliente de Binance Spot
client = Spot(api_key=api_key, api_secret=api_secret)

# Configuraciones
symbol = "BTCUSDC"  # Cambiado a USDC
balance_percentage = 1.0  # 100%

# Función para enviar mensajes a Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    requests.post(url, data=payload)

# Webhook de TradingView
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print(f"Alerta recibida: {data}")

    order_type = data.get("order_type")

    balances = client.account()["balances"]
    usdc_balance = next((float(b["free"]) for b in balances if b["asset"] == "USDC"), 0.0)
    btc_balance = next((float(b["free"]) for b in balances if b["asset"] == "BTC"), 0.0)

    price = float(client.ticker_price(symbol=symbol)["price"])

    if order_type == "long":
        amount_to_use = usdc_balance * balance_percentage
        quantity = round(amount_to_use / price, 6)

        if quantity == 0:
            send_telegram_message("⚠️ No hay suficiente USDC para comprar BTC.")
            return {"code": "no balance"}

        client.new_order(symbol=symbol, side="BUY", type="MARKET", quantity=quantity)
        mensaje = f"🟢 COMPRA ejecutada: {quantity} BTC a {price} USDC"
        send_telegram_message(mensaje)

    elif order_type == "short":
        quantity = round(btc_balance, 6)

        if quantity == 0:
            send_telegram_message("⚠️ No hay BTC disponible para vender.")
            return {"code": "no balance"}

        client.new_order(symbol=symbol, side="SELL", type="MARKET", quantity=quantity)
        mensaje = f"🔴 VENTA ejecutada: {quantity} BTC a {price} USDC"
        send_telegram_message(mensaje)

    else:
        send_telegram_message("❌ Orden no reconocida.")
        return {"code": "invalid order"}

    return {"code": "success"}

# Ejecutar el servidor
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

