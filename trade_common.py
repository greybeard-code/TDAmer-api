#  Common core of functions  for  trading SMOT  trades.
# See StockMartetOptionsTrading.net for info on trading
# Code by Derek Jones

from tda import orders, utils
from tda.orders.options import bull_put_vertical_open, bull_put_vertical_close
from tda.orders.common import Duration, Session
from tda.auth import easy_client
from tda.client import Client
from tda.utils import Utils
import json, time, httpx
from datetime import datetime, timedelta
import bisect 
import pandas as pd
import config


def trading_core(trade_strat, trade_date  ):
    #import trade strategy and trade date (expiration date)

    # flag to trade or not, used by trades that filter
    make_trade = False

   
    #Setup Client
    c = easy_client(
            api_key= config.API_KEY,
            redirect_uri=config.REDIRECT_URI,
            token_path=config.TOKEN_PATH)


    # test for  filter
    #grab price data
    resp = c.get_price_history( trade_strat["under"],
            period_type=Client.PriceHistory.PeriodType.MONTH,
            period=Client.PriceHistory.Period.TWO_MONTHS,
            frequency_type=Client.PriceHistory.FrequencyType.DAILY,
            frequency=Client.PriceHistory.Frequency.DAILY)
    history=resp.json( )
    df = pd.DataFrame(history["candles"])
    #convert date colum to readable text
    df["date"] = pd.to_datetime(df['datetime'], unit='ms')
    # calculate emas for each
    df["21ema"] = pd.Series.ewm(df["close"], span=21).mean()
    df["8ema"] = pd.Series.ewm(df["close"], span=8).mean()
    df["5ema"] = pd.Series.ewm(df["close"], span=5).mean()
    #clean up unused columns
    del df["volume"]
    del df["datetime"]
    print("Pricing History:")
    print ( df.tail())
    print("")

    if trade_strat["filter"] =='Alpha5' :
            #Is last night's 5ema over day before?
            print("Calculating Alpha 5")
            if df["5ema"].iloc[-1]> df["5ema"].iloc[-2] :
                    print ("Good to trade")
                    make_trade=True

    elif trade_strat["filter"] =='21ema' :
            # Is last night's closing over 21ema? 
            print ("Calculating 21ema")
            if df["close"].iloc[-1] > df["21ema"].iloc[-1] :
                    print ("Good to trade")
                    make_trade=True

    elif trade_strat["filter"] =='8ema' :
            # Is last night's closing over 21ema? 
            print ("Calculating 21ema")
            if df["close"].iloc[-1] > df["21ema"].iloc[-1] :
                    print ("Good to trade")
                    make_trade=True

    elif trade_strat["filter"] =='none' :
            # no filter, proceed
            print("No Filter used")
            make_trade=True

    # Setup chain request
    if trade_strat["type"] =='PUT' :
            trade_type = c.Options.ContractType.PUT
    elif trade_strat["type"] =='CALL' :
            trade_type = c.Options.ContractType.CALL

    # Get the options chain from TDA
    results = c.get_option_chain( trade_strat["under"], 
            contract_type= trade_type,
            strike_count= 10,
            include_quotes=True,
            from_date= trade_date,
            to_date= trade_date )
