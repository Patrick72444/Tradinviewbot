import os
from flask import Flask, request
from kucoin_futures.client import Trade
import requests

app = Flask(__name__)

# Variables de entorno
api_key = os.getenv("KUCOIN_API_KEY")
api_secret = os.getenv("KUCOIN_API_SECRET")
api_passphrase = os.getenv("KUCOIN_API_PASSPHRASE")
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")

# Cliente de KuCoin Futures
client = Trade(key=api_key, secret=api_secret, passphrase=api_passphrase, is_sandbox=False)

# Configuraciones
symbol = "BTCUSDTM"  # ⚡ IMPORTANTE: Futuros KuCoin usan USDT, termina en M (perpetual)
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

    # Obtener balance de USDT
    account_overview = client.get_account_overview()
    usdt_balance = float(account_overview["availableBalance"])

    # Obtener precio de mercado
    ticker = client.get_ticker(symbol)
    price = float(ticker["price"])

    # Cálculo de tamaño de posición (size) en contratos
    amount_to_use = usdt_balance * balance_percentage
    size = round(amount_to_use / price, 3)  # Tamaño en BTC

    if order_type == "long":
        if size <= 0:
            send_telegram_message("⚠️ No hay suficiente USDT para abrir LONG.")
            return {"code": "no balance"}

        client.create_market_order(symbol, "buy", size=size)
        mensaje = f"🟢 LONG ejecutado: {size} BTC a {price} USDT"
        send_telegram_message(mensaje)

    elif order_type == "short":
        if size <= 0:
            send_telegram_message("⚠️ No hay suficiente USDT para abrir SHORT.")
            return {"code": "no balance"}

        client.create_market_order(symbol, "sell", size=size)
        mensaje = f"🔴 SHORT ejecutado: {size} BTC a {price} USDT"
        send_telegram_message(mensaje)

    else:
        send_telegram_message("❌ Orden no reconocida.")
        return {"code": "invalid order"}

    return {"code": "success"}

# Ejecutar el servidor
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

