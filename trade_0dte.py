# Program to trade SMOT 0dte trades.
# Set up in Cron or scheduler to run at 9:45 am M,W,F
# See StockMartetOptionsTrading.net for info on trading
# Code by Derek Jones

from tda import orders, utils
from tda.orders.options import bull_put_vertical_open, bull_put_vertical_close
from tda.orders.common import Duration, Session
from tda.auth import easy_client
from tda.client import Client
from tda.utils import Utils
import json, time
from datetime import datetime, timedelta
import bisect 
import pandas as pd
import config

# Make sure we're in our script direcotry 
os.chdir(os.path.dirname(sys.argv[0]))

# flag to trade or not, used by trades that filter
make_trade = False

# Pick Trade - What is today?
# set date range, use datetime objects. Start now and go 7 days forward
# Define the next weekday date for strategies that are day of week specific
# 0=Monday, 2= Wed, 4=Friday
today = datetime.today()

#trade_strat is a list
day_of_week = today.weekday()
if day_of_week == 0:
        trade_day="Monday"
        trade_strat =  config.Zero_dte_strategies[ "Monday"]
        trade_date = today + timedelta( (0-today.weekday()) % 7 )
elif day_of_week == 2:
        trade_day="Wednesday"
        trade_strat =  config.Zero_dte_strategies[ "Wednesday"]
        trade_date = today + timedelta( (2-today.weekday()) % 7 )
elif day_of_week == 4:
        trade_day="Friday"
        trade_strat =  config.Zero_dte_strategies[ "Friday"]
        trade_date = today + timedelta( (4-today.weekday()) % 7 )
else:
        trade_day = "Testing -Friday"
        trade_strat =  config.Zero_dte_strategies[ "Friday"]
        trade_date = today + timedelta( (4-today.weekday()) % 7 )


#Setup Client
c = easy_client(
        api_key= config.API_KEY,
        redirect_uri=config.REDIRECT_URI,
        token_path=config.TOKEN_PATH)



# Monday Strategy - should change this to a object later
# trade_under = "$SPX.X"  # Underlying Stock for option trade
# trade_filter = 0  # place holder for Entry filter 
# trade_strike_count = 2  # how far away from ATM
# trade_strike_direction = "OTM"
# 
# trade_strike_width = 1 # how many strikes wide
# trade_close_rule = .75
# trade_strategy = c.Options.Strategy.VERTICAL
# trade_qty = 1 # number to buy
# trade_price_target = .90  # Percent of Mid Price to target order limit
# #trade_execute_time = datetime.datetime.strptime('9:45, '%T').time()


#strike_range= trade_strike_direction, 

