import requests
import time
import hashlib
import hmac
import os
from base64 import b64encode, b64decode

try:
    KEY = os.environ.get("BTCMARKETS_KEY").encode()
    SECRET = os.environ.get("BTCMARKETS_SECRET").encode()
except AttributeError:
    raise RuntimeError("BTCMARKETS_KEY or BTCMARKETS_SECRET"
                       " environment variables not set.")


BASE_URL = 'https://api.btcmarkets.net'


def get_timestamp():
    return str(round(time.time() * 1000))


def get_headers(signature, timestamp):

    return {
        "Accept": "application/json",
        "Accept-Charset": "UTF-8",
        "Content-Type": "application/json",
        "apikey": KEY,
        "timestamp": timestamp,
        "signature": signature.decode(),
        "User-Agent": "btcmarkets 0.1"
    }


def sign(endpoint, body=None):

    timestamp = get_timestamp()

    payload = endpoint + "\n" + timestamp + "\n"

    if body:
        payload = payload + body

    signature = b64encode(hmac.new(b64decode(SECRET), msg=payload.encode(),
                          digestmod=hashlib.sha512).digest())

    return(signature, timestamp)


def get(endpoint):

    (signature, timestamp) = sign(endpoint)

    url = BASE_URL + endpoint

    r = requests.get(url, headers=get_headers(signature, timestamp))
    return r.json()


def post(endpoint, data):

    (signature, timestamp) = sign(endpoint, data)

    url = BASE_URL + endpoint

    r = requests.post(url, headers=get_headers(signature, timestamp),
                      data=data)
    return r.json()


def get_account_balance():

    content = get('/account/balance')

    print("Current balances:")

    portfolio = 0

    for coin in content:

        if coin['balance'] > 0:

            balance = coin['balance'] / 100000000
            # pending = coin['pendingFunds'] / 100000000
            currency = coin['currency']

            if currency == 'AUD':
                price = 1
            else:
                price = get_tick_price(currency, 'AUD', False)

            worth = price * balance
            portfolio = portfolio + worth

            print('{} - {} [Trading at {}] [Value ${:,.2f} AUD]'.format(
                currency, balance, price, worth))

    print("\nPortfolio balance: ${:,.2f} AUD\n".format(portfolio))

    return


def get_tick_price(in_currency, out_currency, output=True):

    endpoint = '/market/{}/{}/tick'.format(in_currency, out_currency)

    content = get(endpoint)

    if output:
        if 'success' in content and not content['success']:
            return
        print("{} current price: ".format(in_currency))
        print("{} {}\n".format(content['lastPrice'], content['currency']))
        return
    else:
        if 'success' in content and not content['success']:
            return 0
        return(content['lastPrice'])


if __name__ == "__main__":

    get_account_balance()
    # print("\nOther coins:")
    # get_tick_price('LTC', 'BTC', True)
