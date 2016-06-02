import json
import os

import oandapy
import requests
import threading
from qsforex import settings
from qsforex.data.streaming import StreamingForexPrices
try:
    import Queue as queue
except ImportError:
    import queue


instruments = "EUR_USD"


def test_rest_connection():
    # Initiate a connection, and get current EUR_USD price
    oanda = oandapy.API(environment="live",
                        access_token=settings.ACCESS_TOKEN)

    response = oanda.get_prices(instruments=instruments)
    prices = response.get("prices")
    buy_price = prices[0].get("bid")


def test_stream():
    # Create the OANDA market price streaming class
    # making sure to provide authentication commands
    pairs = ['EURUSD']

    # Fix the length of the queue to 5 objects
    events = queue.Queue(5)

    prices = StreamingForexPrices(
        settings.STREAM_DOMAIN,
        settings.ACCESS_TOKEN,
        settings.ACCOUNT_ID,
        pairs
    )

    response = prices.connect_to_stream()
    assert response.status_code == 200, \
        "Response status code is %, aborting" % (response.status_code)

    # Waits for 3 ticks, then exit with success
    max_lines = 3
    n_lines = 0
    for line in response.iter_lines(1):
        tev = prices.process_line(line)
        if tev is not None:
            print tev
            n_lines += 1
        if n_lines >= max_lines:
            break
    response.connection.close()

test_stream()
