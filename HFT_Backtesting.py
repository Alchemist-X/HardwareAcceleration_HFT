import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def moving_average_crossover_strategy(data, short_window, long_window, latency=0):
    signals = pd.DataFrame(index=data.index)
    signals['price'] = data['price']
    
    signals['short_mavg'] = data['price'].rolling(window=short_window, min_periods=1, center=False).mean()
    signals['long_mavg'] = data['price'].rolling(window=long_window, min_periods=1, center=False).mean()

    signals['signal'] = 0.0
    signals['signal'][short_window:] = np.where(signals['short_mavg'][short_window:] > signals['long_mavg'][short_window:], 1.0, 0.0)   

    signals['positions'] = signals['signal'].diff()
    
    signals['trade_price'] = signals['price'].shift(latency)
    
    return signals

def mean_reversion_strategy(data, window, latency=0):
    signals = pd.DataFrame(index=data.index)
    signals['price'] = data['price']

    # Compute the Bollinger Bands
    signals['rolling_mean'] = signals['price'].rolling(window=window).mean()
    signals['rolling_std'] = signals['price'].rolling(window=window).std()
    signals['upper_band'] = signals['rolling_mean'] + (signals['rolling_std'] * 2)
    signals['lower_band'] = signals['rolling_mean'] - (signals['rolling_std'] * 2)

    # Create buy and sell signals
    signals['signal'] = 0
    buy_signals = signals['price'][window:] < signals['lower_band'][window:]
    sell_signals = signals['price'][window:] > signals['upper_band'][window:]
    signals.loc[buy_signals[window:].index, 'signal'] = buy_signals[window:]
    signals.loc[sell_signals[window:].index, 'signal'] = -sell_signals[window:]

    signals['trade_price'] = signals['price'].shift(latency)

    return signals

def backtest(signals, initial_capital):
    positions = pd.DataFrame(index=signals.index).fillna(0.0)
    
    signals['positions'] = signals['signal']
    
    positions['trade'] = signals['positions'] * signals['trade_price']

    portfolio = positions.multiply(signals['trade_price'], axis=0)

    pos_diff = positions.diff()

    portfolio['holdings'] = (positions.multiply(signals['trade_price'], axis=0)).sum(axis=1)
    portfolio['cash'] = initial_capital - (pos_diff.multiply(signals['trade_price'], axis=0)).sum(axis=1).cumsum()

    portfolio['total'] = portfolio['cash'] + portfolio['holdings']
    portfolio['returns'] = portfolio['total'].pct_change()
    
    return portfolio


def plot_results(data, positions_10, positions_1000):
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 16))
    
    # P&L plot
    ax1.plot(positions_10['holdings'], label='10ms Latency (Mean Reversion)')
    ax1.plot(positions_1000['holdings'], label='1000ms Latency (Moving Average Crossover)')
    ax1.set_xlabel('Time')
    ax1.set_ylabel('P&L')
    ax1.set_title('P&L vs Time')
    ax1.legend(loc='best')
    
    # Profit plot
    ax2.plot(positions_10['trade'].cumsum(), label='10ms Latency')
    ax2.plot(positions_1000['trade'].cumsum(), label='1000ms Latency')
    ax2.set_xlabel('Time')
    ax2.set_ylabel('Cumulative Profit')
    ax2.set_title('Cumulative Profit vs Time')
    ax2.legend(loc='best')


    # Maximum drawdown plot
    max_dd_10 = np.maximum.accumulate(positions_10['holdings']) - positions_10['holdings']
    max_dd_1000 = np.maximum.accumulate(positions_1000['holdings']) - positions_1000['holdings']

    ax3.plot(max_dd_10, label='10ms Latency')
    ax3.plot(max_dd_1000, label='1000ms Latency')
    ax3.set_xlabel('Time')
    ax3.set_ylabel('Maximum Drawdown')
    ax3.set_title('Maximum Drawdown vs Time')
    ax3.legend(loc='best')

    plt.show()
data = pd.read_csv("BNBBUSD-trades-2023-04-05.csv", names=["trade_id", "price", "qty", "quoteQty", "time", "isBuyerMaker", "isBestMatch"])

short_window = 40
long_window = 100

# signals_10 = mean_reversion_strategy(data, window=short_window, latency=10)
signals_10 = moving_average_crossover_strategy(data, short_window, long_window, latency=10)
signals_1000 = moving_average_crossover_strategy(data, short_window, long_window, latency=10000)
# signals_1000 = mean_reversion_strategy(data, window=short_window, latency=1000)

initial_capital = 100 # Define your initial capital here
positions_10 = backtest(signals_10, initial_capital)
positions_1000 = backtest(signals_1000, initial_capital)

plot_results(data, positions_10, positions_1000)

