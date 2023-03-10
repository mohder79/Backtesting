from datetime import datetime
import oandapyV20.endpoints.instruments as instruments
import oandapyV20
import pandas as pd

from backtesting import Backtest
from backtesting import Strategy
from backtesting.lib import crossover
import numpy as np
# pd.set_option('display.max_rows', None)  # fix *** to show all rows


access_token = ''
client = oandapyV20.API(access_token=access_token)


def fetch(symbol:  str, timeframe: str, count: int):
    print(
        f"Fetching {symbol} new bars for {datetime.now().isoformat(sep='_')}")
    params = {
        "count": count,
        "granularity": timeframe}
    r_data = instruments.InstrumentsCandles(instrument=symbol,
                                            params=params)
    client.request(r_data)

    data = []
    for i in r_data.response['candles']:
        data.append([i['time'], i['mid']['o'],
                    i['mid']['h'], i['mid']['l'], i['mid']['c'], i['volume']])
    df = pd.DataFrame(data)
    df.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
    df['Time'] = pd.to_datetime(df['Time'])

    df['Time'] = pd.to_datetime(
        df['Time']).dt.tz_convert('iran')

    df['Date'] = df['Time']

    df['Date'] = pd.to_datetime(df['Time'], unit='ms')
    # df.set_index('Date', inplace=True)

    return df


EUR_USD = fetch('EUR_USD', 'M5', 500)


EUR_USD['Close'] = EUR_USD['Close'].astype(np.float64)
EUR_USD['Open'] = EUR_USD['Open'].astype(np.float64)
EUR_USD['Low'] = EUR_USD['Low'].astype(np.float64)
EUR_USD['Volume'] = EUR_USD['Volume'].astype(np.float64)
EUR_USD['High'] = EUR_USD['High'].astype(np.float64)


def random_num():
    num = np.random.random(len(EUR_USD))
    signal = np.zeros(len(EUR_USD))
    for i in range(len(EUR_USD)):
        if num[i] < 0.7:
            signal[i] = 0
        elif num[i] < 0.9:
            signal[i] = 1
        else:
            signal[i] = -1
    return signal


EUR_USD['signal'] = random_num()


class SignalStrategy(Strategy):

    def init(self):
        pass

    def next(self):
        current_signal = self.data.signal[-1]
        if current_signal == 1:
            if not self.position:
                self.buy()
        elif current_signal == -1:
            if self.position.is_long:
                self.position.close()

        if current_signal == -1:
            if not self.position:
                self.sell()
        elif current_signal == 1:
            if self.position.is_short:
                self.position.close()


bt = Backtest(EUR_USD, SignalStrategy, cash=10_000)

stats = bt.run()


print(stats)
bt.plot(plot_drawdown=True, show_legend=True)


print((EUR_USD))
