# Program to trade SMOT 30dte trades.
# Set up in Cron or scheduler to run at 3:30pm on Tuesdays

# See StockMartetOptionsTrading.net for info on trading
# Code by Derek Jones

from datetime import datetime, timedelta
import config
import trade_common


# The strategy, Using Main incase we want to add others later
#     'under' : The stock the option is based on
#     'filter': Which Filter? none. Alpha5, or 21ema
#     'distance': How far a way from ATM for the first strike 
#           OR 
#         'delta': What delta for the sell strike
#     'direction': Strikes  ITM or OTM
#     'type': PUT or CALL ?
#     'width': How many strikes wide is the vertical?
#     'closing': Close trade at what profit? decimal percent, 0 for let expire
#     'quantity': How many vertical to purchase
#     'target' : Percent of Mid Price for purchase limit
# Use $SPX.X for large accounts, $XSP.X  for smaller

strategies = {
    'Main' :{
        'under' : '$SPX.X',
        'filter': 'CloseOver21',
        'delta': 45,
        'direction': 'OTM',
        'type': 'PUT',
        'width': 2,
        'closing': 0,
        'quantity': 1,
        'target' : 1
    },
}


# set date range, use datetime objects. Start now and go 7 days forward
# 0=Monday, 2= Wed, 4=Friday
today = datetime.today()


print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")

# only run this on Tue
if today.weekday() == 1:
#if True:
    trade_day="Tuesday"
    trade_strat =  strategies[ "Main"]
    trade_date = today + timedelta( days=30)
    # make sure trade_date is a option day (M,W,or F)
    while trade_date.weekday() != 4:
        #print("Moving up to next trade day:", trade_date.strftime("%D" ), trade_date.weekday())
        trade_date = trade_date + timedelta( days=1)


    # Start the logs/ reporting
    print(" 30DTE Option Trader for ", trade_day, " on underlying ", trade_strat["under"])
    print(" Running at : ", datetime.now())
    print("")

    ##### Common Core #####

    #test the filter
    make_trade = trade_common.test_filter(trade_strat["filter"], trade_strat["under"])

    if make_trade:
        trade_common.trading_vertical( trade_strat, trade_date )

    trade_common.check_auth_token

    # End log/reporting
    print(" ")
    print("Finshed at : ", datetime.now())
else:
    print(" ERROR - Only run this on Wednesday")

print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
