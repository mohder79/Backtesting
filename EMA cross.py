from datetime import datetime
import oandapyV20.endpoints.instruments as instruments
import oandapyV20
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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


EUR_USD = fetch('EUR_USD', 'M5', 2000)


EUR_USD = EUR_USD[['Open', 'High', 'Low',
                   'Close', 'Volume']].astype(np.float64)


# { function for calculate EMA
def EMA(src: str, Length: int, smoothing=2):
    EMA = np.zeros(np.size(src))
    emasize = np.size(src)
    EMA[:Length-1] = np.NaN
    EMA[Length-1] = np.mean(src[:Length])
    for i in range(Length, emasize):
        EMA[i] = (((smoothing/(Length + 1)) * src[i]) +
                  ((1-(smoothing/(Length + 1))) * EMA[i-1]))
    return EMA
# }


print(EUR_USD)


class EMACross(Strategy):
    Fast_Ema_Len = 10
    Slow_Ema_Len = 40

    def init(self):
        self.EMA1 = self.I(EMA, pd.Series(self.data.Close), self.Fast_Ema_Len)
        self.EMA2 = self.I(EMA, pd.Series(self.data.Close), self.Slow_Ema_Len)

    def next(self):

        # {long}

        # if self.EMA1[-1] > self.EMA2[-1] and self.EMA1[-2] < self.EMA2[-1]:
        #     self.buy()

        if crossover(self.EMA1, self.EMA2):
            self.buy()

        # }

        # {short

        # if self.EMA1[-1] < self.EMA2[-1] and self.EMA1[-2] > self.EMA2[-1]:
        #     self.sell()

        if crossover(self.EMA2, self.EMA1):
            self.sell()

        # }

# {run the backtest


bt = Backtest(EUR_USD, EMACross, cash=30_000,
              exclusive_orders=True, commission=0.0002)

stats = bt.run()


print(stats)
bt.plot(plot_drawdown=True, show_legend=True)


# }
