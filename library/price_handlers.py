from __future__ import print_function

from decimal import Decimal, getcontext, ROUND_HALF_DOWN
import os
import os.path
import re
import datetime

import logging
import json
import requests

import numpy as np
import pandas as pd

from qsforex import settings
from qsforex.library.events import TickEvent

from celery import Task


class PriceHandler(Task):
    """
    PriceHandler is an abstract base class providing an interface for
    all subsequent (inherited) data handlers (both live and historic).

    The goal of a (derived) PriceHandler object is to output a set of
    bid/ask/timestamp "ticks" for each currency pair and place them into
    an event queue.

    This will replicate how a live strategy would function as current
    tick data would be streamed via a brokerage. Thus a historic and live
    system will be treated identically by the rest of the QSForex 
    backtesting suite.
    """
    _initialized = False

    def _set_up_prices_dict(self):
        """
        Due to the way that the Position object handles P&L
        calculation, it is necessary to include values for not
        only base/quote currencies but also their reciprocals.
        This means that this class will contain keys for, e.g.
        "GBPUSD" and "USDGBP".

        At this stage they are calculated in an ad-hoc manner,
        but a future TODO is to modify the following code to
        be more robust and straightforward to follow.
        """
        prices_dict = dict(
            (k, v) for k, v in (
                (p, {"bid": None, "ask": None, "time": None}) for p in self.pairs
            )
        )
        inv_prices_dict = dict(
            (k, v) for k, v in (
                (
                    "%s%s" % (p[3:], p[:3]),
                    {"bid": None, "ask": None, "time": None}
                ) for p in self.pairs
            )
        )
        prices_dict.update(inv_prices_dict)
        return prices_dict

    @staticmethod
    def invert_prices(pair, bid, ask):
        """
        Simply inverts the prices for a particular currency pair.
        This will turn the bid/ask of "GBPUSD" into bid/ask for
        "USDGBP" and place them in the prices dictionary.
        """
        getcontext().rounding = ROUND_HALF_DOWN
        inv_pair = "%s%s" % (pair[3:], pair[:3])
        inv_bid = (Decimal("1.0") / bid).quantize(
            Decimal("0.00001")
        )
        inv_ask = (Decimal("1.0") / ask).quantize(
            Decimal("0.00001")
        )
        return inv_pair, inv_bid, inv_ask

    @staticmethod
    def to_decimal(x, quant=Decimal("0.00001")):
        getcontext().rounding = ROUND_HALF_DOWN
        return Decimal(str(x)).quantize(quant)

    def run(self):
        raise NameError(
            'This is an abstract class. Overload your run function to return a TickEvent')


class HistoricCSVPriceHandler(PriceHandler):
    """
    HistoricCSVPriceHandler is designed to read CSV files of
    tick data for each requested currency pair and stream those
    to the provided events queue.
    """

    def initialize(self,
                   pairs=settings.PAIRS,
                   csv_dir=settings.CSV_DATA_DIR):
        """
        Initialises the historic data handler by requesting
        the location of the CSV files and a list of symbols.

        It will be assumed that all files are of the form
        'pair.csv', where "pair" is the currency pair. For
        GBP/USD the filename is GBPUSD.csv.

        Parameters:
        pairs - The list of currency pairs to obtain.
        csv_dir - Absolute directory path to the CSV files.
        """
        self.pairs = pairs
        self.csv_dir = csv_dir
        self.prices = self._set_up_prices_dict()
        self.pair_frames = {}
        self.file_dates = self._list_all_file_dates()
        self.continue_backtest = True
        self.cur_date_idx = 0
        self.cur_date_pairs = self._open_convert_csv_files_for_day(
            self.file_dates[self.cur_date_idx]
        )
        self._initialized = True

    def _list_all_csv_files(self):
        files = os.listdir(self.csv_dir)
        matching_files = []
        for pair in self.pairs:
            pattern = re.compile(pair + "_\d{8}.csv")
            matching_files += [f for f in files if pattern.search(f)]
            matching_files.sort()
        return matching_files

    def _list_all_file_dates(self):
        """
        Removes the pair, underscore and '.csv' from the
        dates and eliminates duplicates. Returns a list
        of date strings of the form "YYYYMMDD". 
        """
        csv_files = self._list_all_csv_files()
        de_dup_csv = list(set([d[7:-4] for d in csv_files]))
        de_dup_csv.sort()
        return de_dup_csv

    def _open_convert_csv_files_for_day(self, date_str):
        """
        Opens the CSV files from the data directory, converting
        them into pandas DataFrames within a pairs dictionary.

        The function then concatenates all of the separate pairs
        for a single day into a single data frame that is time 
        ordered, allowing tick data events to be added to the queue 
        in a chronological fashion.
        """
        for p in self.pairs:
            pair_path = os.path.join(self.csv_dir, '%s_%s.csv' % (p, date_str))
            self.pair_frames[p] = pd.io.parsers.read_csv(
                pair_path, header=0, index_col=0,
                parse_dates=True, dayfirst=True,
                names=("Time", "Ask", "Bid", "AskVolume", "BidVolume")
            )
            self.pair_frames[p]["Pair"] = p
        return pd.concat(self.pair_frames.values()).sort_index().iterrows()

    def _update_csv_for_day(self):
        try:
            dt = self.file_dates[self.cur_date_idx + 1]
        except IndexError:  # End of file dates
            return False
        else:
            self.cur_date_pairs = self._open_convert_csv_files_for_day(dt)
            self.cur_date_idx += 1
            return True

    def run(self):
        """
        This method returns a single tick and it updates
        the current bid/ask and inverse bid/ask.
        """
        try:
            index, row = next(self.cur_date_pairs)
        except StopIteration:
            # End of the current days data
            if self._update_csv_for_day():
                index, row = next(self.cur_date_pairs)
            else:  # End of the data
                self.continue_backtest = False
                return

        pair = row["Pair"]
        bid = self.to_decimal(row["Bid"])
        ask = self.to_decimal(row["Ask"])

        # Create decimalised prices for traded pair
        self.prices[pair]["bid"] = bid
        self.prices[pair]["ask"] = ask
        self.prices[pair]["time"] = index

        # Create decimalised prices for inverted pair
        inv_pair, inv_bid, inv_ask = self.invert_prices(pair, bid, ask)
        self.prices[inv_pair]["bid"] = inv_bid
        self.prices[inv_pair]["ask"] = inv_ask
        self.prices[inv_pair]["time"] = index

        # Return the tick event
        return TickEvent(pair, index, bid, ask)

    def stream_next_tick(self, events_queue):
        """
        This method is called by the backtesting function outside
        of this class and places a single tick onto the queue, as
        well as updating the current bid/ask and inverse bid/ask.
        """
        events_queue.put(self.run())


