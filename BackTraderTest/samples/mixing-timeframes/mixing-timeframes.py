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
            self.strat.entering = 0
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


class EMASlopeStopTrailer(bt.Indicator):
    '''
    data0: 保证同步 小周期
    data1：计算止损 日线 大周期
    '''
    lines = ('stop_long', 'stop_long_l', 'stop_long_s', 'slope_slope', 'slope_slope_zero', )
    plotinfo = dict(subplot=True, plotlinelabels=True)

    plotlines = dict(
        stop_long_l=dict(_plotskip='True',),
        stop_long_s=dict(_plotskip='True',),
        stop_long=dict(_plotskip='True', ),
    )

    params = dict(
        emaPeriod=26,
        slopePeriod=5.0,
        atrPeriod=13,
        stopeFactorL=3.0,
        stopFactorS=3.0,
    )

    def __init__(self):
        self.strat = self._owner  # alias for clarity

        self.slope = bt.talib.LINEARREG_SLOPE(self.data1.close, self.p.emaPeriod)
        self.l.slope_slope = bt.talib.LINEARREG_SLOPE(self.slope, self.p.slopePeriod)
        self.l.atr = bt.ind.ATR(self.data1, period=self.p.atrPeriod)
        self.stopDistL = self.l.atr * self.p.stopeFactorL
        self.stopDistS = self.l.atr * self.p.stopFactorS

        # Running stop price calc, applied in next according to market pos
        self.s_l = self.data - self.stopDistL
        self.s_s = self.data - self.stopDistS

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

                if self.l.slope_slope[0] > 0:
                    self.l.slope_slope_zero[0] = 0.01
                    self.l.stop_long[0] = self.l.stop_long_l[0]
                else:
                    self.l.slope_slope_zero[0] = -0.01
                    self.l.stop_long[0] = self.l.stop_long_s[0]


class MACDStopTrailer(bt.Indicator):
    '''
    data0: 保证同步 小周期
    data1：计算止损 日线 大周期
    MACD stop trailer.
    If the slope of macd(diff) less than 0, trun to small stop trailer.
    '''
    lines = ('stop_long', 'stop_long_l', 'stop_long_s', 'macdHist')
    plotinfo = dict(subplot=True, plotlinelabels=True)

    plotlines = dict(
        stop_long_l=dict(_plotskip='True',),
        stop_long_s=dict(_plotskip='True',),
        stop_long=dict(_plotskip='True', ),
    )

    params = dict(
        atrPeriod=13,
        stopeFactorL=3.0,
        stopFactorS=1.5,
    )

    def __init__(self):
        self.strat = self._owner  # alias for clarity

        self.l.macdHist = self.macd_hist = bt.ind.MACDHisto(self.data1, period_me1=12, period_me2=26, period_signal=9)

        self.l.atr = bt.ind.ATR(self.data1, period=self.p.atrPeriod)
        self.stopDistL = self.l.atr * self.p.stopeFactorL
        self.stopDistS = self.l.atr * self.p.stopFactorS

        # Running stop price calc, applied in next according to market pos
        self.s_l = self.data - self.stopDistL
        self.s_s = self.data - self.stopDistS

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

                if self.macd_hist[0] > self.macd_hist[-1]:
                    self.l.stop_long[0] = self.l.stop_long_l[0]
                else:
                    self.l.stop_long[0] = self.l.stop_long_s[0]


class EMASlopeEntryPoint(bt.Indicator):
    lines = ('top_divergences', 'bottom_divergences', 'entryPoint', )
    plotinfo = dict(subplot=True, plotlinelabels=True)

    params = dict(
        smaPeriod=26,
    )

    def __init__(self):
        self.strat = self._owner  # alias for clarity
        self.buyTrend = False
        self.div_top_List = []
        self.div_bottom_List = []

        self.sma = bt.talib.SMA(self.data, period=self.p.smaPeriod)

        for data in self.strat.datas:
            self.div_top_List.append(data.divergence_top)
            self.div_bottom_List.append(data.divergence_bottom)

    def next(self):
        self.l.entryPoint[0] = 0

        if self.buyTrend:
            # 这里进入之后，需要判断拐头和交叉，如果没有，要退出
            if self.data[0] > self.sma[0]:
                self.buyTrend = False
                self.l.entryPoint[0] = 1
            else:
                for div_top in self.div_top_List:
                    if div_top[0] > 0:
                        self.buyTrend = False
                        self.l.top_divergences[0] = 1
        else:
            for div_bottom in self.div_bottom_List:
                if div_bottom[0] > 0:
                    self.buyTrend = True
                    self.l.bottom_divergences[0] = 1



