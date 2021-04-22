import backtrader as bt
import sympy
from math import fsum

from backtrader.indicators import BaseApplyN

from BackTraderTest.BackTraderFunc.Indicator.PectRankAbsInd import PercentRankAbs
from BackTraderTest.BackTraderFunc.Indicator.StopTrailer import StopTrailer

'''
布林带仓位管理
'''


class BollPositionManager(bt.Indicator):
    lines = ('PositionPercent',)
    plotinfo = dict(subplot=True, plotlinelabels=True)

    params = dict(
        bollperiod=20,
        devfactor=2.0,
    )

    def __init__(self):
        self.strat = self._owner  # alias for clarity
        # boll
        self.boll = bt.ind.BollingerBands(self.data, period=self.p.bollperiod, devfactor=self.p.devfactor)
        self.lastRelPos = -1

    def next(self):
        curRelPos = self.relativePosition()
        widthPercent = (self.boll.l.top[0] - self.boll.l.bot[0]) / self.boll.l.mid[0]

        posPercent = (0.6 - widthPercent) * 2
        if posPercent > 1:
            posPercent = 0.99
        elif posPercent < 0.2:
            posPercent = 0.2

        if curRelPos == 0:
            self.l.PositionPercent[0] = posPercent / 2
        elif curRelPos == 1:
            self.l.PositionPercent[0] = posPercent
        elif curRelPos == 2:
            self.l.PositionPercent[0] = 0

    def relativePosition(self):
        '''
        相对布林带的相对位置
        :param rail:上轨 中轨 或者 下轨 之一
        :return: 0：高于上轨 1：上轨和中轨之间  2：低于中轨
        '''
        if self.data.low[0] > self.boll.l.top[0]:
            return 0
        elif self.boll.l.top[0] > self.data[0] > self.boll.l.mid[0]:
            return 1
        else:
            return 2


'''
均线仓位管理
低于均线清仓，高于均线满仓
'''


class SMAPositionManager(bt.Indicator):
    lines = ('PositionPercent', 'OrderPrice', 'sma20Slope', 'ema20Slope')
    plotinfo = dict(subplot=True, plotlinelabels=True)

    params = dict(
        period=20,
    )

    def __init__(self):
        self.strat = self._owner  # alias for clarity
        # sma
        # self.sma = bt.ind.SMA(self.data, period=self.p.period)
        self.sma20 = bt.talib.SMA(self.data, timeperiod=self.p.period)
        self.ema20 = bt.talib.EMA(self.data, timeperiod=self.p.period)
        self.sma60 = bt.talib.SMA(self.data, timeperiod=60)
        self.l.sma20Slope = self.sma20Slope = bt.talib.LINEARREG_SLOPE(self.sma20, timeperiod=2) * 100
        self.l.ema20Slope = self.ema20Slope = bt.talib.LINEARREG_SLOPE(self.ema20, timeperiod=2) * 100
        self.sma60Slope = bt.talib.LINEARREG_SLOPE(self.sma60, 1)

    def next(self):
        '''
        卖出：20日EMA或20日SMA任一个拐头向下
        买入：20日EMA或20日SMA全部拐头向上
        '''
        if self.strat.position.size > 0:
            # 20日的ema和sma有一个拐头向下
            self.l.OrderPrice[0] = max(self.ema20[0], self.data[-19])
            self.l.PositionPercent[0] = 0
        else:
            # 20日的ema和sma全部拐头向上
            self.l.OrderPrice[0] = max(self.ema20[0], self.data[-19])
            self.l.PositionPercent[0] = 0.99

        '''
        卖出：20日EMA拐头向下
        买入：20日EMA拐头向上
        '''
        # if self.strat.position.size > 0:
        #     # 20日的ema和sma有一个拐头向下
        #     self.l.OrderPrice[0] = self.ema20[0]
        #     self.l.PositionPercent[0] = 0
        # else:
        #     # 20日的ema和sma有一个拐头向上
        #     self.l.OrderPrice[0] = self.ema20[0]
        #     self.l.PositionPercent[0] = 0.99


