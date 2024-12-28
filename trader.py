import backtrader as bt
import datetime
import schedule
import time
import asyncio
import websockets
import json
from strategy.MACDStrategy import MACDStrategy
from fetch_data import fetch_1year_data

count = 1
last_signal = None
signals = []
clients = set()

async def broadcast_signal(signal):
    if clients:  # asyncio.wait doesn't accept an empty list
        message = f"New signal: {signal['signal']}, Price: {signal['price']}, Datetime: {signal['datetime']}"
        await asyncio.wait([client.send(message) for client in clients])

async def handler(websocket):
    clients.add(websocket)
    try:
        async for message in websocket:
            if message == "get_signals":
                signals_serializable = [
                    {**signal, 'datetime': signal['datetime'].strftime('%Y-%m-%dT%H:%M:%S')}
                    for signal in signals
                ]
                await websocket.send(json.dumps(signals_serializable))
    finally:
        clients.remove(websocket)

async def start_server():
    server = await websockets.serve(handler, "localhost", 8765)
    print("WebSocket server started on ws://localhost:8765")
    await server.wait_closed()
    
def _handle_signals_callback(data):
    global count, last_signal, signals
    
    if data not in signals:
        print(f"{count}- Signal: {data['signal']}, Price: {data['price']}, Datetime: {data['datetime']}")
        signals.append(data)
        last_signal = data
        count += 1
        if count > 1:  # Ensure this is not the first run
            print("New signal received!")
            asyncio.run(broadcast_signal(data))

def run_strategy():
    symbol = 'BTCUSDT'
    interval = '3m'
    # Fetch 1 year of data
    fetch_1year_data(symbol, interval)

    cerebro = bt.Cerebro()
    data = bt.feeds.GenericCSVData(
        dataname=f'./data/{symbol}_{interval}.csv',  # Added interval to the data file path
        dtformat='%m-%d-%YT%H:%M:%S.000Z',  # New format to match '2024-12-01T00:00:00.000Z'
        timeframe=bt.TimeFrame.Minutes,
        fromdate=datetime.datetime(2024, 12, 16),
        todate=datetime.datetime(2024, 12, 31),
        compression=3,
        openinterest=-1,
    )
    print(len(data))
    cerebro.adddata(data)

    # Add strategy
    cerebro.addstrategy(MACDStrategy, lookback_bars=55, callback=_handle_signals_callback)

    # Run
    cerebro.broker.setcash(1000)
    cerebro.broker.setcommission(commission=0.0)
    print(f'Starting Portfolio Value: {cerebro.broker.getvalue()}')
    cerebro.run()
    print(f'Final Portfolio Value: {cerebro.broker.getvalue()}')






if __name__ == '__main__':
    run_strategy()

    def check_and_run_strategy():
        current_minute = datetime.datetime.now().minute
        if current_minute % 3 == 0:
            run_strategy()

    schedule.every().minute.do(check_and_run_strategy)

    asyncio.run(start_server())

    while True:
        schedule.run_pending()
        time.sleep(1)