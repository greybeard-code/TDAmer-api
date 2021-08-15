# Program to trade SMOT 0dte trades.
# Set up in Cron or scheduler to run at 3:30pm on Wednesdays

# See StockMartetOptionsTrading.net for info on trading
# Code by Derek Jones

from datetime import datetime, timedelta
import holidays
import config
import trade_common



# The strategy, Using Main incase we want to add others later
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

# This is the Broken Wing Butterfly strategy.
# 3ema > 8ema, Sell 2 Delta 55 strikes, Buy 1 - 2 strikes lower, Buy 1 -1 strike higher.
# Use $SPX.X for large accounts, $XSP.X for smaller

BWB_4_dte_strategies = {
    'Main' :{
        'under' : '$SPX.X',
        'filter': '3over8',
        'delta': 55,
        'type' : 'PUT',
        'closing': 0,
        'quantity': 1,
        'target' : 1
    },
}


# Pick Trade - What is today?
# set date range, use datetime objects. Start now and go 7 days forward
# Define the next weekday date for strategies that are day of week specific
# 0=Monday, 2= Wed, 4=Friday
today = datetime.today()

#trade_strat is a list
day_of_week = today.weekday()

trade_day="Friday"
trade_strat =  BWB_4_dte_strategies[ "Main"]
trade_date = today + timedelta( (4-today.weekday()) % 7 )


# Start the logs/ reporting
print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
print(" Broken Wing Butterfly Option Trader for ", trade_day," on underlying ", trade_strat["under"])
print(" Running at : ", datetime.now())
print("")

##### Common Core #####
#test the filter
make_trade = trade_common.test_filter(trade_strat["filter"], trade_strat["under"])

# need to check if market is open On Monday and Friday
if today in holidays.US() :
    make_trade =False
if trade_date in holidays.US():
    make_trade = False


if make_trade:
    trade_common.trading_butterfly( trade_strat, trade_date )

trade_common.check_auth_token

# End log/reporting
print(" ")
print("Finshed at : ", datetime.now())
print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