# need to add multi account support

    results = results.json() # pull out the json data
    if results['status'] == 'FAILED':
        print ("Getting the option chain failed.")
        make_trade = False
        sys.exit()
        
    #grab last price
    last_price_under = results["underlying"]["last"]
    print ("Last price of underlying, ",trade_strat["under"], "- $", last_price_under)
    print ("Option expiration date:", trade_date)

    #print(json.dumps(results, indent=4))
    chain = results["putExpDateMap"] # pull the options chain, enumerated by the strike date
    expirations = list(chain.keys()) # expirations in the chain


    # should only be one expiration date
    chain = chain[expirations[0]] # only one, but pick it
    strikes = list(map(float,chain.keys()))

    ### PUT or CALL?  ITM or OTM?

    # then pick two options that match strategy
    # bisect_left and subtraction for OTM puts
    atm_position =  bisect.bisect_left(strikes,last_price_under)
    atm_strike = strikes[ atm_position]
    print ( "At the Money Strike = ", "{:.2f}".format(atm_strike))
    print ( "Sell OTM Strike     = ", "{:.2f}".format(strikes[ atm_position - 1]))
    print ( "Buy OTM Strike      = ", "{:.2f}".format(strikes[ atm_position - (1+ trade_strat["width"] ) ]))

    # Pull Option leg symbols
    sell_leg = chain[str(strikes[ atm_position - 1] )]  
    sell_leg = sell_leg[0]
    print("Sell leg   :" , sell_leg["symbol"] )

    buy_leg = chain[str(strikes[ atm_position - (1+ trade_strat["width"])])]
    buy_leg = buy_leg[0]
    print("Buy leg    :", buy_leg["symbol"])

    #calculate prices
    price_nat = round(sell_leg['bid'] - buy_leg['ask'],2)
    price_high = round(sell_leg['mark'] - buy_leg['mark'],2)
    price_mid = round( (price_high + price_nat)/2 ,2) # price mid is adv of low & high price
    price_target = round( price_mid * trade_strat["target"] , 2) *100 # lower the target to get better fills
    price_target = (round((price_target/5))*5 ) / 100  # convert to a 5 cent mark

    print("Price Bid    = {:.2f}".format(sell_leg['bid'] )," - Price Ask = {:.2f}".format(buy_leg['ask']), " = Price Nat = ", "{:.2f}".format(price_nat))
    print("Price High   = ", "{:.2f}".format(price_high))
    print("Price Mid    = ", "{:.2f}".format(price_mid))
    print("Price Target = ", "{:.2f}".format(price_target))
    print(" ")

    # Ready the order (PUT or CALL??)
    put_order = bull_put_vertical_open(buy_leg["symbol"],sell_leg["symbol"],trade_strat["quantity"], price_target)
   
    #place the order - support multi accts later
    if make_trade :
            print("Making the trade...")
            r = c.place_order(config.ACCOUNT_ID, put_order)

            print("Order status code - " ,r.status_code)
            if r.status_code == httpx.codes.OK : 
                    order_id = Utils(c, config.ACCOUNT_ID).extract_order_id(r)
                    print ("Order placed, order ID-", order_id )
            else :  
                    print("FAILED - placing the order failed.")


    # wait 5 for order to be submitted & maybe filled
    time.sleep(5)  # wait 5 seconds
    # check if order is filled ? loop?

    #place close order
    if trade_strat["closing"] > 0  and  make_trade :
            print(" Placing closing order.")
            close_price_target = price_target * (1-trade_strat["closing"])
            close_price_target = (round((close_price_target/5))*5 ) / 100  # convert to a 5 cent mark
            put_order = bull_put_vertical_close(buy_leg["symbol"],sell_leg["symbol"],trade_strat["quantity"], close_price_target)
            put_order.set_duration(orders.common.Duration.GOOD_TILL_CANCEL)
            r = c.place_order(config.ACCOUNT_ID, put_order)

            print("Order status code - " ,r.status_code)
            if r.status_code == httpx.codes.OK : 
                    order_id = Utils(c, config.ACCOUNT_ID).extract_order_id(r)
                    print ("Sell to Close order placed, order ID-", order_id )
            else :  
                    print("FAILED - placing the order failed.")

    # Read TDA token to note token expiration
    with open(config.TOKEN_PATH) as file:
            data = json.load(file)
    #print(json.dumps(data, indent=4))
    token_created = pd.to_datetime(data['creation_timestamp'], unit='s')
    token_expires = token_created + timedelta( days=90)
    print(" Authentication Token Created: ",  str(token_created) , " Will Expire: ", str(token_expires) )
    # add warning when nearing expiration
    if (token_expires < datetime.now() - timedelta(days=7)) :
            print("  --**-- Authorization token expiring soon. Run token_renew.py to renew.")
    ### Send data back
    return ;
