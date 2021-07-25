# TD Ameritrade Automated Trading
Automated trading scripts for placing 0 days to exparation trades on TD Ameritrrade based on the strategies for Stock Market Options Trading
https://www.stockmarketoptionstrading.net


## Prereqs
Developed on Pyton 3.8
```
pip install tda-api
pip install selenium
```
You will need to install the Chrome Browser and add the chromedriver in the same directory as the scripts
chromedriver - https://sites.google.com/chromium.org/driver/

You will need a TD Ameritrade account with Options permissions 
Register yourself a TD Ameritrade Developer account and get a API key. This is a separate account from your trading account
https://developer.tdameritrade.com/user/me/apps
Create a app and get your "Consumer Key"

Copy the sample_config.py to config.py and add your App Consumer Key and your trading account number

## Running the program
You can run the program after hours to test and make sure the order is working. After it runs, just delete the order at TD Ameritrade or in Think or Swim.

Set up a cron or schedule job to run the script on Monday, Wednesday, & Fridays at 9:45am

# WARNING
- No guarantees, this is not stock advice.
- I'm not responsible for any losses, but wouldn't mind if you shared some of the winnings :-)


## Buy me a coffe/donations
soon.