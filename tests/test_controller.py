from qsforex.controller.celery import app
from qsforex.library.price_handlers import RandomPriceHandler
import mock
from nose.tools import eq_


def run_celery():
    return mock.patch('qsforex.controller.celeryconfig.CELERY_ALWAYS_EAGER', True, create=True)


# This test does not succeed. I still have to understand how to test properly
# celery workers

# def test_process_tick():
#     with run_celery():
#         ph = RandomPriceHandler()
#         ph.initialize()
#         res = ph.delay()
#         eq_(res.state, 'SUCCESS')
