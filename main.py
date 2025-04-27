from kucoin_futures.client import Trade

# Tus claves de API (ponlas de forma segura, nunca en el código final!)
api_key = 'TU_API_KEY'
api_secret = 'TU_API_SECRET'
api_passphrase = 'TU_API_PASSPHRASE'

# Conexión al cliente de trading
client = Trade(
    key=api_key,
    secret=api_secret,
    passphrase=api_passphrase,
    is_sandbox=False  # Pon True si usas sandbox, pero ahora parece que es real
)

# Crear una orden de mercado para abrir un long en BTC/USDT
order = client.create_market_order(
    symbol='BTCUSDCM',    # Ojo: en KuCoin para futuros añaden la "M" al final
    side='buy',           # 'buy' para long, 'sell' para short
    size=0.0001            # tamaño en BTC
)

print(order)