# Start the logs/ reporting
print ("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
print(" 0DTE Option Trader for ", trade_day, " on underlying ", trade_strat["under"])
print(" Running at : ", datetime.now())
print("")

# test for  filter
#grab price data
resp = c.get_price_history( trade_strat["under"],
        period_type=Client.PriceHistory.PeriodType.MONTH,
        period=Client.PriceHistory.Period.TWO_MONTHS,
        frequency_type=Client.PriceHistory.FrequencyType.DAILY,
        frequency=Client.PriceHistory.Frequency.DAILY)
history=resp.json( )
df = pd.DataFrame(history["candles"])
df["date"] = pd.to_datetime(df['datetime'], unit='ms')
df["21ema"] = pd.Series.ewm(df["close"], span=21).mean()
df["5ema"] = pd.Series.ewm(df["close"], span=5).mean()
print ( df.tail())

if trade_strat["filter"] =='Alpha5' :
        # get  10 days of pricing and calulate 5ema for each
        #Is last night's 5ema over day before?
        print("Calculating Alpha 5")
        if df["5ema"].iloc[-1]> df["5ema"].iloc[-2] :
                print ("Good to trade")
                make_trade=True

elif trade_strat["filter"] =='21ema' :
        # get  30 days of pricing and calulate 21ema for each
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

results = results.json() # pull out the json data
if results['status'] == 'FAILED':
    print ("Getting the option chain failed")
    make_trade = False
    sys.exit()
    
#grab last price
last_price_under = results["underlying"]["last"]
print ("Last Price of underlying, ",trade_strat["under"], "- $", last_price_under)

#print(json.dumps(results, indent=4))
chain = results["putExpDateMap"] # pull the options chain, enumerated by the strike date
expirations = list(chain.keys()) # expirations in the chain


# should only be one exparation date
chain = chain[expirations[0]] # only one, but pick it
strikes = list(map(float,chain.keys()))

### PUT or CALL?  ITM or OTM?

# then pick two options that match strategy
# bisect_left and subtraction for OTM puts
atm_position =  bisect.bisect_left(strikes,last_price_under)
atm_strike = strikes[ atm_position]
print ( "At the Money Strike = ", atm_strike)
print ( "Sell OTM Strike = ", strikes[ atm_position - 1])
print ( "Buy OTM Strike = ", strikes[ atm_position - (1+ trade_strat["width"] ) ])

# Pull Option leg symbols
sell_leg = chain[str(strikes[ atm_position - 1] )]  
sell_leg = sell_leg[0]
print("Sell leg-", sell_leg["symbol"] )

buy_leg = chain[str(strikes[ atm_position - (1+ trade_strat["width"])])]
buy_leg = buy_leg[0]
print("Buy leg-", buy_leg["symbol"])

#calculate prices
price_nat = round(sell_leg['bid'] - buy_leg['ask'],2)
price_high = round(sell_leg['mark'] - buy_leg['mark'],2)
price_mid = round( (price_high + price_nat)/2 ,2) # price mid is adv of low & high price
price_target = round( price_mid * trade_strat["target"] , 2) *100 # lower the target to get better fills
price_target = (round((price_target/5))*5 ) / 100  # convert to a 5 cent mark

print("Price Bid    = ", sell_leg['bid'] ," - Price Ask", buy_leg['ask'])
print("Price Nat    = ", sell_leg['bid'] ," - ", buy_leg['ask'], "=",price_nat)
print("Price High   = ", price_high)
print("Price Mid    = ", price_mid)
print("Price Target = ", price_target)
print(" ")

# Ready the order (PUT or CALL??)
put_order = bull_put_vertical_open(buy_leg["symbol"],sell_leg["symbol"],trade_strat["quantity"], price_target)

#place the order - support multi accts later
if make_trade :
        print("Making the trade...")
        r = c.place_order(config.ACCOUNT_ID, put_order)

        print("Order status code - " ,r.status_code)

        order_id = Utils(c, config.ACCOUNT_ID).extract_order_id(r)
        print ("Order placed, order ID-", order_id )

# need to figure out how to place a limit order to close position
time.sleep(5)  # wait 5 seconds
# check if order is filled ? loop?

#place close order
if trade_strat["closing"] > 0 :
        print(" Placing closing order.")
        close_price_target = price_target * trade_strat["closing"]
        put_order = bull_put_vertical_close(buy_leg["symbol"],sell_leg["symbol"],trade_strat["quantity"], close_price_target)
        put_order.set_duration(orders.common.Duration.GOOD_TILL_CANCEL)
        r = c.place_order(config.ACCOUNT_ID, put_order)

        print("Order status code - " ,r.status_code)

        order_id = Utils(c, config.ACCOUNT_ID).extract_order_id(r)
        print ("Sell to Close order placed, order ID-", order_id )

# Read TDA token to note token exparation
with open(config.TOKEN_PATH) as file:
        data = json.load(file)
#print(json.dumps(data, indent=4))
token_created = pd.to_datetime(data['creation_timestamp'], unit='s')
token_expires = token_created + timedelta( days=90)
print(" Authentication Token Created: ",  str(token_created) , " Will Expire: ", str(token_expires) )
# add warning when nearing exparation
if (token_expires < datetime.now -timedelta(days=7)) :
        print("  --**-- Authorization token expiring soon. Run token_renew.py to renew.")

# End log/reporting
print(" ")
print("Finshed at : ", datetime.now())
print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
