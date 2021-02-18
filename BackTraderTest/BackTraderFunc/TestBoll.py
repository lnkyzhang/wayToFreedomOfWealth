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
from BackTraderTest.BackTraderFunc.Indicator.DFGLInd import DFGLInd
from BackTraderTest.BackTraderFunc.Indicator.EntryMacdDivergence import MACDEMAEntryPoint
from BackTraderTest.BackTraderFunc.Indicator.JXMJInd import JXMJIndicator
from BackTraderTest.BackTraderFunc.Indicator.PositionManger import BollPositionManager, SMAPositionManager, \
    MACDSMAPositionManager, MACDBiasPositionManager, DeviateIndicator
from BackTraderTest.BackTraderFunc.Indicator.StopTrailer import StopTrailer
from BackTraderTest.BackTraderFunc.MacdDivergence import macd_extend_data
from BackTraderTest.BackTraderFunc.St_TripleScreen import TripleScreen_extend_data
from BackTraderTest.BackTraderFunc.makeData import QAIndex2btData, QAStock2btData, QAStock2btDataOnline
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


class EMASlopeStopTrailer(bt.Indicator):
    '''
    data0: 保证同步 小周期
    data1：计算止损 日线 大周期
    '''
    lines = ('stop_long', 'stop_long_l', 'stop_long_s', 'slope_slope', 'slope_slope_zero',)
    plotinfo = dict(subplot=True, plotlinelabels=True)

    plotlines = dict(
        stop_long_l=dict(_plotskip='True', ),
        stop_long_s=dict(_plotskip='True', ),
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
        stop_long_l=dict(_plotskip='True', ),
        stop_long_s=dict(_plotskip='True', ),
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
    lines = ('top_divergences', 'bottom_divergences', 'entryPoint',)
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
        stopfactor=18.0,  # actual stop distance for smoothed atr
        verbose=True,  # print out debug info
        samebar=True,  # close and re-open on samebar
    )

    def __init__(self):

        # 布林带测试
        # self.bollPosition = BollPositionManager(self.data)
        # self.bollPosition = SMAPositionManager(self.data2)
        # self.bollPosition = SMAPositionManager(self.data)
        # self.bollPosition = MACDSMAPositionManager(self.data)
        # self.macdBiasPosition60min = MACDBiasPositionManager(self.data)
        # self.macdBiasPosition60min = MACDBiasPositionManager(self.data, name='15min')
        self.macdBiasPositionDay = MACDBiasPositionManager(self.data,  name='day')
        # self.ema20min15 = bt.talib.EMA(self.data, timeperiod=20)
        # self.sma20min15 = bt.talib.SMA(self.data, timeperiod=20)
        # self.ema60min15 = bt.talib.EMA(self.data, timeperiod=60)
        # self.sma60min15 = bt.talib.SMA(self.data, timeperiod=60)
        # self.ema120min15 = bt.talib.EMA(self.data, timeperiod=120)
        # self.sma120min15 = bt.talib.SMA(self.data, timeperiod=120)
        #
        # self.ema20min60 = bt.talib.EMA(self.data1, timeperiod=20)
        # self.sma20min60 = bt.talib.SMA(self.data1, timeperiod=20)
        # self.ema60min60 = bt.talib.EMA(self.data1, timeperiod=60)
        # self.sma60min60 = bt.talib.SMA(self.data1, timeperiod=60)
        # self.ema120min60 = bt.talib.EMA(self.data1, timeperiod=120)
        # self.sma120min60 = bt.talib.SMA(self.data1, timeperiod=120)

        self.ema20day = bt.talib.EMA(self.data, timeperiod=20)
        self.sma20day = bt.talib.SMA(self.data, timeperiod=20)
        self.ema60day = bt.talib.EMA(self.data, timeperiod=60)
        self.sma60day = bt.talib.SMA(self.data, timeperiod=60)
        self.ema120day = bt.talib.EMA(self.data, timeperiod=120)
        self.sma120day = bt.talib.SMA(self.data, timeperiod=120)


        self.JXMJIndicator = JXMJIndicator(self.data)



        # self.deviate60min = DeviateIndicator(self.data)
        # self.deviateDay = DeviateIndicator(self.data1)
        # self.macd60min = bt.ind.MACDHisto(self.data, period_me1=20, period_me2=60, period_signal=9)

        # self.macd = bt.ind.MACD(self.data, period_me1=20,period_me2=60,period_signal=9)
        # self.shortmacdhist = bt.ind.MACDHistogram(self.data, period_me1=20, period_me2=60, period_signal=9)
        # self.longmacdhist = bt.ind.MACDHistogram(self.data, period_me1=60, period_me2=120, period_signal=9)
        # self.histo = bt.ind.CrossOver(self.longmacdhist.histo, 0)
        # self.longhistoUpday = bt.ind.UpDayBool(self.longmacdhist.histo)

        self.order = None
        self.entering = None
        self.stop_large = True

        self.stoptrailer = st = StopTrailer(atrperiod=14,
                                            emaperiod=10,
                                            stopfactor=100)

        self.exit_long = bt.ind.CrossDown(self.data,
                                          self.stoptrailer.stop_long, plotname='Exit Long')

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

        self.cancel(self.order)
        if self.order is not None:
            return

        # self.entering = 0
        closing = None

        # self.order = self.order_target_percent(target=self.bollPosition.PositionPercent[0])


    def next_open(self):
        if self.data.datetime.date(0).isoformat() == '2020-01-06':
            print("123123")



        if self.position.size > 0:
            if self.JXMJIndicator.JXMJHoldState[0] == 1:
                return

            if self.JXMJIndicator.PositionPercent[0] == 0:
                if self.data.low[0] < self.JXMJIndicator.OrderPrice[0]:
                    self.order = self.order_target_percent(target=self.JXMJIndicator.PositionPercent[0],
                                                           price=self.JXMJIndicator.OrderPrice[0],
                                                           exectype=bt.Order.Stop)

            elif self.macdBiasPositionDay.PositionPercent[0] == 0:
                if self.data.low[0] < self.macdBiasPositionDay.OrderPrice[0]:
                    self.order = self.order_target_percent(target=self.macdBiasPositionDay.PositionPercent[0],
                                                           price=self.macdBiasPositionDay.OrderPrice[0],
                                                           exectype=bt.Order.Stop)

        else:
            if self.JXMJIndicator.PositionPercent[0] == 0.99:
                self.order = self.order_target_percent(target=self.JXMJIndicator.PositionPercent[0],
                                                       # price=self.JXMJIndicator.OrderPrice[0],
                                                       exectype=bt.Order.Market)
                # if self.data.open[0] > self.JXMJIndicator.OrderPrice[0]:
                #     self.order = self.order_target_percent(target=self.JXMJIndicator.PositionPercent[0],
                #                                            price=self.data.open[0],
                #                                            exectype=bt.Order.Stop)
                # elif self.data.high[0] > self.JXMJIndicator.OrderPrice[0]:
                #     self.order = self.order_target_percent(target=self.JXMJIndicator.PositionPercent[0],
                #                                            price=self.JXMJIndicator.OrderPrice[0],
                #                                            exectype=bt.Order.Stop)

            elif self.macdBiasPositionDay.PositionPercent[0] == 0.99:
                if self.JXMJIndicator.l.JXMJ[0] == 1:
                    return
                if self.data.open[0] > self.macdBiasPositionDay.OrderPrice[0]:
                    self.order = self.order_target_percent(target=self.macdBiasPositionDay.PositionPercent[0],
                                                           price=self.data.open[0],
                                                           exectype=bt.Order.Stop)
                elif self.data.high[0] > self.macdBiasPositionDay.OrderPrice[0]:
                    self.order = self.order_target_percent(target=self.macdBiasPositionDay.PositionPercent[0],
                                                           price=self.macdBiasPositionDay.OrderPrice[0],
                                                           exectype=bt.Order.Stop)





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

    cerebro = bt.Cerebro(cheat_on_open=True)
    cerebro.broker.setcommission(commission=0.0012, stocklike=True)
    # cerebro.broker.set_coo(True)

    # Data feed kwargs
    # '15min', '30min', '60min',
    # dataframe = read_dataframe(args.data, args.years, ['15min', '60min', 'd'])
    # dataframe = read_dataframe(args.data, args.years, ['15min', '60min', 'd'])
    # for i in range(len(dataframe)):
    #     cerebro.adddata(bt.feeds.PandasData(dataname=dataframe[i]))


    # for i in range(len(dataframe)):
    #     temp_df = macd_extend_data(dataframe[i])
    #     cerebro.adddata(pandas_divergence(dataname=temp_df,
    #                                       divergence_top=temp_df.columns.to_list().index('divergence_top'),
    #                                       divergence_bottom=temp_df.columns.to_list().index('divergence_bottom')))

    # dataframe = QAIndex2btData("159934", '2014-01-01', '2020-10-13')
    dataframe = QAStock2btData("000651", '2014-01-01', '2020-10-13')
    # dataframe = read_dataframe('000651.csv', '2014-2020', ['d'])[0]
    cerebro.adddata(bt.feeds.PandasData(dataname=dataframe))

    cerebro.addstrategy(St)

    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='DrawDown')
    cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='AnnualReturn')

    cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')

    strat = cerebro.run(stdstats=True, runonce=False)

    drawDown = strat[0].analyzers.DrawDown.get_analysis()
    print("max drawdown: %f", drawDown.max.drawdown)
    annualReturn = strat[0].analyzers.AnnualReturn.get_analysis()
    print("annualReturn: %s", annualReturn)

    pyfoliozer = strat[0].analyzers.getbyname('pyfolio')
    returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()

    transactions.to_csv("transtion.csv")
    if args.plot:
        # cerebro.plot(style='line')
        cerebro.plot(style='candle',iplot=False)


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Sample for pivot point and cross plotting')

    parser.add_argument('--data', required=False,
                        default='000651.csv',
                        help='Data to be read in')

    parser.add_argument('--years', default='2014-2020',
                        help='Formats: YYYY-ZZZZ / YYYY / YYYY- / -ZZZZ')

    parser.add_argument('--multi', required=False, action='store_true',
                        help='Couple all lines of the indicator')

    parser.add_argument('--plot', required=False, action='store_true',
                        default=True,
                        help=('Plot the result'))

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()