'''
macd和ema的
'''


class MACDSMAPositionManager(bt.Indicator):
    lines = ('PositionPercent', 'OrderPrice', 'sma20Slope', 'ema20Slope', 'macd', 'macdsignal', 'macdhist')
    plotinfo = dict(subplot=True, plotlinelabels=True)

    params = dict(
        period=20,
    )

    def __init__(self):
        self.strat = self._owner  # alias for clarity
        # sma
        # self.sma = bt.ind.SMA(self.data, period=self.p.period)
        self.sma20 = bt.talib.SMA(self.data, timeperiod=self.p.period)
        self.ema20 = bt.talib.EMA(self.data, timeperiod=self.p.period)
        self.sma60 = bt.talib.SMA(self.data, timeperiod=60)
        self.l.sma20Slope = self.sma20Slope = bt.talib.LINEARREG_SLOPE(self.sma20, timeperiod=2) * 100
        self.l.ema20Slope = self.ema20Slope = bt.talib.LINEARREG_SLOPE(self.ema20, timeperiod=2) * 100
        self.sma60Slope = bt.talib.LINEARREG_SLOPE(self.sma60, 1)

        self.macd = bt.ind.MACDHisto(self.data, period_me1=20, period_me2=60, period_signal=9)
        self.l.macd = self.macd.macd
        self.l.macdsignal = self.macd.signal
        self.l.macdhist = self.macd.histo
        # self.macdhistSlope = bt.talib.LINEARREG_SLOPE(self.l.macdhist, timeperiod=2)

    def next(self):
        '''
        卖出：20日EMA或20日SMA任一个拐头向下
        买入：20日EMA或20日SMA全部拐头向上
        '''
        if self.data.datetime.date(0).isoformat() == '2016-02-19':
            print("123123")
        if self.strat.position.size > 0:
            if self.l.macdhist[0] < self.l.macdhist[-1] > 0:
                # 20日的ema和sma有一个拐头向下
                self.l.OrderPrice[0] = max(self.ema20[0], self.data[-19])
                self.l.PositionPercent[0] = 0

        elif self.l.macdhist[0] > self.l.macdhist[-1] > -0.1 and self.l.macdsignal > -1:
            # 20日的ema和sma全部拐头向上
            self.l.OrderPrice[0] = max(self.ema20[0], self.data[-19])
            self.l.PositionPercent[0] = 0.99
        else:
            self.l.PositionPercent[0] = -1

        '''
        卖出：20日EMA拐头向下
        买入：20日EMA拐头向上
        '''
        # if self.strat.position.size > 0:
        #     # 20日的ema和sma有一个拐头向下
        #     self.l.OrderPrice[0] = self.ema20[0]
        #     self.l.PositionPercent[0] = 0
        # else:
        #     # 20日的ema和sma有一个拐头向上
        #     self.l.OrderPrice[0] = self.ema20[0]
        #     self.l.PositionPercent[0] = 0.99


'''
增加乖离率
'''


