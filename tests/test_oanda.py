from datetime import datetime
import requests
import oandapy
import json
import os

oanda_access_token = os.environ.get('OANDA_API_ACCESS_TOKEN', None)
oanda_account_id = os.environ.get('OANDA_API_ACCOUNT_ID', None)
instruments = "EUR_USD"

def test_rest_connection():
    # Initiate a connection, and get current EUR_USD price
    oanda = oandapy.API(environment="live",
                        access_token=oanda_access_token)
    
    response = oanda.get_prices(instruments="EUR_USD")
    prices = response.get("prices")
    buy_price = prices[0].get("bid")


def connect_to_stream():
    # Replace the following variables with your personal ones
    domain = 'stream-fxtrade.oanda.com'


    try:
        s = requests.Session()
        url = "https://" + domain + "/v1/prices"
        headers = {'Authorization' : 'Bearer ' + oanda_access_token,
                   'X-Accept-Datetime-Format' : 'unix'}
        
        params = {'instruments' : instruments, 'accountId' : oanda_account_id}
        req = requests.Request('GET', url, headers = headers, params = params)
        pre = req.prepare()
        resp = s.send(pre, stream = True, verify = True)
        return resp
    except Exception as e:
        s.close()
        print "Caught exception when connecting to stream\n" + str(e) 

def test_stream():
    display_heartbeat = True
    max_lines = 5
    response = connect_to_stream()
    if response.status_code != 200:
        print response.text
        return
    lineno = 0
    for line in response.iter_lines(1):
        if line:
            try:
                msg = json.loads(line)
            except Exception as e:
                print "Caught exception when converting message into json\n" + str(e)
                return
            
            if display_heartbeat:
                print line
            else:
                if "instrument" in msg or "tick" in msg:
                    print line
            lineno += 1
            if lineno >= max_lines:
                break
