#  Common core of functions  for  trading SMOT  trades.
# See StockMartetOptionsTrading.net for info on trading
# Code by Derek Jones

from logging import makeLogRecord
from tda import orders, utils
from tda.orders.options import bull_put_vertical_open, bull_put_vertical_close
from tda.orders.generic import OrderBuilder
from tda.orders.common import (
        Duration,
        OrderStrategyType,
        OrderType,
        Session,
        ComplexOrderStrategyType,
        OptionInstruction,
        Destination
        )
from tda.auth import easy_client
from tda.client import Client
from tda.utils import Utils
import json, time, httpx, sys
from datetime import datetime, timedelta
import bisect 
import pandas as pd
import config

##############################################################################################
def test_filter (filter_name, stock) :
    print("Testing for", filter_name,"filter with", stock,".")
    # flag to trade or not
    make_trade = False
    
    #Setup Client
    c = easy_client(
            api_key= config.API_KEY,
            redirect_uri=config.REDIRECT_URI,
            token_path=config.TOKEN_PATH)

    # test for  filter
    #grab price data
    resp = c.get_price_history( stock,
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
    df["8ema"]  = pd.Series.ewm(df["close"], span=8).mean()
    df["5ema"]  = pd.Series.ewm(df["close"], span=5).mean()
    df["3ema"]  = pd.Series.ewm(df["close"], span=5).mean()

    #clean up unused columns
    del df["volume"]
    del df["datetime"]
    #print("Pricing History:")
    #print ( df.tail())
    print("")

    if filter_name =='Alpha5' :
            #Is last night's 5ema over day before?
            print("Calculating Alpha 5 filter")
            if df["5ema"].iloc[-1]> df["5ema"].iloc[-2] :
                    print ("Good to trade")
                    make_trade=True

    elif filter_name =='CloseOver21' :
            # Is last night's closing over 21ema? 
            print ("Calculating  Close over 21ema")
            if df["close"].iloc[-1] > df["21ema"].iloc[-1] :
                    print ("Good to trade")
                    make_trade=True

    elif filter_name =='8over21' :
            # Is 8ema over 21ema? 
            print ("Calculating 8ema over 21ema")
            if df["8ema"].iloc[-1] > df["21ema"].iloc[-1] :
                    print ("Good to trade")
                    make_trade=True

    elif filter_name =='3over8' :
            # Is 3ema over 8ema 
            print ("Calculating 3ema over 8ema")
            if df["3ema"].iloc[-1] > df["8ema"].iloc[-1] :
                    print ("Good to trade")
                    make_trade=True

    elif filter_name =='Alpha3' :
            #Is last night's 3ema over day before?
            print("Calculating Alpha 3 filter")
            if df["3ema"].iloc[-1]> df["3ema"].iloc[-2] :
                    print ("Good to trade")
                    make_trade=True

    elif filter_name =='none' :
            # no filter, proceed
            print("No Filter used")
            make_trade=True
    else :
            print("ERROR -- Filter not found!")   
            make_trade=False     

    return make_trade

##############################################################################
def nicklefy (org_price):
    # Convert a price to the nearest nickle. SPX options are priced at 5 cent increments 
    new_price = org_price  * 100 #bring up to whole
    new_price= round( new_price/5, 0) *5  / 100  # convert to a 5 cent mark
    new_price = round(new_price, 2)
    return new_price

##############################################################################
def check_fulfillment (order, order_id, org_price, decrement):
    # check to see if order is filled.
    #Need existing order object, the TDA order_id, 
    #     the original price, and how much to subtract each loop
    make_trade = True
    #Setup Client
    client = easy_client(
            api_key= config.API_KEY,
            redirect_uri=config.REDIRECT_URI,
            token_path=config.TOKEN_PATH)

    order_status = client.get_order(order_id, config.ACCOUNT_ID).json()
    print(json.dumps(order_status, indent=4))  # testing
    print("Order status:", order_status['status'])
    loop_count =0
    lower_price = org_price
    while order_status['status'] not in ['FILLED', 'REJECTED', 'CANCELED'] :
        loop_count += 1
        print(" Changing price by",decrement,"and reordering. ",loop_count)
        #change price
        lower_price = (lower_price - decrement ) #lower price 
        lower_price= nicklefy( lower_price )  # convert to a 5 cent mark
        print("New price : {:.2f}".format(lower_price))
        order = order.copy_price(lower_price) 
        r = client.replace_order(config.ACCOUNT_ID, order_id, order)

        print("Order status code - " ,r.status_code)
        if r.status_code < 400 : #http codes under 400 are success. usually 200 or 201
            order_id = Utils(client, config.ACCOUNT_ID).extract_order_id(r)
            print ("Order placed, order ID-", order_id )
        else :  
            print("FAILED - placing the order failed.")
            make_trade = False  # stop the closing order
            break


        time.sleep(60)  # wait 60 seconds
        if loop_count == 5:  #TD Ameri fails the order at this point
             break


    return order_id, make_trade
        
##############################################################################
def trading_vertical(trade_strat, trade_date  ):
    #import trade strategy and trade date (expiration date)

    #Setup Client
    c = easy_client(
            api_key= config.API_KEY,
            redirect_uri=config.REDIRECT_URI,
            token_path=config.TOKEN_PATH)
  
   
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
        print ("Getting the option chain failed for date", trade_date)
        make_trade = False
        sys.exit()
        
    #grab last price
    last_price_under = results["underlying"]["last"]
    print ("Last price of underlying, ",trade_strat["under"], "- $", last_price_under)
    print ("Option expiration date:", trade_date)

    #what did we pull? TESTING
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
    sell_leg['mid'] =round((sell_leg['bid'] + sell_leg['ask'])/2,2)
    buy_leg['mid'] = round((buy_leg['bid']  + buy_leg['ask'])/2,2)

    price_mid = round( sell_leg['mid'] - buy_leg['mid'],2) 
    price_target = round( price_mid * trade_strat["target"] , 2) # adjust the target to get better fills
    # XSP doesn't do nickle steps in pricing, need to add code to not use steps
    price_target = nicklefy(price_target)  # convert to a 5 cent mark

    print("Price Bid    = {:.2f}".format(sell_leg['bid'] )," - Price Ask = {:.2f}".format(buy_leg['ask']), " = Price Nat = ", "{:.2f}".format(price_nat))
    print("Price High   = {:.2f}".format(price_high))
    print("Price Mid    = {:.2f}".format(price_mid))
    print("Price Target = {:.2f}".format(price_target), "(",trade_strat["target"],")" )
    print(" ")

    # Ready the order (PUT or CALL??)
    put_order = bull_put_vertical_open(buy_leg["symbol"],sell_leg["symbol"],trade_strat["quantity"], price_target)
   
    #place the order - support multi accts later
  
    print("Making the trade...")
    r = c.place_order(config.ACCOUNT_ID, put_order)

    print("Order status code - " ,r.status_code)
    if r.status_code < 400 : #http codes under 400 are success. usually 200 or 201
            order_id = Utils(c, config.ACCOUNT_ID).extract_order_id(r)
            print ("Order placed, order ID-", order_id )
    else :  
            print("FAILED - placing the order failed.")
            make_trade = False  # stop the closing order


    # wait 5 for order to be submitted & maybe filled
    time.sleep(60)  # wait 60 seconds
    # Need to add code to  check if order is filled ? loop?
    order_id, make_trade = check_fulfillment(put_order, order_id,price_target, .05)



    #place close order
    if trade_strat["closing"] > 0 and make_trade  :
            close_price_target = round(price_target * (1-trade_strat["closing"]), 2)  #Set limit order at the inverse of the profit goal
            close_price_target = nicklefy(close_price_target)  # convert to a 5 cent mark
            print(" Placing closing order at ",close_price_target)
            put_order = bull_put_vertical_close(buy_leg["symbol"],sell_leg["symbol"],trade_strat["quantity"], close_price_target)
            put_order.set_duration(orders.common.Duration.GOOD_TILL_CANCEL)
            r = c.place_order(config.ACCOUNT_ID, put_order)

            print("Order status code - " ,r.status_code)
            if r.status_code  < 400 : #http codes under 400 are success. usually 200 or 201: 
                    order_id = Utils(c, config.ACCOUNT_ID).extract_order_id(r)
                    print ("Sell to Close order placed, order ID-", order_id )
            else :  
                    print("FAILED - placing the order failed.")

 
    return 

##########################################################################################
def check_auth_token ():
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
    return

# code to send logs via email
# future

##########################################################################################
def trading_butterfly(trade_strat, trade_date  ):
    #import trade strategy and trade date (expiration date)

    #Setup Client
    c = easy_client(
            api_key= config.API_KEY,
            redirect_uri=config.REDIRECT_URI,
            token_path=config.TOKEN_PATH)
  
   
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


    chain = results["putExpDateMap"] # pull the options chain, enumerated by the strike date
    expirations = list(chain.keys()) # expirations in the chain  
    # should only be one expiration date
  # should only be one expiration date
    chain = chain[expirations[0]] # only one, but pick it
    
    #what did we pull? TESTING
    #print(json.dumps(chain , indent=4))

    # Find the Delta 55
    for strike in chain :
            data= chain[strike]
            #print(data)
            #print(strike, " Delta:", data[0]['delta'] ) 
            if abs(data[0]['delta'] ) > 0.55 :
                print(" Delta over 55:",strike, " Delta:", data[0]['delta'] ) 
                body_strike = float(strike)
                break
        
    
    strikes = list(map(float,chain.keys()))
    body_position = strikes.index(body_strike)
       

    # Buy at 2 lower and 1 higher
    print ( "Delta 55 Body = ", "{:.2f}".format(strikes[body_position]))
    print ( "Lower Strike  = ", "{:.2f}".format(strikes[ body_position - 2]))
    print ( "Higher Strike = ", "{:.2f}".format(strikes[ body_position + 1 ]))

    # Pull Option leg symbols
    sell_leg = chain[str(strikes[ body_position ] )]  
    sell_leg = sell_leg[0]
    print("Sell (body) leg  :" , sell_leg["symbol"] )

    buy_lower_leg = chain[str(strikes[ body_position - 2 ])]
    buy_lower_leg = buy_lower_leg[0]
    print("Buy lower leg    :", buy_lower_leg["symbol"])

    buy_higher_leg = chain[str(strikes[ body_position + 1 ])]
    buy_higher_leg = buy_higher_leg[0]
    print("Buy higher leg   :", buy_higher_leg["symbol"])

    # Find the mid points of each leg
    sell_leg['mid']       = (sell_leg['bid'] + sell_leg['ask'])/2
    buy_lower_leg['mid']  = (buy_lower_leg['bid'] + buy_lower_leg['ask'])/2
    buy_higher_leg['mid'] = (buy_higher_leg['bid'] + buy_higher_leg['ask'])/2

#     print("Sell Leg ", sell_leg['bid'] , sell_leg['ask'], sell_leg['mid'],sell_leg['mark'])
#     print("Buy Low  ", buy_lower_leg['bid'] , buy_lower_leg['ask'], buy_lower_leg['mid'],buy_lower_leg['mark']) 
#     print("Buy High ", buy_higher_leg['bid'] , buy_higher_leg['ask'], buy_higher_leg['mid'],buy_higher_leg['mark']) 
    #print(sell_leg)
    
    # Calculate prices
    price_nat  = round((sell_leg['bid'] *2) - (buy_lower_leg['ask'] +  buy_higher_leg['ask']),2)
    price_high = round((sell_leg['mark'] *2) - (buy_lower_leg['mark'] + buy_higher_leg['mark']) ,2)
    price_mid  = round((sell_leg['mid'] *2) - (buy_lower_leg['mid'] + buy_higher_leg['mid']) ,2)
    price_target = round( price_mid * trade_strat["target"] , 2) # lower the target to get better fills
    price_target = nicklefy(price_target)  # convert to a 5 cent mark

    print("Price Nat    = ", "{:.2f}".format(price_nat))
    print("Price High   = ", "{:.2f}".format(price_high))
    print("Price Mid    = ", "{:.2f}".format(price_mid))
    print("Price Target = ", "{:.2f}".format(price_target))
    print(" ")

    # Ready the order (PUT or CALL??)
    
    order = OrderBuilder() \
        .set_complex_order_strategy_type(ComplexOrderStrategyType.BUTTERFLY) \
        .set_duration(Duration.DAY) \
        .set_order_strategy_type(OrderStrategyType.SINGLE) \
        .set_order_type(OrderType.NET_CREDIT) \
        .copy_price(price_target) \
        .set_quantity(trade_strat["quantity"] ) \
        .set_requested_destination(Destination.AUTO) \
        .set_session(Session.NORMAL) \
        .add_option_leg(OptionInstruction.BUY_TO_OPEN, buy_higher_leg["symbol"], trade_strat["quantity"] ) \
        .add_option_leg(OptionInstruction.SELL_TO_OPEN, sell_leg["symbol"] , trade_strat["quantity"] *2) \
        .add_option_leg(OptionInstruction.BUY_TO_OPEN, buy_lower_leg["symbol"] , trade_strat["quantity"] )


    #place the order - support multi accts later
  
    print("Making the trade...")
    r = c.place_order(config.ACCOUNT_ID, order)

    print("Order status code - " ,r.status_code)
    if r.status_code < 400 : #http codes under 400 are success. usually 200 or 201
                order_id = Utils(c, config.ACCOUNT_ID).extract_order_id(r)
                print ("Order placed, order ID-", order_id )
    else :  
                print("FAILED - placing the order failed.")
                make_trade = False  # stop the closing order


    # wait 5 for order to be submitted & maybe filled
    time.sleep(60)  # wait 60 seconds
    # check if order is filled , send starting price too
    order_id, make_trade = check_fulfillment(order, order_id,price_target, .05)
  
    #place close order
    if trade_strat["closing"] > 0  and make_trade :
            print(" Placing closing order.")
            close_price_target = price_target * (1-trade_strat["closing"])
            close_price_target = (round((close_price_target/5))*5 ) / 100  # convert to a 5 cent mark
            put_order = bull_put_vertical_close(buy_leg["symbol"],sell_leg["symbol"],trade_strat["quantity"], close_price_target)
            put_order.set_duration(orders.common.Duration.GOOD_TILL_CANCEL)
            ###r = c.place_order(config.ACCOUNT_ID, put_order)

            print("Order status code - " ,r.status_code)
            if r.status_code  < 400 : #http codes under 400 are success. usually 200 or 201: 
                    order_id = Utils(c, config.ACCOUNT_ID).extract_order_id(r)
                    print ("Sell to Close order placed, order ID-", order_id )
            else :  
                    print("FAILED - placing the order failed.")

 
    return 