class MACDBiasPositionManager(bt.Indicator):
    # lines = ('holdState', 'pctAtrPrice','PositionPercent', 'OrderPrice', 'sma20Slope', 'ema20Slope', 'macd', 'macdsignal', 'macdhist', 'macdlong',
    #          'macdlongsignal', 'macdlonghist', 'nextlevel', 'stop_long', )
    '''
    macdHistMoveRank: macd 柱线图 中，当日值与前日值的差值，统计并排名
    '''
    lines = ('holdState', 'natr','PositionPercent', 'OrderPrice', 'macd', 'macdsignal', 'macdhist', 'stop_long', 'natrRank', 'shortbiasrank', 'longbiasrank', 'macdHistMoveRank', 'jxml', 'riskLevel')
    plotinfo = dict(subplot=True, plotlinelabels=True)

    plotlines = dict(
        stop_long=dict(_plotskip='True',),
        OrderPrice=dict(_plotskip='True',),
        PositionPercent=dict(_plotskip='True', ),
        holdState=dict(_plotskip='True', ),
        natr=dict(_plotskip='True', ),
        macdsignal=dict(_plotskip='True', ),
        macd=dict(_plotskip='True', ),
        macdHistMoveRank=dict(_plotskip='True', ),
        # macdhist=dict( _method='bar',),
        # pctAtrPrice=dict(_plotskip='True', ),
    )

    params = dict(
        period=20,
        name='',
        msrThresholdValue=0.99, # macdsignalRank的阈值
    )

    def __init__(self):
        self.strat = self._owner  # alias for clarity
        # sma
        # self.sma = bt.ind.SMA(self.data, period=self.p.period)
        self.sma20 = bt.talib.SMA(self.data, timeperiod=self.p.period)
        self.ema20 = bt.talib.EMA(self.data, timeperiod=self.p.period)
        self.sma60 = bt.talib.SMA(self.data, timeperiod=60)
        self.ema60 = bt.talib.EMA(self.data, timeperiod=60)
        self.sma120 = bt.talib.SMA(self.data, timeperiod=120)
        self.ema120 = bt.talib.EMA(self.data, timeperiod=120)

        # self.l.sma20Slope = self.sma20Slope = bt.talib.LINEARREG_SLOPE(self.sma20, timeperiod=2) * 100
        # self.l.ema20Slope = self.ema20Slope = bt.talib.LINEARREG_SLOPE(self.ema20, timeperiod=2) * 100
        # self.sma60Slope = bt.talib.LINEARREG_SLOPE(self.sma60, 1)
        # self.ema120Slope = bt.talib.LINEARREG_SLOPE(self.ema120, 2)

        self.macd = bt.ind.MACDHisto(self.data, period_me1=20, period_me2=60, period_signal=9)
        self.l.macd = self.macd.macd
        self.l.macdsignal = self.macd.signal
        self.l.macdhist = self.macd.histo
        # self.l.macdhistobool = bt.ind.CrossOver(self.macd.histo, 0)
        self.l.macdHistMoveRank = bt.ind.PercentRank(abs(bt.ind.UpMove(self.l.macdhist)), period=144)

        self.macdlong = bt.ind.MACDHisto(self.data, period_me1=20, period_me2=120, period_signal=9)
        # self.macdlong = self.macdlong.macd
        # self.macdlongsignal = self.macdlong.signal
        # self.macdlonghist = self.macdlong.histo
        # self.l.macdlonghistobool = bt.ind.CrossOver(self.macdlonghist,0)

        # self.pctRank = PercentRankAbs(self.l.macdsignal, period=200)
        self.l.shortbiasrank = bt.ind.PercentRank(abs(self.l.macdsignal), period=144)
        self.l.longbiasrank = bt.ind.PercentRank(abs(self.macdlong.signal), period=144)


        self.lowestHist = bt.ind.Lowest(self.l.macdhist, period=144)
        self.lowestDiff = bt.ind.Lowest(self.l.macdsignal, period=144)
        # self.macdhistSlope = bt.talib.LINEARREG_SLOPE(self.l.macdhist, timeperiod=2)

        self.pctATR = bt.ind.ATR(self.data)
        self.riskLevel = 0

        self.l.natr = bt.talib.NATR(self.data.high, self.data.low, self.data.close)
        self.l.natrRank = bt.ind.PercentRank(self.l.natr, period=144)

        # 均线密集计算
        # self.l.jxmj = JXMJIndicator(self.data)

        # 止损
        atr = bt.ind.ATR(self.data, period=14)
        emaatr = bt.ind.EMA(atr, period=10)
        self.stop_dist = emaatr * 10
        self.s_l = self.data - self.stop_dist

    def solveDiff(lastDea, hist, N):
        '''
        根据macd 反推 diff
        :param lastDea:上一个dea
        :param hist:需要的hist
        :param N:周期
        :return:
        '''
        x = sympy.symbols('x')
        return sympy.solve(x - ((2 * x + ((N - 1) * lastDea)) / (N + 1)) - hist, x)

    def solvePrice(lastShortEma, lastLongEma, diff, shortN, longN):
        '''
        根据macd 反推 price
        :param lastShortEma:上一个短期ema
        :param lastLongEma:上一个长期ema
        :param diff:计算的diff
        :param shortN:短期周期
        :param longN:长期周期
        :return:
        '''
        x = sympy.symbols('x')
        return sympy.solve(((2 * x + ((shortN - 1) * lastShortEma)) / (shortN + 1)) - (
                (2 * x + ((longN - 1) * lastLongEma)) / (longN + 1)) - diff, x)

    def solveShortMidCrossPrice(self, shortSMA, shortEndData, shortN,midSMA, midEndData,midN):
        '''
        推算sma20和sma60交叉时的价格
        :param shortEMA:
        :param shortEndData:
        :param shortN:
        :param midEMA:
        :param minEndData:
        :param midN:
        :return:
        '''
        x = sympy.symbols('x')
        return sympy.solve(shortSMA + (x / shortN) - (shortEndData / shortN) - midSMA - (x / midN) + (midEndData / midN) , x)

    def next(self):
        '''
        卖出：20日EMA或20日SMA任一个拐头向下
        买入：20日EMA或20日SMA全部拐头向上
        '''
        if self.l.shortbiasrank[0] > 0.5:
            print("name: %5s, date: %s, macdsignalRank: %.3f, diff :%.3f, lowest hist: %.3f, lowest diff:%.3f natr:%.3f, atrPctRank: %.3f"
                  %(self.p.name, self.data.datetime.date(0).isoformat(), self.l.shortbiasrank[0], self.l.macdsignal[0], self.lowestHist[0],
                  self.lowestDiff[0],  self.l.natr[0], self.l.natrRank[0]))

        if self.data.datetime.date(0).isoformat() < '2010-04-17':
            return
        if self.data.datetime.date(0).isoformat() == '2015-12-21':
            print("1")
        if self.data.datetime.date(0).isoformat() == '2013-02-02':
            pass

        # 风险分级
        if self.riskLevel == 0:
            if self.l.shortbiasrank[0] > self.p.msrThresholdValue or self.l.longbiasrank[0] > self.p.msrThresholdValue:
                self.riskLevel = 1
        elif self.riskLevel == 1:
            if self.l.shortbiasrank[0] > 0.9 or self.l.longbiasrank[0] > 0.9:
                pass
            elif self.l.natrRank[0] < 0.6:
                self.riskLevel = 0

        self.l.riskLevel[0] = self.riskLevel






        # self.l.pctAtrPrice[0] = self.pctATR[0] / self.ema20[0] * 100

        # if len(self.l.holdState) > 1:
        #     self.l.holdState[0] = self.l.holdState[-1]
        # else:
        #     self.l.holdState[0] = 0
        #
        # if self.l.PositionPercent[-1] == 0.99 and self.data.high[0] >  self.l.OrderPrice[-1]:
        #     self.l.holdState[0] = 5
        #
        # if self.l.PositionPercent[-1] == 0 and self.data.low[0] < self.l.OrderPrice[-1]:
        #     self.l.holdState[0] = 0


        '''
        2020-11-01 卖出条件
        1.大幅乖离之后且atr未恢复到正常水平之前
        2.60日sma拐头向下或20日sma与60日sma空头排列
        3.跌破60日ema均綫
            前提是20日sma与60日sma乖离率不是很小的时候。
            如果20日和60日sma的乖离率小于3%，等待不卖
        4.1、2的充分条件是破线 20日ema或sma
        5.均线密集不卖
        '''
        # todo 均线密集的问题没解决  包括进场和出场
        if self.strat.position.size > 0:
            # 判断均线密集
            # if abs(self.sma20[0] / self.sma60[0] - 1) < 0.05 and abs(self.sma60[0] / self.sma120[0] - 1) < 0.05:
            #     return

            if self.riskLevel == 1:
                self.l.OrderPrice[0] = max(self.ema20[0], self.data[-19])
                self.l.PositionPercent[0] = 0
            else:
                # crossPrice = self.solveShortMidCrossPrice(self.sma20[0], self.data[-19], 20, self.sma60[0], self.data[-59], 60)
                if abs(self.sma20[0] / self.sma60[0] - 1) < 0.02:
                    return
                elif self.sma60[0] < self.sma60[-1] or self.sma60[0] > self.sma20[0]:
                    self.l.OrderPrice[0] = max(self.ema20[0], self.data[-19])
                    self.l.PositionPercent[0] = 0
                else:
                    self.l.OrderPrice[0] = max(self.ema60[0], self.data[-59])
                    self.l.PositionPercent[0] = 0

        else:
            '''
            2020-11-1买入逻辑修改：
            增加：
            1.大幅乖离（短中、中长）之后，且ATR、乖离率未恢复到正常水平之前：
                不进场
                ----如果均线全部多头排列，且斜率全部向上，则进场
            2.60日sma斜率大于0，且短、中、长期均线多`头排列，则进场
            3.1、2的充分条件破线20日sma和ema
            4.均线密集不买
            '''


            if self.riskLevel == 1:
                pass
                # if self.sma60[0] > self.sma60[-1] and self.sma20[0] > self.sma20[-1] and self.sma20[0] > self.sma60[0] \
                #         and self.ema60[0] > self.ema60[-1] and self.ema20[0] > self.ema20[-1] and self.ema20[0] > self.ema60[0]:
                #     self.l.OrderPrice[0] = max(self.ema20[0], self.data[-19])
                #     self.l.PositionPercent[0] = 0.99
            else:
                if abs(self.sma20[0] / self.sma60[0] - 1) < 0.05 and abs(self.sma60[0] / self.sma120[0] - 1) < 0.05 and abs(self.data[0] / self.sma20[0] -1) < 0.05:
                    return
                if self.sma60[0] > self.sma60[-1] and self.sma20[0] > self.sma60[0] and self.sma20[0] > self.sma20[-1] and self.ema20[0] > self.ema20[-1] \
                        and self.sma60[0] > self.sma120[0]:
                    self.l.OrderPrice[0] = max(self.ema20[0], self.data[-19])
                    self.l.PositionPercent[0] = 0.99

            '''
            2020-11-8 买入逻辑
            1.大幅乖离（短中、中长）之后，且ATR、乖离率未恢复到正常水平之前：
                不进场
                ----如果均线全部多头排列，且斜率全部向上，则进场
            2.60日sma斜率大于0，且短、中、长期均线多头排列，则进场
            3.1、2的充分条件破线20日sma和ema
            4.均线密集(多头排列)
                突破boll上轨买入
            '''


