import backtrader as bt

class Position:
    def __init__(self):
        self.size = 0
        self.price = 0
        self.time = None

class MACDStrategy(bt.Strategy):
    params = (
        ('enable_long_strategy', True),
        ('long_stoploss', 5),  # percent
        ('long_takeprofit', 3),
        ('enable_short_strategy', True),
        ('short_stoploss', 2),
        ('short_takeprofit', 3),
        ('rsi_period', 14),
        ('rsi_overbought', 70),
        ('rsi_oversold', 30),
        ('macd_fast', 12),
        ('macd_slow', 26),
        ('macd_signal', 9),
        ('ema_periods', [9, 21, 50, 100, 200]),
        ('start_date', None),
        ('end_date', None),
        ('lookback_bars', 55),
        ('callback', None),
    )

    def __init__(self):
        self.a_log_trade = -1
        self.a_total_closed_positions = 0
        self.a_calculated_profit = 0
        self.a_max_trades = 9999
        self.a_position_closed = True
        self.a_last_position = Position()
        self.a_signal = ""
        self.a_SL_or_TP_hit = False

        # Indicators
        self.rsi = bt.indicators.RSI_Safe(self.data.close, period=self.params.rsi_period)
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.params.macd_fast,
            period_me2=self.params.macd_slow,
            period_signal=self.params.macd_signal,
        )

        self.ema_lines = [bt.indicators.EMA(self.data.close, period=period) for period in self.params.ema_periods]

        # Custom counters for `barssince`
        self.bars_since_oversold = None
        self.bars_since_overbought = None

    def next(self):
        if self.rsi[0] <= self.params.rsi_oversold:
            self.bars_since_oversold = 0  # Reset counter
        elif self.bars_since_oversold is not None:
            self.bars_since_oversold += 1

        if self.rsi[0] >= self.params.rsi_overbought:
            self.bars_since_overbought = 0  # Reset counter
        elif self.bars_since_overbought is not None:
            self.bars_since_overbought += 1

        # Generate signals
        was_oversold = self.bars_since_oversold is not None and self.bars_since_oversold <= self.params.lookback_bars
        was_overbought = self.bars_since_overbought is not None and self.bars_since_overbought <= self.params.lookback_bars
        crossover_bull = self.macd.macd[0] > self.macd.signal[0]
        crossover_bear = self.macd.macd[0] < self.macd.signal[0]

        self.buy_signal = was_oversold and crossover_bull
        self.sell_signal = was_overbought and crossover_bear

        # Long Strategy
        if self.buy_signal and self.params.enable_long_strategy:
            if self.a_log_trade - 1 == self.a_total_closed_positions:
                print("buy signal")
            
            if self.a_signal == "sell" or self.a_signal == "":
                self.a_signal = "buy"
                self.a_SL_or_TP_hit = False

                if self.params.callback:
                    self.params.callback({
                        'signal': 'buy',
                        'price': self.data.close[0],
                        'datetime': self.datas[0].datetime.datetime(0)
                    })

        # Short Strategy
        if self.sell_signal and self.params.enable_short_strategy:
            if self.a_log_trade - 1 == self.a_total_closed_positions:
                print("sell signal")
            
            if self.a_signal == "buy" or self.a_signal == "":
                self.a_signal = "sell"
                self.a_SL_or_TP_hit = False
                
                if self.params.callback:
                    self.params.callback({
                        'signal': 'sell',
                        'price': self.data.close[0],
                        'datetime': self.datas[0].datetime.datetime(0)
                    })

        if not self.a_position_closed:
            self.set_stop_loss_take_profit()

    def set_stop_loss_take_profit(self):
        stop_loss = None
        take_profit = None

        position_type = 'long' if self.a_last_position.size > 0 else 'short'

        if position_type == 'long':
            stop_loss = self.a_last_position.price * (1 - self.params.long_stoploss / 100)
            take_profit = self.a_last_position.price * (1 + self.params.long_takeprofit / 100)
        elif position_type == 'short':
            stop_loss = self.a_last_position.price * (1 + self.params.short_stoploss / 100)
            take_profit = self.a_last_position.price * (1 - self.params.short_takeprofit / 100)

        if position_type == 'long' and self.data.close[0] < stop_loss:
            if self.params.callback:
                self.a_signal = ""
                self.params.callback({
                    'signal': 'stop_loss',
                    'price': self.data.close[0],
                    'datetime': self.datas[0].datetime.datetime(0)
                })
        if position_type == 'short' and self.data.close[0] > stop_loss:
            if self.params.callback:
                self.a_signal = ""
                self.params.callback({
                    'signal': 'stop_loss',
                    'price': self.data.close[0],
                    'datetime': self.datas[0].datetime.datetime(0)
                })
        if position_type == 'long' and self.data.close[0] > take_profit:
            if self.params.callback:
                self.a_signal = ""
                self.params.callback({
                    'signal': 'take_profit',
                    'price': self.data.close[0],
                    'datetime': self.datas[0].datetime.datetime(0)
                })
        if position_type == 'short' and self.data.close[0] < take_profit:
            if self.params.callback:
                self.a_signal = ""
                self.params.callback({
                    'signal': 'take_profit',
                    'price': self.data.close[0],
                    'datetime': self.datas[0].datetime.datetime(0)
                })
