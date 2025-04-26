import os
from flask import Flask, request
from binance.spot import Spot
import requests

app = Flask(__name__)

api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")

client = Spot(api_key=api_key, api_secret=api_secret)

symbol = "BTCUSDC"
balance_percentage = 1.0

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    requests.post(url, data=payload)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    order_type = data.get("order_type")

    balances = client.account()["balances"]
    usdt_balance = next((float(b["free"]) for b in balances if b["asset"] == "USDT"), 0.0)

    price = float(client.ticker_price(symbol=symbol)["price"])
    quantity = round((usdt_balance * balance_percentage) / price, 6)

    if quantity == 0:
        send_telegram_message("⚠️ No hay suficiente balance para operar.")
        return {"code": "no balance"}

    if order_type == "long":
        client.new_order(symbol=symbol, side="BUY", type="MARKET", quantity=quantity)
        mensaje = f"🟢 COMPRA ejecutada: {quantity} BTC a {price} USDT"
    elif order_type == "short":
        client.new_order(symbol=symbol, side="SELL", type="MARKET", quantity=quantity)
        mensaje = f"🔴 VENTA ejecutada: {quantity} BTC a {price} USDT"
    else:
        mensaje = "❌ Orden no reconocida"

    send_telegram_message(mensaje)
    return {"code": "success"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
