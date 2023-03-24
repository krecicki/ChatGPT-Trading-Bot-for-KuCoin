

# These are the time frame you can use:
# {'1m': '1min', '3m': '3min', '5m': '5min', '15m': '15min', '30m': '30min', 
# '1h': '1hour', '2h': '2hour', '4h': '4hour', '6h': '6hour', '8h': '8hour', 
# '12h': '12hour', '1d': '1day', '1w': '1week'}

import ccxt
from time import sleep
from datetime import datetime
import openai

# Replace EXCHANGE_NAME with the name of the exchange you want to use
exchange_name = 'kucoin'

# Instantiate the Exchange class
exchange = getattr(ccxt, exchange_name)()

# Set sandbox mode to True or False
exchange.set_sandbox_mode(enabled=False)

# Set your API keys
exchange.apiKey = ''
exchange.secret = ''
exchange.password = ''

# Set the symbol you want to trade on Kucoin
symbol = 'BTC/USDT'

## Start the trading script
while True:
    try:

        # Batch streaming data from KuCoin it uses a pair
        # and a window time frame
        data = exchange.fetch_ohlcv(symbol, '1h', limit=1)
        #print(data)

        # Create an infinite loop to trade continuously
        while True:
            # Fetch the current ticker information for the symbol
            print('# Fetch the current ticker information for the symbol')
            try:
                ticker = exchange.fetch_ticker(symbol)
            except:
                continue

            # Check the current bid and ask prices
            print('# Check the current bid and ask prices')
            bid = ticker['bid']
            ask = ticker['ask']

            # Calculate the midpoint of the bid and ask prices
            print('# Calculate the midpoint of the bid and ask prices')
            midpoint = (bid + ask) / 2


            # KuCoin fee per transcation
            fee = .001

            # Set the premium for the sell order
            #print('# Set the premium for the sell order')
            premium = 0.003 + fee

            amount = round(1 / midpoint, 3)

            # Get balance for selling
            balance = exchange.fetch_balance()
            btc_balance = balance['BTC']['free']
            usdt_balance = balance['USDT']['free']
            print(btc_balance)
            print(usdt_balance)
            
            # Market Data Print
            current_time = datetime.now()
            print(current_time.strftime("%B %d, %Y %I:%M %p"))
            # Market Data Print

            # Ask ChatGPT if it's going up or down
            def gpt_up_down(data):
                openai.api_key = "sk-"
                preprompt = "Predict: UP or DOWN (no other information)."
                print(preprompt)
                cleaned = str(data)
                datacleaned = cleaned.replace('[', '').replace(']', '')
                #cleaned = "test"
                print(datacleaned)
                completions = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    max_tokens=4000,
                    n=1,
                    stop=None,
                    temperature=0.5,
                    messages=[
                        {"role": "system", "content": preprompt},
                        {"role": "user", "content": datacleaned}
                    ]
                )
                content = completions["choices"][0]["message"]["content"].strip().replace("\n", "").replace(".", "").lower()
                print(content)
                return content

            # Check if there are any open orders
            print('# Check if there are any open orders')
            open_orders = exchange.fetch_open_orders(symbol)
            if not open_orders:
                print('# Place a limit buy order at the midpoint price')
                try:
                    # Check if it is bullish up or bearish down before buying
                    if gpt_up_down(data) == 'up':
                        # Place a limit buy order at the midpoint price
                        order_id = exchange.create_order(symbol, 'limit', 'buy', amount, ask)
                except:
                    # We must own bitcoin and we want to sell it if the script
                    # tries to buy more bitcoin and has insufficent funds
                    if not open_orders:
                        # Check if it is bullish up or bearish down before buying
                        if gpt_up_down(data) == 'down':
                            # Place a limit sell order at the midpoint price plus the premium which includes the fee
                            #order_id = exchange.create_order(symbol, 'limit', 'sell', btc_balance, midpoint * (1 + fee))
                            order_id = exchange.create_order(symbol, 'limit', 'sell', amount, bid)

            # Pause for a few seconds and check the status of the open orders
            print('# Pause for a few seconds and check the status of the open orders')
            sleep(5)
            try:
                open_orders = exchange.fetch_open_orders(symbol)
            except:
                sleep(60)
                open_orders = exchange.fetch_open_orders(symbol)

            # Check if there are any open orders
            print('# Check if there are any open orders')
            if not open_orders:
                # Place a limit sell order at the midpoint price plus the premium
                try:
                    if gpt_up_down(data) == 'down':
                        #order_id = exchange.create_order(symbol, 'limit', 'sell', btc_balance, midpoint * (1 + fee))
                        order_id = exchange.create_order(symbol, 'limit', 'sell', amount, bid)
                except:
                    # Place a limit buy order at the midpoint price
                    # If for some reason the script doesnt have anything to sell
                    # It'll just buy it
                    if gpt_up_down(data) == 'up':
                        order_id = exchange.create_order(symbol, 'limit', 'buy', amount, ask)


            # Pause for a few seconds and check the status of the open orders XYZ
            print('# Pause for a few seconds and check the status of the open orders')
            sleep(60 * 60)
            try:
                open_orders = exchange.fetch_open_orders(symbol)
            except:
                sleep(5)
                open_orders = exchange.fetch_open_orders(symbol)
    except:
        # The logic for this sleeping is if the script fails for some rate limit error 
        # or other issue it'll wait one minute before restarting the script again.
        sleep(60)
        continue
