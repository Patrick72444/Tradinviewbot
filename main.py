import os
from flask import Flask, request
from kucoin.client import KucoinFutures

# Cargar las claves de las variables de entorno
api_key = os.getenv('API_KEY')
api_secret = os.getenv('API_SECRET')
api_passphrase = os.getenv('API_PASSPHRASE')

# Crear la app de Flask
app = Flask(__name__)

# Conexión al cliente de KuCoin Futures
client = KucoinFutures(
    key=api_key,
    secret=api_secret,
    passphrase=api_passphrase,
    is_sandbox=False  # True si usas sandbox, False si es real
)

# Ruta de prueba para ver si el bot está vivo
@app.route('/ping', methods=['GET'])
def ping():
    return 'Bot está vivo! 🚀'

# Ruta para abrir una operación LONG
@app.route('/buy', methods=['POST'])
def buy():
    try:
        order = client.create_market_order(
            symbol='BTCUSDCM',
            side='buy',
            size=0.0001  # Puedes ajustar el tamaño
        )
        return {'status': 'success', 'order': order}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

# Ruta para abrir una operación SHORT
@app.route('/sell', methods=['POST'])
def sell():
    try:
        order = client.create_market_order(
            symbol='BTCUSDCM',
            side='sell',
            size=0.0001  # Puedes ajustar el tamaño
        )
        return {'status': 'success', 'order': order}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

# Ejecutar el servidor
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