###############################################2020-10-31########################################################
        # '''
        # 2020-10-27 卖出条件
        # 1.多头排列时，大幅乖离之后卖出
        # 2.空头排列时，乖离没有减少的趋势不卖
        #     柱线图小于0时，可卖
        #     柱线图大于0时，有明显下降趋势可卖
        #
        # '''
        # if self.l.holdState[0] == 5:
        # # if self.strat.position.size > 0:
        #     self.l.stop_long[0] = max(self.s_l[0], self.l.stop_long[-1])
        #     if self.l.macdsignal[0] < 0:
        #         # todo 这个位置还需要继续衡量
        #         if self.l.macdhist[0] < self.l.macdhist[-1] < 0 \
        #             or (self.l.macdhist[0] < self.l.macdhist[-1] and self.l.macdHistMoveRank[0] > 0.8) :
        #             self.l.OrderPrice[0] = max(self.ema20[0], self.data[-19])
        #             self.l.PositionPercent[0] = 0
        #     elif self.l.macdsignal[0] > 0 and self.macdsignalRank[0] < self.p.msrThresholdValue:
        #         if self.riskLevel == 1:
        #             self.l.OrderPrice[0] = max(self.ema20[0], self.data[-19])
        #             self.l.PositionPercent[0] = 0
        #         elif self.riskLevel == 0:
        #             # pass
        #             self.l.OrderPrice[0] = self.l.stop_long[0]
        #             self.l.PositionPercent[0] = 0
        #
        #     elif self.macdsignalRank[0] > self.p.msrThresholdValue:
        #         self.l.OrderPrice[0] = max(self.ema20[0], self.data[-19])
        #         self.l.PositionPercent[0] = 0
        # else:
        #     '''
        #     2020-10-27之前的买入逻辑
        #     1.大幅乖离之后不进场
        #     2.短、中、长期均线明显空头排列不进场
        #     3.当短、中、长期均线多头排列时，乖离率有增大的趋势
        #         macd柱状图的cur_value > pre_value
        #     4.当短、中、长期均线空头排列时，乖离率有增大的趋势且正在增大
        #         macd柱状图的cur_value > pre_value 且 cur_value > 0
        #     5.破线。同时突破短期ema和sma均线
        #     '''
        #     if self.riskLevel == 1:
        #         return
        #     if self.l.macdsignal[0] > 0:
        #         # todo  self.lowestHist[0] / 4 不合理
        #         if self.l.macdhist[0] > self.l.macdhist[-1] > self.lowestHist[0] / 4:
        #             self.l.OrderPrice[0] = max(self.ema20[0], self.data[-19])
        #             self.l.PositionPercent[0] = 0.99
        #     elif self.lowestDiff[0] / 4 < self.l.macdsignal < 0:
        #         # pass
        #         if self.l.macdhist[0] > self.l.macdhist[-1] > 0:
        #             self.l.OrderPrice[0] = max(self.ema20[0], self.data[-19])
        #             self.l.PositionPercent[0] = 0.99