class StreamingForexPrices(PriceHandler):

    def initialize(self,
                   domain=settings.STREAM_DOMAIN,
                   access_token=settings.ACCESS_TOKEN,
                   account_id=settings.ACCOUNT_ID,
                   pairs=settings.PAIRS):
        self.domain = domain
        self.access_token = access_token
        self.account_id = account_id
        self.pairs = pairs
        self.prices = self._set_up_prices_dict()
        self.logger = logging.getLogger(__name__)
        self.stream = self.connect_to_stream()
        if self.stream.status_code is not 200:
            raise NameError('Error: stream status code ' +
                            str(self.stream.status_code))

    def connect_to_stream(self):
        pairs_oanda = ["%s_%s" % (p[:3], p[3:]) for p in self.pairs]
        pair_list = ",".join(pairs_oanda)
        try:
            requests.packages.urllib3.disable_warnings()
            s = requests.Session()
            url = "https://" + self.domain + "/v1/prices"
            headers = {'Authorization': 'Bearer ' + self.access_token}
            params = {'instruments': pair_list, 'accountId': self.account_id}
            req = requests.Request('GET', url, headers=headers, params=params)
            pre = req.prepare()
            resp = s.send(pre, stream=True, verify=False)
            return resp
        except Exception as e:
            s.close()
            print("Caught exception when connecting to stream\n" + str(e))

    def process_line(self, line):
        if line:
            try:
                dline = line.decode('utf-8')
                msg = json.loads(dline)
            except Exception as e:
                self.logger.error(
                    "Caught exception when converting message into json: %s" % str(
                        e)
                )
                return
            if "instrument" in msg or "tick" in msg:
                self.logger.debug(msg)
                getcontext().rounding = ROUND_HALF_DOWN
                instrument = msg["tick"]["instrument"].replace("_", "")
                time = msg["tick"]["time"]
                bid = self.to_decimal(msg["tick"]["bid"])
                ask = self.to_decimal(msg["tick"]["ask"])

                self.prices[instrument]["bid"] = bid
                self.prices[instrument]["ask"] = ask
                # Invert the prices (GBP_USD -> USD_GBP)
                inv_pair, inv_bid, inv_ask = self.invert_prices(
                    instrument, bid, ask)
                self.prices[inv_pair]["bid"] = inv_bid
                self.prices[inv_pair]["ask"] = inv_ask
                self.prices[inv_pair]["time"] = time
                return TickEvent(instrument, time, bid, ask)
            else:
                return None

    def run(self):
        for line in self.stream.iter_lines(1):
            tev = self.process_line(line)
            if tev is not None:
                return tev

    def stream_to_queue(self, events_queue):
        for line in self.stream.iter_lines(1):
            tev = self.process_line(line)
            if tev is not None:
                events_queue.put(tev)


class RandomPriceHandler(PriceHandler):
    """
      RandomPriceHandler is designed to generate a random tick.
    """

    def initialize(self, instrument='EURUSD',
                   S0=1.1, spread=0.002,
                   start_time=datetime.datetime.now(),
                   mu_dt=1400, sigma_dt=100, seed=42):
        np.random.seed(seed)
        self.instrument = instrument
        self.S0 = S0
        self.spread = spread
        self.ask = self.to_decimal(S0 + spread / 2.0)
        self.bid = self.to_decimal(S0 - spread / 2.0)
        self.current_time = start_time
        self.mu_dt = mu_dt
        self.sigma_dt = sigma_dt
        self._initialized = True

    @staticmethod
    def random():
        return np.random.standard_normal() * dt / 1000.0 / 86400.0

    def run(self):
        if self._initialized == False:
            raise NameError("Not initialized! Run initialize()")
        dt = abs(np.random.normal(self.mu_dt, self.sigma_dt))
        W = self.to_decimal(np.random.standard_normal()
                            * dt / 1000.0 / 86400.0)
        self.ask += W
        self.bid += W

        self.current_time += datetime.timedelta(0, 0, 0, dt)
        return TickEvent(self.instrument, self.current_time, self.bid, self.ask)
