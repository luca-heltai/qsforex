from decimal import Decimal
import inspect, os

ENVIRONMENTS = {
    "streaming": {
        "live": "stream-fxtrade.oanda.com",
        "practice": "stream-fxpractice.oanda.com",
        "sandbox": "stream-sandbox.oanda.com"
    },
    "api": {
        "live": "api-fxtrade.oanda.com",
        "practice": "api-fxpractice.oanda.com",
        "sandbox": "api-sandbox.oanda.com"
    }
}

qsforexdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

CSV_DATA_DIR = qsforexdir + "/csv_files"
OUTPUT_RESULTS_DIR = qsforexdir + "/output_dir"

DOMAIN = os.environ.get('OANDA_API_DOMAIN', None)
STREAM_DOMAIN = ENVIRONMENTS["streaming"][DOMAIN]
API_DOMAIN = ENVIRONMENTS["api"][DOMAIN]
ACCESS_TOKEN = os.environ.get('OANDA_API_ACCESS_TOKEN', None)
ACCOUNT_ID = os.environ.get('OANDA_API_ACCOUNT_ID', None)

BASE_CURRENCY = "EUR"
EQUITY = Decimal("100.00")
PAIRS = ['EURUSD']
