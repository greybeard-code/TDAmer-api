

# Set the  API_Key and Account ID for your account
API_KEY = 'your_key_here@AMER.OAUTHAP'
TOKEN_PATH = 'auth-token.json'
REDIRECT_URI = 'https://localhost'
ACCOUNT_ID = 126456789   #trading account


# The strategy for each day
# First line is the Day of the week the trade occurs
#     'under' : The stock the option is based on
#     'filter': Which Filter? none. Alpha5, or 21ema
#     'distance': How far a way from ATM for the first strike
#     'direction': Strikes  ITM or OTM
#     'type': PUT or CALL ?
#     'width': How many strikes wide is the vertical?
#     'closing': Close trade at what profit? decimal percent, 0 for let expire
#     'quantity': How many vertical to purchace
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
