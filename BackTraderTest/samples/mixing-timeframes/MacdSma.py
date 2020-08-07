'''
strategy:
    buy precondition:
        1.macd gold cross
        2.price beyond short SMA
        3.short SMA trun up
        4.not strict short sequence
    after buy stop price:
        1.in three days:
            min of ATR stop price and buy price
        2.out three days:
            ATR stop price
    sell condition:
        1.stop price
'''
import argparse

import pandas as pd

import backtrader as bt




# pd全局设置
from BackTraderTest.BackTraderFunc.DataReadFromCsv import read_dataframe

pd.set_option('display.max_rows', 5000)
pd.set_option('display.max_columns', 100)
pd.set_option('display.width', 300)





class BuyTrailer(bt.Indicator):
    lines = ('buyPoints', )
    plotinfo = dict(subplot=True, plotlinelabels=True)

    params = dict(
        smaShortPeriod=13,
        smaMidPeriod=26,
        smaLongPeriod=52,
        turnUpRate=0,
    )

    def __init__(self):
        self.strat = self._owner  # alias for clarity

        self.shortSma = bt.ind.SMA(self.data, period=self.p.smaShortPeriod)
        self.midSma = bt.ind.SMA(self.data, period=self.p.smaMidPeriod)
        self.longSma = bt.ind.SMA(self.data, period=self.p.smaLongPeriod)

        self.macd = bt.ind.MACD(self.data)
        # goldCross = bt.ind.CrossUp(macd.macd, macd.signal)

    def next(self):
        self.l.buyPoints[0] = 0

        if self.shortSma[0] < self.midSma[0] < self.longSma[0]:
            return

        if self.data[0] < self.shortSma[0]:
            return

        if (self.shortSma[0] - self.shortSma[-1]) / self.shortSma[-1] < self.p.turnUpRate:
            return

        if self.macd.macd[0] < self.macd.signal:
            return

        self.l.buyPoints[0] = 1


class StopTrailer(bt.Indicator):
    _nextforce = True  # force system into step by step calcs

    lines = ('stopPrice',)
    plotinfo = dict(subplot=False, plotlinelabels=True)

    params = dict(
        atrperiod=14,
        emaperiod=10,
        stopfactor=3.0,
    )

    def __init__(self):
        self.strat = self._owner  # alias for clarity

        # Volatility which determines stop distance
        atr = bt.ind.ATR(self.data, period=self.p.atrperiod)
        emaatr = bt.ind.EMA(atr, period=self.p.emaperiod)
        self.stop_dist = emaatr * self.p.stopfactor
        self.s_s = self.data - self.stop_dist

    def next(self):
        if self.strat.position.size > 0:
            self.l.stopPrice[0] = max(self.s_s[0], self.l.stopPrice[-1])


class St(bt.Strategy):
    params = dict(
        atrperiod=14,  # measure volatility over x days
        emaperiod=10,  # smooth out period for atr volatility
        stopfactor=3.0,  # actual stop distance for smoothed atr
        verbose=True,  # print out debug info
        samebar=True,  # close and re-open on samebar
    )

    def __init__(self):

        self.buyPoints = BuyTrailer()
        self.stopPrice = StopTrailer()

        self.exit_long = bt.ind.CrossDown(self.data,
                                          self.stopPrice, plotname='Exit Long')


        self.order = None
        self.entering = None
        self.stop_large = True

    def start(self):
        self.entering = 0
        self.start_val = self.broker.get_value()

    def next(self):
        txt = ','.join(
            ['%04d' % len(self),
             '%04d' % len(self.data0),
             # '%04d' % len(self.data1),
             self.data.datetime.date(0).isoformat(),
             '%.2f' % self.data0.close[0],
             # '%.2f' % self.pp.s1[0],
             # '%.2f' % self.sellsignal[0]
             ])

        # print(txt)
        # print("Cross over :%f" % self.crossOver[0])

        if self.order is not None:
            return

        # self.entering = 0
        closing = None
        if self.position.size > 0 :  # In the market - Long
            self.log('Long Stop Price: {:.2f}, current price: {:.2f}', self.stopPrice[0], self.data[0])
            if self.exit_long > 0:
                self.log('收到卖出信号')
                # self.stats.trades
                bt.order.OrderData
                self.order = self.close()
        elif self.buyPoints[0] > 0:
            self.order = self.order_target_percent(target=0.99)
            if self.order:
                self.entering = 1
                self.stop_large = True

    def notify_trade(self, trade):
        if trade.size > 0:
            self.log('Long  Entry at: {:.2f}', trade.price)
        elif trade.size < 0:
            self.log('Short Entry at: {:.2f}', trade.price)
        else:  # not trade.size - trade is over
            self.log('Trade PNL: {:.2f}', trade.pnlcomm)

    def notify_order(self, order):
        if order.status in [bt.Order.Submitted, bt.Order.Accepted]:
            return  # Await further notifications

        if order.status == order.Completed:
            if order.isbuy():
                buytxt = 'BUY COMPLETE, %.2f' % order.executed.price

                self.log(buytxt, order.executed.dt)
            else:
                selltxt = 'SELL COMPLETE, %.2f' % order.executed.price
                self.log(selltxt, order.executed.dt)

        elif order.status in [order.Expired, order.Canceled, order.Margin]:
            self.log('%s ,' % order.Status[order.status])
            pass  # Simply log

        self.order = None

    def logdata(self):
        if self.p.verbose:  # logging
            txt = []
            txt += ['{:.2f}'.format(self.position.size)]
            txt += ['{:.2f}'.format(self.data.open[0])]
            txt += ['{:.2f}'.format(self.data.high[0])]
            txt += ['{:.2f}'.format(self.data.low[0])]
            txt += ['{:.2f}'.format(self.data.close[0])]
            self.log(','.join(txt))

    def log(self, txt, *args):
        if self.p.verbose:
            out = [self.datetime.date().isoformat(), txt.format(*args)]
            print(','.join(out))

    def stop(self):
        self.stop_val = self.broker.get_value()
        self.pnl_val = self.stop_val - self.start_val
        self.log('Start Value: {:.2f}', self.start_val)
        self.log('Final Value: {:.2f}', self.stop_val)
        self.log('PNL   Value: {:.2f}', self.pnl_val)



def runstrat():
    args = parse_args()

    cerebro = bt.Cerebro()

    # Data feed kwargs
    # '15min', '30min', '60min',
    dataframe = read_dataframe(args.data, args.years, ['d'])

    for i in range(len(dataframe)):
        cerebro.adddata(bt.feeds.PandasData(dataname=dataframe[i]))

    cerebro.addstrategy(St)

    cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')

    strat = cerebro.run(stdstats=True, runonce=False)

    pyfoliozer = strat[0].analyzers.getbyname('pyfolio')
    returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()

    transactions.to_csv("transtion.csv")
    if args.plot:
        cerebro.plot(style='line')
        cerebro.plot(style='candle')


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Sample for pivot point and cross plotting')

    parser.add_argument('--data', required=False,
                        default='000651.csv',
                        help='Data to be read in')

    parser.add_argument('--years', default='2015-2020',
                        help='Formats: YYYY-ZZZZ / YYYY / YYYY- / -ZZZZ')

    parser.add_argument('--multi', required=False, action='store_true',
                        help='Couple all lines of the indicator')

    parser.add_argument('--plot', required=False, action='store_true',
                        default=True,
                        help=('Plot the result'))

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()