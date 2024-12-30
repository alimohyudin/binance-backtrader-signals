import backtrader as bt
from datetime import datetime, date, timedelta
from fetch_data import fetch_1year_data
from strategy.MACDStrategy import MACDStrategy
import concurrent.futures
import itertools


def get_last_date_of_month(year, month):
    # Get the first day of the next month
    if month == 12:  # Handle December separately
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    # Subtract one day from the first day of the next month
    last_date = next_month - timedelta(days=1)
    return last_date


def run_strategy(params):
    cerebro = bt.Cerebro()
    strategy_params = {k: v for k, v in params.items() if k not in ['start_month', 'end_month']}
    cerebro.addstrategy(MACDStrategy, **strategy_params)

    data = bt.feeds.GenericCSVData(
        dataname='./backtrader/data/BTCUSDT_3m.csv',
        # dataname='./backtrader/data/BTCUSDT.csv',
        dtformat='%m-%d-%YT%H:%M:%S.000Z',  # New format to match '2024-12-01T00:00:00.000Z'
        timeframe=bt.TimeFrame.Minutes,
        
        fromdate=datetime(2024, params['start_month'], 1),
        todate=datetime(2024, params['end_month'], get_last_date_of_month(2024, params['end_month']).day),
        
        compression=1,
        openinterest=-1,
    )
    cerebro.adddata(data)

    cerebro.broker.setcash(1000)
    cerebro.broker.setcommission(commission=0.0)

    starting_cash = cerebro.broker.getvalue()
    cerebro.run()
    ending_cash = cerebro.broker.getvalue()

    profit = ending_cash - starting_cash
    return profit, params

def generate_params_grid():
    month_pairs = [(10, 12)]
    long_stoploss = [5]
    long_takeprofit = [3]
    short_stoploss = [2]
    short_takeprofit = [3]
    lookback_bars = [55]
    param_grid = list(itertools.product(month_pairs, long_stoploss, long_takeprofit, short_stoploss, short_takeprofit, lookback_bars))
    return [{'start_month': p[0][0], 'end_month': p[0][1], 'long_stoploss': p[1], 'long_takeprofit': p[2], 'short_stoploss': p[3], 'short_takeprofit': p[4], 'lookback_bars': p[5]} for p in param_grid]

def test_macd_strategy():
    test_params = generate_params_grid()

    best_profit = float('-inf')
    best_params = None

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(run_strategy, params) for params in test_params]
        for future in concurrent.futures.as_completed(futures):
            profit, params = future.result()
            print(f"Params: {params}, Profit: {profit}")
            if profit > best_profit:
                best_profit = profit
                best_params = params

    print(f"Best Params: {best_params}, Best Profit: {best_profit}")

if __name__ == '__main__':
    fetch_1year_data("BTCUSDT", interval='3m', output_folder='./backtrader/data')
    test_macd_strategy()