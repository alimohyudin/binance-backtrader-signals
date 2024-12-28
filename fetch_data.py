import os
import csv
from datetime import datetime, timedelta
from binance.client import Client

# Replace with your Binance API key and secret
API_KEY = 'your_api_key'
API_SECRET = 'your_api_secret'

client = Client(API_KEY, API_SECRET)

def clear_directory(output_folder, symbol):
    try:
        # Read the contents of the directory
        files = os.listdir(os.path.join(output_folder, symbol))

        # Iterate through each file and delete it
        for file in files:
            file_path = os.path.join(output_folder, symbol, file)

            # Check if it's a file and delete it
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Deleted file: {file_path}")

        print('Directory cleared successfully.')
    except Exception as err:
        print('Error clearing directory:', err)

def fetch_kline_data(symbol, start_date, end_date, interval=Client.KLINE_INTERVAL_3MINUTE):
    klines = client.get_historical_klines(symbol, interval, start_date, end_date)
    return klines

def format_kline_data(kline):
    timestamp = datetime.utcfromtimestamp(kline[0] / 1000).strftime('%m-%d-%YT%H:%M:%S.000Z')
    open_price = kline[1]
    high_price = kline[2]
    low_price = kline[3]
    close_price = kline[4]
    volume = kline[5]
    return [timestamp, open_price, high_price, low_price, close_price, volume]

def fetch_and_append_kline_data(symbol, start_date, end_date, interval=Client.KLINE_INTERVAL_3MINUTE, output_folder='./data'):
    output_file = os.path.join(output_folder, f'{symbol}_{interval}.csv')
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    existing_data = []
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            reader = csv.reader(f)
            existing_data = list(reader)

    if existing_data:
        last_fetched_date = datetime.strptime(existing_data[-1][0], '%m-%d-%YT%H:%M:%S.000Z')
    else:
        last_fetched_date = datetime.strptime(start_date, '%Y-%m-%d')

    new_data = []

    # Fetch data from the last fetched date to the end date
    current_date = last_fetched_date + timedelta(minutes=3)
    print(f"Fetching data from {current_date.strftime('%Y-%m-%d %H:%M:%S')} to {end_date}")
    while current_date <= datetime.strptime(end_date, '%Y-%m-%d'):
        klines = fetch_kline_data(symbol, current_date.strftime('%Y-%m-%d %H:%M:%S'), end_date, interval)
        formatted_klines = [format_kline_data(kline) for kline in klines]
        new_data.extend(formatted_klines)

        print(f"Fetched data from {current_date.strftime('%Y-%m-%d %H:%M:%S')} to {end_date}")
        if not formatted_klines:
            break
        current_date = datetime.strptime(formatted_klines[-1][0], '%m-%d-%YT%H:%M:%S.000Z') + timedelta(minutes=3)

    # Write the combined data to the CSV file
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(existing_data + new_data)

def myfetch(symbol, start_date, end_date):
    fetch_and_append_kline_data(symbol, start_date, end_date)

def fetch_1year_data(symbol, interval=Client.KLINE_INTERVAL_3MINUTE, output_folder='./data'):
    start_date = '2024-01-01'
    end_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    fetch_and_append_kline_data(symbol, start_date, end_date, interval, output_folder)
# Example usage
if __name__ == '__main__':
    # output_folder = './data'
    # symbol = 'BTCUSDT'
    # start_date = '2024-12-31'
    # end_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

    # # clear_directory(output_folder, symbol)
    # myfetch(symbol, start_date, end_date)
    fetch_1year_data('BTCUSDT')