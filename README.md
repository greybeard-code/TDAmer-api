# TD Ameritrade Automated Trading
Automated trading scripts for placing trades on TD Ameritrade based on the strategies from Stock Market Options Trading
https://www.stockmarketoptionstrading.net


## Prereqs
Developed on Python 3.8
```
pip install tda-api
pip install selenium
pip install httpx
```
You will need to install the Chrome Browser and add the chromedriver in a directory in your path (I use /usr/local/bin )
chromedriver - https://sites.google.com/chromium.org/driver/

You will need a TD Ameritrade account with Options permissions 
Register yourself a TD Ameritrade Developer account and get a API key. This is a separate account from your trading account
https://developer.tdameritrade.com/user/me/apps
Create a app and get your "Consumer Key"

Copy the sample_config.py to config.py and add your App Consumer Key and your trading account number

## Running the program
Run token_renew.py first to create the authentication token. Run this every month to see if your token is about to expire. The program will renew your token 7 days before expiration. If the token expires, the scheduled code will not run.

You can run the program after hours to test and make sure the order is working. After it runs, just delete the order at TD Ameritrade or in Think or Swim.

Set up a cron or schedule job to run the 0dte script on Monday & Wednesday at 9:45am and & Fridays at 9:35am. Run the 7dte script on Wednesdays at 3:30pm.  Adjust your time if you're not in eastern time zone. The job needs to change to the directory the script is in so it finds the authentication token. Edit /home/user/TDAmeri-api to match your system.
```
# TD Ameri-api BOT  -- Times updated for Aug 2021 update
55 09 * * MON,WED cd /home/user/TDAmer-api/ && (python3 trade_0dte.py >> trade_0dte.log 2>&1)
35 09 * * FRI     cd /home/user/TDAmer-api/ && (python3 trade_0dte.py >> trade_0dte.log 2>&1)

30 15 * * WED     cd /home/user/TDAmer-api/ && (python3 trade_7dte.py >> trade_7dte.log 2>&1)
30 15 * * MON     cd /home/user/TDAmer-api/ && (python3 trade_BWB_4dte.py >> trade_BWB_4dte.log 2>&1)

```

# WARNING
- No guarantees, this is not stock advice.
- I'm not responsible for any losses, but wouldn't mind if you shared some of the winnings :-)


## Buy me a coffee/donations
https://www.buymeacoffee.com/greybeardcode 

## Updates
2021-0803 - Added new Aug 2021 0dte rules, cleaned up common code, added BWB trade bot
