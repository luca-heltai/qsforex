from __future__ import print_function

import calendar
import os.path
import sys
from datetime import datetime

import numpy as np

from qsforex import settings
from qsforex.library.price_handlers import RandomPriceHandler


def month_weekdays(year_int, month_int):
    """
    Produces a list of datetime.date objects representing the
    weekdays in a particular month, given a year.
    """
    cal = calendar.Calendar()
    return [
        d for d in cal.itermonthdates(year_int, month_int)
        if d.weekday() < 5 and d.year == year_int
    ]


if __name__ == "__main__":
    try:
        pair = sys.argv[1]
    except:
        pair = settings.PAIRS[0]

    rph = RandomPriceHandler()
    rph.initialize()

    days = month_weekdays(datetime.now().year,
                          datetime.now().month)

    rph.current_time = datetime(
        days[0].year, days[0].month, days[0].day, 0, 0, 0,
    )

    # Loop over every day in the month and create a CSV file
    # for each day, e.g. "GBPUSD_20150101.csv"
    for d in days:
        rph.current_time = rph.current_time.replace(day=d.day)
        filename = os.path.join(
            settings.CSV_DATA_DIR,
            "%s_%s.csv" % (
                pair, d.strftime("%Y%m%d")
            )
        )
        outfile = open(filename,"w")
        print(filename)
        outfile.write("Time,Ask,Bid,AskVolume,BidVolume\n")

        # Create the random walk for the bid/ask prices
        # with fixed spread between them
        while True:
            tev = rph()
            if rph.current_time.day != d.day:
                outfile.close()
                break
            else:
                ask_volume = 1.0 + np.random.uniform(0.0, 2.0)
                bid_volume = 1.0 + np.random.uniform(0.0, 2.0)

                line = "%s,%s,%s,%s,%s\n" % (
                    rph.current_time.strftime("%d.%m.%Y %H:%M:%S.%f")[:-3],
                    "%0.5f" % tev.ask, "%0.5f" % tev.bid,
                    "%0.2f00" % ask_volume, "%0.2f00" % bid_volume
                )
                outfile.write(line)
