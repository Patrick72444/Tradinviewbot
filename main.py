import os
from flask import Flask, request
from kucoin.client import Client
import requests

app = Flask(__name__)

# Variables de entorno
api_key = os.getenv("KUCOIN_API_KEY")
api_secret = os.getenv("KUCOIN_API_SECRET")
api_passphrase = os.getenv("KUCOIN_API_PASSPHRASE")
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")

# Cliente de KuCoin
client = Client(api_key, api_secret, api_passphrase, sandbox=False)

# Configuraciones
symbol = "BTCUSDCM"  # ✅ BTC/USDC perpetual en KuCoin Futures
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

    # Obtener balance disponible en Futures
    futures_account = client.get_futures_account_overview(currency='USDC')
    usdc_balance = float(futures_account["availableBalance"])

    # Obtener precio actual
    ticker = client.get_futures_mark_price(symbol)
    price = float(ticker["value"])

    # Cálculo del tamaño de orden
    amount_to_use = usdc_balance * balance_percentage
    size = round(amount_to_use / price, 4)  # 4 decimales para BTC

    if order_type == "long":
        if size <= 0:
            send_telegram_message("⚠️ No hay suficiente USDC para abrir LONG.")
            return {"code": "no balance"}

        client.create_market_order(symbol=symbol, side="buy", size=size, leverage=1)
        mensaje = f"🟢 LONG ejecutado: {size} BTC a {price} USDC"
        send_telegram_message(mensaje)

    elif order_type == "short":
        if size <= 0:
            send_telegram_message("⚠️ No hay suficiente USDC para abrir SHORT.")
            return {"code": "no balance"}

        client.create_market_order(symbol=symbol, side="sell", size=size, leverage=1)
        mensaje = f"🔴 SHORT ejecutado: {size} BTC a {price} USDC"
        send_telegram_message(mensaje)

    else:
        send_telegram_message("❌ Orden no reconocida.")
        return {"code": "invalid order"}

    return {"code": "success"}

# Ejecutar el servidor
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

