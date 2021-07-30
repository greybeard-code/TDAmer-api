# Program to trade SMOT 0dte trades.
# Set up in Cron or scheduler to run at 3:30pm on Wednesdays

# See StockMartetOptionsTrading.net for info on trading
# Code by Derek Jones

from datetime import datetime, timedelta
import config
import trade_common



# Pick Trade - What is today?
# set date range, use datetime objects. Start now and go 7 days forward
# Define the next weekday date for strategies that are day of week specific
# 0=Monday, 2= Wed, 4=Friday
today = datetime.today()

#trade_strat is a list
day_of_week = today.weekday()

trade_day="Wednesday"
trade_strat =  config.Seven_dte_strategies[ "Main"]
trade_date = today + timedelta( (2-today.weekday()) % 7 )


# Start the logs/ reporting
print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
print(" 7DTE Option Trader for ", trade_day, " on underlying ", trade_strat["under"])
print(" Running at : ", datetime.now())
print("")

##### Common Core #####
trade_common.trading_core( trade_strat, trade_date )

# End log/reporting
print(" ")
print("Finshed at : ", datetime.now())
print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
