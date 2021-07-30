# Program to trade SMOT 0dte trades.
# Set up in Cron or scheduler to run at 9:45 am M,W,F
# See StockMartetOptionsTrading.net for info on trading
# Code by Derek Jones


from datetime import datetime, timedelta

import config
import trade_common


# The strategy for each day
# First line is the Day of the week the trade occurs
#     'under' : The stock the option is based on
#     'filter': Which Filter? none. Alpha5, or 21ema
#     'distance': How far a way from ATM for the first strike
#     'direction': Strikes  ITM or OTM
#     'type': PUT or CALL ?
#     'width': How many strikes wide is the vertical?
#     'closing': Close trade at what profit? decimal percent, 0 for let expire
#     'quantity': How many vertical to purchase
#     'target' : Percent of Mid Price for purchase limit

Zero_dte_strategies = {
    'Monday' :{
        'under' : '$SPX.X',
        'filter': 'none',
        'distance': 1,
        'direction': 'OTM',
        'type': 'PUT',
        'width': 1,
        'closing': .75,
        'quantity': 1,
        'target' :.90
    },
    'Wednesday' :{
        'under' : '$SPX.X',
        'filter': 'Alpha5',
        'distance': 2,
        'direction': 'OTM',
        'type': 'PUT',
        'width': 1,
        'closing': .75,
        'quantity': 1,
        'target' :.90
    },
    'Friday' :{
        'under' : '$SPX.X',
        'filter': '21ema',
        'distance': 2,
        'direction': 'OTM',
        'type': 'PUT',
        'width': 1,
        'closing': 0,
        'quantity': 1,
        'target' :.90
    },
}

# Pick Trade - What is today?
# set date range, use datetime objects. Start now and go 7 days forward
# Define the next weekday date for strategies that are day of week specific
# 0=Monday, 2= Wed, 4=Friday
today = datetime.today()

#Pick the trade strategy 
day_of_week = today.weekday()
if day_of_week == 0:
        trade_day="Monday"
        trade_strat =  Zero_dte_strategies[ "Monday"]
        trade_date = today + timedelta( (0-today.weekday()) % 7 )
elif day_of_week == 2:
        trade_day="Wednesday"
        trade_strat =  Zero_dte_strategies[ "Wednesday"]
        trade_date = today + timedelta( (2-today.weekday()) % 7 )
elif day_of_week == 4:
        trade_day="Friday"
        trade_strat =  Zero_dte_strategies[ "Friday"]
        trade_date = today + timedelta( (4-today.weekday()) % 7 )
else:
        trade_day = "Testing-Friday"
        trade_strat =  Zero_dte_strategies[ "Friday"]
        trade_date = today + timedelta( (4-today.weekday()) % 7 )






# Start the logs/ reporting
print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
print(" 0DTE Option Trader for ", trade_day, " on underlying ", trade_strat["under"])
print(" Running at : ", datetime.now())
print("")


##### Common Core #####
trade_common.trading_core( trade_strat, trade_date )

# End log/reporting
print(" ")
print("Finshed at : ", datetime.now())
print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
