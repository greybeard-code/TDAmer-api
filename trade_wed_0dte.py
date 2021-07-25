from tda import utils
from tda.orders.options import bull_put_vertical_open, bull_put_vertical_close
from tda.orders.common import Duration, Session
from tda.auth import easy_client
from tda.client import Client
from tda.utils import Utils
import json
from datetime import datetime, timedelta
import bisect , httpx
import config

#Setup Client
c = easy_client(
        api_key= config.API_KEY,
        redirect_uri=config.REDIRECT_URI,
        token_path=config.TOKEN_PATH)



# set date range, use datetime objects. Start now and go 7 days forward
# Define the next weekday date for strategies that are day of week specific
# 0=Monday, 2= Wed, 4=Friday
today = datetime.today()
Monday = today + timedelta( (0-today.weekday()) % 7 )
Wednesday = today + timedelta( (2-today.weekday()) % 7 )
Friday = today + timedelta( (4-today.weekday()) % 7 )


# Monday Strategy - should change this to a object later
trade_under = "$SPX.X"  # Underlying Stock for option trade
trade_filter = 0  # place holder for Entry filter 
trade_strike_count = 2  # how far away from ATM
trade_strike_direction = "OTM"
trade_type = c.Options.ContractType.PUT
trade_strike_width = 1 # how many strikes wide
trade_close_rule = .75
trade_strategy = c.Options.Strategy.VERTICAL
trade_day = Wednesday
trade_qty = 1 # number to buy
trade_price_target = .90  # Percent of Mid Price to target order limit
#trade_execute_time = datetime.datetime.strptime('9:45, '%T').time()


#strike_range= trade_strike_direction, 

# Start the logs/ reporting
print ("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
print(" 0DTE Option Trader for ", trade_day)
print(" Running at : ", datetime.now())
print("")

# Get the options chain from TDA
results = c.get_option_chain( trade_under, 
        contract_type= trade_type,
        
        strike_count= 10,
        include_quotes=True,
        from_date= trade_day,
        to_date= trade_day )

results = results.json() # pull out the json data
if results['status'] == 'FAILED':
    print ("Getting the option chain failed")
    # need to add exit here
    
#grab last price
last_price_under = results["underlying"]["last"]
print ("Last Price of underlying, ",trade_under, "- $", last_price_under)

#print(json.dumps(results, indent=4))
chain = results["putExpDateMap"] # pull the options chain, enumerated by the strike date
expirations = list(chain.keys()) # expirations in the chain


# should only be one exparation date
chain = chain[expirations[0]] # only one, but pick it
strikes = list(map(float,chain.keys()))


# then pick two options that match strategy
# bisect_left and subtraction for OTM puts
atm_position =  bisect.bisect_left(strikes,last_price_under)
atm_strike = strikes[ atm_position]
print ( "At the Money Strike = ", atm_strike)
print ( "Sell OTM Strike = ", strikes[ atm_position - 1])
print ( "Buy OTM Strike = ", strikes[ atm_position - (1+ trade_strike_width) ])

# Pull Option leg symbols
sell_leg = chain[str(strikes[ atm_position - 1] )]  
sell_leg = sell_leg[0]
print("Sell leg-", sell_leg["symbol"] )

buy_leg = chain[str(strikes[ atm_position - (1+ trade_strike_width)])]
buy_leg = buy_leg[0]
print("Buy leg-", buy_leg["symbol"])

#calculate prices
price_nat = round(sell_leg['bid'] - buy_leg['ask'],2)
price_high = round(sell_leg['mark'] - buy_leg['mark'],2)
price_mid = round( (price_high + price_nat)/2 ,2) # price mid is adv of low & high price
price_target = price_mid * trade_price_target # lower the target to get better fills

print("Price Bid    = ", sell_leg['bid'] ," - Price Ask", buy_leg['ask'])
print("Price Nat    = ", sell_leg['bid'] ," - ", buy_leg['ask'], "=",price_nat)
print("Price High   = ", price_high)
print("Price Mid    = ", price_mid)
print("Price Target = ", price_target)
print(" ")

# Ready the order
put_order = bull_put_vertical_open(buy_leg["symbol"],sell_leg["symbol"],trade_qty, price_target)

#place the order
r = c.place_order(config.ACCOUNT_ID, put_order)

print("Order status code - " ,r.status_code)

order_id = Utils(c, config.ACCOUNT_ID).extract_order_id(r)
print ("Order placed, order ID-", order_id )

# need to figure out how to place a limit order to close position


# End log/reporting
print(" ")
print("Finnshed at : ", datetime.now())
print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
