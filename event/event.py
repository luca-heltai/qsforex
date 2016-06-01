class Event(object):
    pass


class TickEvent(Event):
    def __init__(self, instrument, time, bid, ask):
        self.type = 'TICK'
        self.instrument = instrument
        self.time = time
        self.bid = bid
        self.ask = ask

    def __str__(self):
        return "Type: {0!s}, Instrument: {1!s}, Time: {2!s}, Bid: {3!s}, Ask: {4!s}".format(
            str(self.type), str(self.instrument), 
            str(self.time), str(self.bid), str(self.ask)
        )

    def __repr__(self):
        return str(self)


class SignalEvent(Event):
    def __init__(self, instrument, order_type, side, time):
        self.type = 'SIGNAL'
        self.instrument = instrument
        self.order_type = order_type
        self.side = side
        self.time = time  # Time of the last tick that generated the signal

    def __str__(self):
        return "Type: {0!s}, Instrument: {1!s}, Order Type: {2!s}, Side: {3!s}".format(
            str(self.type), str(self.instrument), 
            str(self.order_type), str(self.side)
        )

    def __repr__(self):
        return str(self)


class OrderEvent(Event):
    def __init__(self, instrument, units, order_type, side):
        self.type = 'ORDER'
        self.instrument = instrument
        self.units = units
        self.order_type = order_type
        self.side = side

    def __str__(self):
        return "Type: {0!s}, Instrument: {1!s}, Units: {2!s}, Order Type: {3!s}, Side: {4!s}".format(
            str(self.type), str(self.instrument), str(self.units),
            str(self.order_type), str(self.side)
        )

    def __repr__(self):
        return str(self)