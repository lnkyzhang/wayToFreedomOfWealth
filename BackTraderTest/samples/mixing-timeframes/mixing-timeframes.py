#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2016 Daniel Rodriguez
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import datetime

import backtrader as bt
import backtrader.feeds as btfeeds
import backtrader.indicators as btind
import backtrader.utils.flushfile

import pandas as pd
from QUANTAXIS import QA_data_min_resample
from QUANTAXIS.QAData.data_resample import QA_data_min_to_day
from backtrader import indicator, LinePlotterIndicator
from backtrader.analyzers import TimeReturn, Transactions

from BackTraderTest.BackTraderFunc.DataReadFromCsv import read_dataframe
from BackTraderTest.BackTraderFunc.DataResample import data_min_resample
from BackTraderTest.BackTraderFunc.MacdDivergence import macd_extend_data
from BackTraderTest.BackTraderFunc.St_TripleScreen import TripleScreen_extend_data
from back_forecast.learn_quant.MACD.jukuan_macd_signal import *

import talib

# pd全局设置
pd.set_option('display.max_rows', 5000)
pd.set_option('display.max_columns', 100)
pd.set_option('display.width', 300)


class pandas_divergence(bt.feeds.PandasData):
    # Add a 'pe' line to the inherited ones from the base class
    lines = ('divergence_top', 'divergence_bottom',)

    # openinterest in GenericCSVData has index 7 ... add 1
    # add the parameter to the parameters inherited from the base class
    params = (('divergence_top', 15), ('divergence_bottom', 16),)


class pandas_tripleScreen(bt.feeds.PandasData):
    # Add a 'pe' line to the inherited ones from the base class
    lines = ('buyPoint',)

    # openinterest in GenericCSVData has index 7 ... add 1
    # add the parameter to the parameters inherited from the base class
    params = (('buyPoint', 15),)



class StopTrailer(bt.Indicator):
    _nextforce = True  # force system into step by step calcs

    lines = ('stop_long', 'stop_long_l', 'stop_long_s')
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

        # Running stop price calc, applied in next according to market pos
        # self.s_l = self.data - self.stop_dist
        # self.s_s = self.data + self.stop_dist

        self.s_l = self.data * 0.85
        self.s_s = self.data * 0.90

        self.lastLarge = True

    def next(self):
        # When entering the market, the stop has to be set
        if self.strat.entering > 0:  # entering long
            self.l.stop_long[0] = self.s_l[0]
            self.l.stop_long_l[0] = self.s_l[0]
            self.l.stop_long_s[0] = self.s_s[0]

        else:  # In the market, adjust stop only in the direction of the trade
            if self.strat.position.size > 0:
                self.l.stop_long_l[0] = max(self.s_l[0], self.l.stop_long_l[-1])
                self.l.stop_long_s[0] = max(self.s_s[0], self.l.stop_long_s[-1])

                if self.strat.stop_large:
                    self.l.stop_long[0] = self.l.stop_long_l[0]
                else:
                    self.l.stop_long[0] = self.l.stop_long_s[0]



class Divergence(bt.Indicator):
    lines = ('top_divergences', 'bottom_divergences')

    plotinfo = dict(plot=True, subplot=True, plotforce=True)

    def __init__(self):
        # self.strat = self._owner  # alias for clarity

        self.lines.top_divergences = -self.data.divergence_top
        self.lines.bottom_divergences = self.data.divergence_bottom



class St(bt.Strategy):
    params = dict(
        atrperiod=14,  # measure volatility over x days
        emaperiod=10,  # smooth out period for atr volatility
        stopfactor=3.0,  # actual stop distance for smoothed atr
        verbose=True,  # print out debug info
        samebar=True,  # close and re-open on samebar
    )

    def __init__(self):


        # 止损
        self.stoptrailer = st = StopTrailer(atrperiod=self.p.atrperiod,
                                            emaperiod=self.p.emaperiod,
                                            stopfactor=self.p.stopfactor)

        # Exit Criteria (Stop Trail) for long / short positions
        self.exit_long = bt.ind.CrossDown(self.data,
                                          st.stop_long, plotname='Exit Long')

        self.testIndicate = Divergence()

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

        self.entering = 0
        closing = None
        if self.position.size > 0:  # In the market - Long

            if self.testIndicate.bottom_divergences[0] > 0:
                self.log("buy signal")
                self.stop_large = True
            if self.testIndicate.top_divergences[0] < 0:
                self.log("sell signal")
                self.stop_large = False

            self.log('Long Stop Price: {:.2f}, current price: {:.2f}', self.stoptrailer.stop_long[0], self.data[0])
            if self.exit_long:
                self.log('收到卖出信号')
                self.order = self.close()
        # elif self.macdDivergence.top_divergences[0] > 0:
        #     self.order = self.order_target_percent(target=1.0)
        #     if self.order:
        #         self.entering = 1
        elif self.testIndicate.bottom_divergences[0] > 0:
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
    dataframe = read_dataframe(args.data, args.years, ['15min', '60min'])

    for i in range(len(dataframe)):
        temp_df = macd_extend_data(dataframe[i])
        cerebro.adddata(pandas_divergence(dataname=temp_df,
                                          divergence_top=temp_df.columns.to_list().index('divergence_top'),
                                          divergence_bottom=temp_df.columns.to_list().index('divergence_bottom')))

    cerebro.addstrategy(St)

    cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')

    strat = cerebro.run(stdstats=True, runonce=False)

    pyfoliozer = strat[0].analyzers.getbyname('pyfolio')
    returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()

    transactions.to_csv("transtion.csv")
    if args.plot:
        cerebro.plot(style='candle')


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Sample for pivot point and cross plotting')

    parser.add_argument('--data', required=False,
                        default='000651.csv',
                        help='Data to be read in')

    parser.add_argument('--years', default='2010-2020',
                        help='Formats: YYYY-ZZZZ / YYYY / YYYY- / -ZZZZ')

    parser.add_argument('--multi', required=False, action='store_true',
                        help='Couple all lines of the indicator')

    parser.add_argument('--plot', required=False, action='store_true',
                        default=False,
                        help=('Plot the result'))

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()