class Divergence(bt.Indicator):
    lines = ('top_divergences', 'bottom_divergences')

    plotinfo = dict(plot=True, subplot=True)

    def __init__(self):
        # self.strat = self._owner  # alias for clarity

        self.lines.top_divergences = -self.data.divergence_top
        self.lines.bottom_divergences = self.data.divergence_bottom

class VolumeSlope(bt.Indicator):
    lines = ('volume_slope',)

    params = dict(
        emaperiod=5,  # smooth out period for atr volatility
    )

    plotinfo = dict(plot=True, subplot=True)

    def __init__(self):
        self.l.volume_slope = bt.talib.LINEARREG_SLOPE(self.data, 5)


class SlopeSlope(bt.Indicator):
    lines = ('slope_slope', 'slope_slope_zero')

    params = dict(
        period=5,  # smooth out period for atr volatility
    )

    plotinfo = dict(plot=True, subplot=True)

    def __init__(self):
        self.slope = bt.talib.LINEARREG_SLOPE(self.data.close, self.p.period)
        self.l.slope_slope = bt.talib.LINEARREG_SLOPE(self.slope, self.p.period)

    def next(self):
        if self.l.slope_slope[0] > 0:
            self.l.slope_slope_zero[0] = 1
        else:
            self.l.slope_slope_zero[0] = -1


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
        # self.exit_long = bt.ind.CrossDown(self.data,
        #                                   st.stop_long, plotname='Exit Long')
        # macd背离
        self.testIndicate = Divergence(self.data1)
        self.testIndicate15min = Divergence(self.data0)
        self.testIndicated = Divergence(self.data2)

        # volume
        # self.obv = bt.talib.OBV(self.data2, self.data2.volume)
        # self.ad = bt.talib.AD(self.data2.high, self.data2.low, self.data2.close, self.data2.volume)
        # self.adosc = bt.talib.ADOSC(self.data2.high, self.data2.low, self.data2.close, self.data2.volume)

        # self.volumeSlope5 = VolumeSlope(self.data2)
        # self.volumeSlope30 = volumeSlope(self.data2, emaperiod=30)
        # self.volumeSlope5 = bt.talib.LINEARREG_SLOPE(self.data2.volume, 5)

        # 均线
        self.ema13 = bt.ind.EMA(self.data2, period=13)
        self.ema26 = bt.talib.EMA(self.data2, period=26)
        self.ema60 = bt.ind.EMA(self.data2, period=60)

        self.ema13Slope = bt.talib.LINEARREG_SLOPE(self.ema13, 5)
        self.ema26Slope = bt.talib.LINEARREG_SLOPE(self.ema26, 5)
        self.ema60Slope = bt.talib.LINEARREG_SLOPE(self.ema60, 5)

        self.ema26SlopeSlope = SlopeSlope(self.data2, period=5)

        self.ema26SlopeSlope1 = self.ema26SlopeSlope.slope_slope
        self.ema26SlopeSlope2 = self.ema26SlopeSlope.slope_slope_zero

        self.sma26 = bt.talib.SMA(self.data2, timeperiod=26)

        # ATR
        self.atrDay = bt.ind.ATR(self.data2)

        # TestNewIndicator
        self.test = EMASlopeEntryPoint(self.data2)
        self.entryPoint = self.test.entryPoint

        # stop price
        self.testStopTrail = MACDStopTrailer(self.data0, self.data2)

        self.exit_long = bt.ind.CrossDown(self.data,
                                          self.testStopTrail.stop_long, plotname='Exit Long')





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
        if self.position.size > 0 and self.entering == 0:  # In the market - Long
            self.log('Long Stop Price: {:.2f}, current price: {:.2f}', self.stoptrailer.stop_long[0], self.data[0])
            if self.exit_long > 0:
                self.log('收到卖出信号')
                self.order = self.close()
        # elif self.macdDivergence.top_divergences[0] > 0:
        #     self.order = self.order_target_percent(target=1.0)
        #     if self.order:
        #         self.entering = 1
        # elif self.testIndicate.bottom_divergences[0] > 0:
        #     self.order = self.order_target_percent(target=0.99)
        #     if self.order:
        #         self.entering = 1
        #         self.stop_large = True
        elif self.entryPoint[0] > 0:
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
    dataframe = read_dataframe(args.data, args.years, ['15min', '60min', 'd'])

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
        cerebro.plot(style='line')
        # cerebro.plot(style='candle')


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Sample for pivot point and cross plotting')

    parser.add_argument('--data', required=False,
                        default='000651.csv',
                        help='Data to be read in')

    parser.add_argument('--years', default='2015-2017',
                        help='Formats: YYYY-ZZZZ / YYYY / YYYY- / -ZZZZ')

    parser.add_argument('--multi', required=False, action='store_true',
                        help='Couple all lines of the indicator')

    parser.add_argument('--plot', required=False, action='store_true',
                        default=True,
                        help=('Plot the result'))

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()
