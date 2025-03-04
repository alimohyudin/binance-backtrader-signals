import backtrader as bt
import datetime
import schedule
import time
import asyncio
import websockets
import json
from strategy.MACDStrategy import MACDStrategy
from fetch_data import fetch_1month_data

count = 1
last_signal = None
signals = []
clients = set()

async def broadcast_signal(signal):
    if clients:  # asyncio.gather doesn't accept an empty list
        message = json.dumps(signal, default=str)
        if signal['datetime'].date() < datetime.datetime.utcnow().date():
            print("Skipping signal broadcast as it is not from today")
            return
        
        temp_signal = {**signal, 'datetime': signal['datetime'].strftime('%Y-%m-%d %H:%M:%S')}
        message = json.dumps(temp_signal, default=str)
        await asyncio.gather(*[client.send(message) for client in clients])

async def handler(websocket):
    clients.add(websocket)
    try:
        async for message in websocket:
            if message == "get_signals":
                signals_serializable = [
                    {**signal, 'datetime': signal['datetime'].strftime('%Y-%m-%d %H:%M:%S')}
                    for signal in signals
                ]
                await websocket.send(json.dumps(signals_serializable))
            if message == "get_last_signal":
                if signals:
                    my_last_signal = signals[-1]
                    signals_serializable = {**my_last_signal, 'datetime': my_last_signal['datetime'].strftime('%Y-%m-%d %H:%M:%S')}
                    await websocket.send(json.dumps(signals_serializable))
    finally:
        clients.remove(websocket)

async def start_server():
    server = await websockets.serve(handler, "0.0.0.0", 8765)
    print("WebSocket server started on ws://0.0.0.0:8765")
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
    fetch_1month_data(symbol, interval)

    end_date = datetime.datetime.utcnow()
    start_date = end_date - datetime.timedelta(days=15)

    cerebro = bt.Cerebro()
    data = bt.feeds.GenericCSVData(
        dataname=f'./data/{symbol}_{interval}.csv',  # Added interval to the data file path
        dtformat='%m-%d-%YT%H:%M:%S.000Z',  # New format to match '2024-12-01T00:00:00.000Z'
        timeframe=bt.TimeFrame.Minutes,
        fromdate=start_date,
        todate=end_date,
        compression=3,
        openinterest=-1,
    )
    print(len(data))
    cerebro.adddata(data)

    # Add strategy
    cerebro.addstrategy(MACDStrategy, lookback_bars=55, rsi_period=15, callback=_handle_signals_callback)

    # Run
    cerebro.broker.setcash(1000)
    cerebro.broker.setcommission(commission=0.0)
    print(f'Starting Portfolio Value: {cerebro.broker.getvalue()}')
    cerebro.run()
    print(f'Final Portfolio Value: {cerebro.broker.getvalue()}')






async def main():
    schedule.every(30).seconds.do(run_strategy)

    # Run scheduled tasks in a separate thread
    def run_schedule():
        while True:
            schedule.run_pending()
            time.sleep(1)

    import threading
    schedule_thread = threading.Thread(target=run_schedule, daemon=True)
    schedule_thread.start()

    await start_server()

if __name__ == '__main__':
    asyncio.run(main())
