import ccxt
import pandas as pd
import numpy as np
import time

# Define the index constituents and their weights
index_weights = {
    'BNB/USDC': 0.135,
    'ETH/USDT': 0.4,
    'BTC/USDT': 0.2,
    'XRP/USDT': 0.265
}

timeframe = '1h'
window = 20
multiplier = 2

exchange = ccxt.binance({
    'rateLimit': 1200,
    'enableRateLimit': True,
})

index_df = None

for symbol, weight in index_weights.items():
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['symbol'] = symbol
    df['close_weighted'] = df['close'] * weight

    if index_df is None:
        index_df = df
    else:
        index_df = pd.merge(index_df, df, on='timestamp', how='outer', suffixes=('', f'_{symbol}'))


index_df['index_price'] = index_df.filter(like='close_weighted').sum(axis=1)

# Calculate the moving average (middle band)
index_df['moving_average'] = index_df['index_price'].rolling(window=window).mean()

# Calculate the standard deviation
index_df['std_dev'] = index_df['index_price'].rolling(window=window).std()

# Calculate the upper and lower Bollinger Bands
index_df['upper_band'] = index_df['moving_average'] + (multiplier * index_df['std_dev'])
index_df['lower_band'] = index_df['moving_average'] - (multiplier * index_df['std_dev'])

index_df = index_df.dropna()
index_df['signal'] = 0
index_df.loc[index_df['index_price'] > index_df['upper_band'], 'signal'] = -1  # Sell signal
index_df.loc[index_df['index_price'] < index_df['lower_band'], 'signal'] = 1   # Buy signal
position = 0
entry_price = 0
profit = 0

for index, row in index_df.iterrows():
    if row['signal'] == 1 and position == 0:  # Buy signal
        position = 1
        entry_price = row['index_price']
        print(f"Buy index at {entry_price}")

    elif row['signal'] == -1 and position == 1:  # Sell signal
        position = 0
        exit_price = row['index_price']
        profit += exit_price - entry_price
        print(f"Sell index at {exit_price}, profit: {profit}")

print(f"Total profit: {profit}")
