from datetime import datetime
import oandapyV20.endpoints.instruments as instruments
import oandapyV20
import pandas as pd
import plotly.graph_objects as go
from backtesting import Backtest
from backtesting import Strategy
import numpy as np
from backtesting.lib import crossover

# pd.set_option('display.max_rows', None)  # fix *** to show all rows


access_token = '4f1c0806046d57e80f1143d71160cfbd-7eff0f2ccf97ace67f436c29588754ad'
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
    df.set_index('Date', inplace=True)

    return df


EUR_USD = fetch('ETH_USD', 'M15', 5000)


EUR_USD = EUR_USD[['Open', 'High', 'Low',
                   'Close', 'Volume']].astype(np.float64)


# { function for calculate sma

def SMA(src: str, length: int):
    return src.rolling(window=length).mean()
# }


print(EUR_USD)


class SMACross(Strategy):
    Fast_SMA_Len = 10
    Slow_SMA_Len = 40

    def init(self):
        self.SMA1 = self.I(SMA, pd.Series(self.data.Close), self.Fast_SMA_Len)
        self.SMA2 = self.I(SMA, pd.Series(self.data.Close), self.Slow_SMA_Len)

    def next(self):

        # {long}

        if crossover(self.SMA1, self.SMA2):
            self.buy()
        # }

        # {short

        if crossover(self.SMA2, self.SMA1):
            self.sell()

        # }

# {run the backtest


bt = Backtest(EUR_USD, SMACross, cash=30_000, exclusive_orders=True, commission=0.001
              )  #

stats = bt.optimize(
    Fast_SMA_Len=range(10, 100, 10),
    Slow_SMA_Len=range(20, 200, 10),


    maximize='Equity Final [$]')

print(stats)

bt.plot(plot_drawdown=True, show_legend=True)


# }


# { pinescript


#     //@version=5
# strategy(title='SMA Cross strategy', overlay=true)


# useDateFilter = input.bool(true, title="Begin Backtest at Start Date",
#      group="Backtest Time Period")
# backtestStartDate = input.time(timestamp("1 Jan 2023"),
#      title="Start Date", group="Backtest Time Period",
#      tooltip="This start date is in the time zone of the exchange " +
#      "where the chart's instrument trades. It doesn't use the time " +
#      "zone of the chart or of your computer.")
# fast_len = input.int(20 , title="fast sma")
# slow_len = input.int(60 , title="slow sma")

# fast_sma = ta.sma(close, fast_len)
# slow_sma = ta.sma(close, slow_len)

# plot(fast_sma, color=color.new(color.red, 0), linewidth=3)
# plot(slow_sma, color=color.new(color.green, 0), linewidth=3)

# longcondition = ta.crossover(fast_sma, slow_sma)
# shortcondition = ta.crossunder(fast_sma, slow_sma)

# inTradeWindow = not useDateFilter or time >= backtestStartDate

# if inTradeWindow and longcondition
#     strategy.entry('long', strategy.long)

# if inTradeWindow and shortcondition
#     strategy.entry('short', strategy.short)


# }
