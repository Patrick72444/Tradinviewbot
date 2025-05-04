from kucoin_futures.client import Trade
import uuid

# Configura tus claves aquí directamente
API_KEY = 'TU_API_KEY'
API_SECRET = 'TU_API_SECRET'
API_PASSPHRASE = 'TU_API_PASSPHRASE'

# Inicializa cliente en modo sandbox (testnet)
client = Trade(key=API_KEY, secret=API_SECRET, passphrase=API_PASSPHRASE, is_sandbox=True)

# Ejecuta orden de compra
try:
    order = client.create_market_order(
        symbol='XBTUSDM',   # símbolo en testnet: BTC/USDT margined
        side='buy',
        leverage=5,
        size=1,
        client_oid=str(uuid.uuid4())
    )
    print("✅ Orden de compra enviada correctamente:")
    print(order)
except Exception as e:
    print("❌ Error al enviar la orden:")
    print(e)
