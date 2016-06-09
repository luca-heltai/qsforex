import oandapy
from qsforex import settings
from qsforex.library.price_handlers import StreamingForexPrices

instruments = "EUR_USD"


def test_rest_connection():
    """Initiate a connection, and get current EUR_USD price"""
    oanda = oandapy.API(access_token=settings.ACCESS_TOKEN,
                        environment=settings.DOMAIN)

    response = oanda.get_prices(instruments=instruments)
    prices = response.get("prices")
    buy_price = prices[0].get("bid")
    print buy_price