###############################################2020-10-31########################################################

        # if self.strat.position.size > 0 :
        #     if self.l.macdsignal[0] < 0:
        #         # todo 这个位置还需要继续衡量
        #         if self.l.macdhist[0] < self.l.macdhist[-1] - 0.01:
        #             self.l.OrderPrice[0] = max(self.ema20[0], self.data[-19])
        #             self.l.PositionPercent[0] = 0
        #     elif self.l.macdsignal[0] > 0 and self.macdsignalRank[0] < 0.99:
        #         pass
        #     elif self.macdsignalRank[0] > 0.99:
        #         self.l.OrderPrice[0] = max(self.ema20[0], self.data[-19])
        #         self.l.PositionPercent[0] = 0
        # else:
        #     if self.l.macdsignal[0] > 0:
        #         if self.l.macdhist[0] > self.l.macdhist[-1] > self.lowestHist[0] / 4:
        #             self.l.OrderPrice[0] = max(self.ema20[0], self.data[-19])
        #             self.l.PositionPercent[0] = 0.99
        #     elif self.lowestDiff[0] / 4 < self.l.macdsignal < 0:
        #         if self.l.macdhist[0] > self.l.macdhist[-1] > 0:
        #             self.l.OrderPrice[0] = max(self.ema20[0], self.data[-19])
        #             self.l.PositionPercent[0] = 0.99


'''
乖离率判断指标
'''
class DeviateIndicator(bt.Indicator):
    lines = ('deviateRank',)
    plotinfo = dict(subplot=True, plotlinelabels=True)

    plotlines = dict(
        # macdhist=dict( _method='bar',),
        # pctAtrPrice=dict(_plotskip='True', ),
        deviateRank=dict(_plotskip='True', ),
    )

    params = dict(
        period_me1=20,
        period_me2=60,
        name='',
        msrThresholdValue=0.99, # macdsignalRank的阈值
    )

    def __init__(self):
        self.macd = bt.ind.MACDHisto(self.data, period_me1=self.p.period_me1, period_me2=self.p.period_me2, period_signal=9)
        self.l.deviateRank = bt.ind.PercentRank(self.macd.signal, period=200)






# bias: AwesomeOscillator\PercentagePriceOscillator\PercentagePriceOscillatorShort\PriceOscillator

# suppor and resistant: DemarkPivotPoint\FibonacciPivotPoint\MovingAverageSimpleEnvelope\PivotPoint

# PrettyGoodOscillator:bias & sr

# jxmj use sma
# dfgl use ema