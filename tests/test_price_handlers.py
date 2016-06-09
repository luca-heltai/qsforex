from qsforex.library.price_handlers import *
from nose.tools import eq_

def test_streaming_price_handler():
    ph = StreamingForexPrices()
    ph.initialize()
    ph.run()

def test_random_price_handler():
    ph = RandomPriceHandler()
    ph.initialize()
    t = ph.run()
    eq_(t.ask, Decimal('1.10100') )


def test_historical_price_handler():
    ph = HistoricCSVPriceHandler()
    ph.initialize(['XXXYYY'])
    t = ph.run()
    eq_(t.ask, Decimal('1.10100'))
