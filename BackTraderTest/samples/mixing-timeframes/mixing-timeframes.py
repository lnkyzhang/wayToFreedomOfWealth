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

from BackTraderTest.BackTraderFunc.DataReadFromCsv import read_dataframe
from BackTraderTest.BackTraderFunc.DataResample import data_min_resample
from BackTraderTest.BackTraderFunc.MacdDivergence import macd_extend_data
from back_forecast.learn_quant.MACD.jukuan_macd_signal import *

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


class MacdDivergence(bt.Indicator):
    lines = ('macd', 'signal', 'top_divergences', 'bottom_divergences', 'gold_cross', 'death_cross')

    params = (('value', 5),)

    plotlines = dict(
        top_divergences=dict(marker='*', markersize=15.0, color='lime', fillstyle='full'),
        bottom_divergences=dict(marker='*', markersize=15.0, color='red', fillstyle='full'),
        gold_cross=dict(_plotskip=True, marker='s', markersize=3.0, color='red', fillstyle='full'),
        death_cross=dict(_plotskip=True, marker='s', markersize=3.0, color='lime', fillstyle='full')
    )

    plotinfo = dict(plot=True, subplot=True, plotforce=True)

    macdCache = MacdCache(None, None)  # mcad背离

    divergences_df = pd.DataFrame(
        columns=[CLOSE, DIF, DEA, MACD, GOLD, DEATH, DIF_LIMIT_TM, CLOSE_LIMIT_TM, MACD_LIMIT_TM])

    def __init__(self):
        '''
        backtrader中的MACD，macd是diff，signal是dea
        而jukuan_macd_signal中的macd是(dif - dea) * 2，diff是长短线差离，dea是diff的差离
        '''
        self.lines.macd = self.macd = btind.MACD(self.data0)
        self.lines.signal = self.macd.signal
        self.cross = self.crossOver = btind.CrossOver(self.macd.macd, self.macd.signal)
        self.diff = (self.macd.macd - self.macd.signal) * 2

    def next(self):
        tm = self.data.datetime.date(0).isoformat()
        self.divergences_df.loc[tm, [CLOSE, DIF, DEA, MACD]] = self.data0.close[0], self.macd[0], self.macd.signal[0], \
                                                               self.diff[0]

        if self.crossOver[0] > 0:
            self.divergences_df.loc[tm, [GOLD, DEATH]] = True, False
            self.lines.gold_cross[0] = self.macd + 0.5

        elif self.crossOver[0] < 0:
            self.divergences_df.loc[tm, [GOLD, DEATH]] = False, True
            self.lines.death_cross[0] = self.macd - 0.5

        else:
            self.divergences_df.loc[tm, [GOLD, DEATH]] = False, False

        self.macdCache.indicator.last_limit_point_tm(self.divergences_df, -1)

        self.macdCache.update_divergences(self.divergences_df, 'divergences')

        self.divergences = self.macdCache.divergences[
            'divergences'] if 'divergences' in self.macdCache.divergences.keys() else []

        if len(self.divergences) > 0:
            if self.macdCache.divergences['divergences'][0].divergence_type is DivergenceType.Top:
                # self.lines.top_divergences[0] = self.macd.macd[0]
                self.lines.top_divergences[0] = -1.0
            elif self.macdCache.divergences['divergences'][0].divergence_type is DivergenceType.Bottom:
                # self.lines.bottom_divergences[0] = self.macd.macd[0]
                self.lines.bottom_divergences[0] = 1.0

class StopTrailer(bt.Indicator):
    _nextforce = True  # force system into step by step calcs

    lines = ('stop_long',)
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

        self.s_l = self.data * 0.7

    def next(self):
        # When entering the market, the stop has to be set
        if self.strat.entering > 0:  # entering long
            self.l.stop_long[0] = self.s_l[0]
        elif self.strat.entering < 0:  # entering short
            self.l.stop_short[0] = self.s_s[0]

        else:  # In the market, adjust stop only in the direction of the trade
            if self.strat.position.size > 0:
                self.l.stop_long[0] = max(self.s_l[0], self.l.stop_long[-1])
            elif self.strat.position.size < 0:
                self.l.stop_short[0] = min(self.s_s[0], self.l.stop_short[-1])

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

        # 买入
        self.macdDivergence = MacdDivergence()


        # 止损
        self.stoptrailer = st = StopTrailer(atrperiod=self.p.atrperiod,
                                            emaperiod=self.p.emaperiod,
                                            stopfactor=self.p.stopfactor)

        # Exit Criteria (Stop Trail) for long / short positions
        self.exit_long = bt.ind.CrossDown(self.data,
                                          st.stop_long, plotname='Exit Long')

        # self.testIndicate = bt.ind.AllN(self.data0.divergence_top)
        # self.testIndicate2 = bt.ind.AllN(self.data0.divergence_bottom)

        self.testIndicate = Divergence()

        self.order = None
        self.entering = None

    def start(self):
        self.entering = 0

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

            self.log('Long Stop Price: {:.2f}', self.stoptrailer.stop_long[0])
            if self.exit_long:
                self.log('收到卖出信号')
                self.order = self.close()
        # elif self.macdDivergence.top_divergences[0] > 0:
        #     self.order = self.order_target_percent(target=1.0)
        #     if self.order:
        #         self.entering = 1
        elif self.macdDivergence.gold_cross[0] > 0:
            self.order = self.order_target_percent(target=1.0)
            if self.order:
                self.entering = 1

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


def runstrat():
    args = parse_args()

    cerebro = bt.Cerebro()

    # Data feed kwargs
    # '15min', '30min', '60min',
    dataframe = read_dataframe(args.data, args.years, ['60min'])

    for i in range(len(dataframe)):
        temp_df = macd_extend_data(dataframe[i])

        # emp_df.loc[50:100, ['divergence_top']] = 0
        # temp_df.loc[temp_df['divergence_top'] == False, ['divergence_top']] = 0

        cerebro.adddata(pandas_divergence(dataname=temp_df,
                                          divergence_top=temp_df.columns.to_list().index('divergence_top'),
                                          divergence_bottom=temp_df.columns.to_list().index('divergence_bottom')))

    cerebro.addstrategy(St)

    cerebro.run(stdstats=True, runonce=False)
    if args.plot:
        cerebro.plot(style='candle')


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Sample for pivot point and cross plotting')

    parser.add_argument('--data', required=False,
                        default='002594.csv',
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
