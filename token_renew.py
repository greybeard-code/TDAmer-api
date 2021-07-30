# Program to update the authentication token for TDAMERI-api app
# Run mannaully  before the 90 token expiration, recommend monthly
# See StockMartetOptionsTrading.net for info on trading
# Code by Derek Jones

from tda import orders, utils, auth
from tda.auth import easy_client
from tda.client import Client
from tda.utils import Utils
import json, sys, os
from datetime import datetime, timedelta

import pandas as pd
import config

from selenium import webdriver

print("Checking status of TD Ameritrade authrntication token.")
# Read token
if (os.path.exists(config.TOKEN_PATH) ):
    with open(config.TOKEN_PATH) as file:
        data = json.load(file)
    #print(json.dumps(data, indent=4))

    token_created = pd.to_datetime(data['creation_timestamp'], unit='s')
    token_expires = token_created + timedelta( days=90)
    print("Token Created: ",  str(token_created) )
    print("Token Expires: ", str(token_expires) )
    # delete token if it's expired
    if (token_expires < datetime.now() - timedelta(days=7)):
        print("Authorization token expiring soon. Deleting old token.")
        os.remove(config.TOKEN_PATH)


#  create new token if needed
if not os.path.exists(config.TOKEN_PATH) :

    #Setup Client
    print("Creating new token.")
    try:
        c = auth.client_from_token_file(config.TOKEN_PATH, config.API_KEY)

    except FileNotFoundError:
        from selenium import webdriver

        with webdriver.Chrome() as driver:
            c = auth.client_from_login_flow(driver, config.API_KEY, config.REDIRECT_URI, config.TOKEN_PATH)
    # c = easy_client(
    #         api_key= config.API_KEY,
    #         redirect_uri=config.REDIRECT_URI,
    #         token_path=config.TOKEN_PATH )


    # grab randon stock history to force key generation
    resp = c.get_price_history( "AAPL",
            period_type=Client.PriceHistory.PeriodType.MONTH,
            period=Client.PriceHistory.Period.TWO_MONTHS,
            frequency_type=Client.PriceHistory.FrequencyType.DAILY,
            frequency=Client.PriceHistory.Frequency.DAILY)
    history=resp.json( )

    # Read token
    with open(config.TOKEN_PATH) as file:
            data = json.load(file)
    #print(json.dumps(data, indent=4))

    token_created = pd.to_datetime(data['creation_timestamp'], unit='s')
    token_expires = token_created + timedelta( days=90)
    print("Updated Token Created: ",  str(token_created) )
    print("Updated Token Expires: ", str(token_expires) )

print("Finished.")


