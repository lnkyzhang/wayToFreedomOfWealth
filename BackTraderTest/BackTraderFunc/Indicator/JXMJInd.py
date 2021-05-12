import backtrader as bt
import sympy
from math import fsum
from backtrader.indicators import BaseApplyN


'''
均线密集判断
大幅乖离判断
统计在过去周期内，有多少天是均线密集

2020-11-08 
均线密集条件
1.60日sma与120sma多头排列
2.当前日期cs，sm，ml，偏离率都小于5%
3.近期20或以上bar，均线密集时期（cs，sm，ml，偏离率都小于5%）大于90%

退出均线密集holdState
1.距离holdState内最低点超过13%
2.多头大幅乖离
3.大量下跌（2倍于5日成交量均值）

均线密集进场条件
1.均线密集时不进场 ？
2.非均线密集，但是holdState为1时
    布林带多头方向开口扩大（top-bot > 1.5*ema(top-bot, 20)）,且price > mid
    布林带空头方向开口扩大，则进场点为布林带开口有变小的趋势 (布林cd.histo变小)
3.布林开口明显扩大与离开均线密集状态相差不超过5个bar
    

大幅乖离条件
1.60日ema与120日ema之间的差值在过去某个周期内超过99%的bar
'''
class JXMJIndicator(bt.Indicator):
    # JXMJ:通过条件判断的均线密集
    # JXMJHoldState:均线密集发生之后，退出均线密集状态发生之前
    # BollRange: 布林线开口，根据top与bot计算,1为多头变大，-1为空头变大
    lines = ('JXMJ', 'JXMJHoldState','JXMJBuySellPoint','DFGL', 'OrderPrice', 'PositionPercent','BollRange',
             "priceIntense", "bollIntense", "bollIntense")
    plotinfo = dict(subplot=True, plotlinelabels=True)

    plotlines = dict(
        PositionPercent=dict(_plotskip='True',),
        OrderPrice=dict(_plotskip='True',),
        BollRange=dict( color = 'black',),
    )

    params = dict(
        period_short=20,
        period_middle=60,
        period_long=120,
        name='',
        period_jxmj=21,  # 均线密集判断周期
        jxmj_ThresholdValue=19, # 周期内均线密集最小时间
        jxmj_lowPect=21, # 判断退出均线密集状态的，价格下降的百分比
        period_dfgl=144,  # 大幅乖离判断周期(用rank的方法)
        dfgl_ThresholdValue=0.99,  # 大幅乖离的判断rank的阈值
        boll_range_ThresholdValue=1.5,  # boll 开口比例
        holdState_upper_ThresholdValue=0.21,  # 均线密集holdState退出的判断条件
        period_volumeShort = 5, # 短期成交量均值周期

        jxmj_ThresholdPctLimit = 0.05,
    )

    def __init__(self):
        self.strat = self._owner  # alias for clarity

        self.smaShort = bt.ind.SMA(self.data, period=self.p.period_short)
        self.smaMid = bt.ind.SMA(self.data, period=self.p.period_middle)
        self.smaLong = bt.ind.SMA(self.data, period=self.p.period_long)
        self.emaShort = bt.ind.EMA(self.data, period=self.p.period_short)
        self.emaMid = bt.ind.EMA(self.data, period=self.p.period_middle)
        self.emaLong = bt.ind.EMA(self.data, period=self.p.period_long)

        self.smaVolumeShort = bt.ind.SMA(self.data.volume, period=self.p.period_volumeShort)

        self.boll = bt.ind.BollingerBands(self.data)
        self.bollDiff = self.boll.top - self.boll.bot
        self.bollSignal = bt.ind.EMA(self.bollDiff, period=self.p.period_short)
        self.l.BollRange = bt.If(bt.And(self.bollDiff/self.p.boll_range_ThresholdValue > self.bollSignal, self.data > self.boll.mid), 1, 0)
        self.l.BollRange = bt.If(
            bt.And(self.bollDiff / self.p.boll_range_ThresholdValue > self.bollSignal, self.data < self.boll.mid), -1, self.l.BollRange)
        self.bollHisto = self.bollDiff - self.bollSignal
        self.boll_signal_Pct = self.bollDiff / self.bollSignal

        self.natr = bt.ind.ATR(self.data, period=self.p.period_short) / self.data
        self.natrEmaShort = bt.ind.EMA(self.natr)
        self.natr_ema_Pct = self.natr / self.natrEmaShort

        smaMin = bt.ind.Min(self.smaShort, self.smaMid, self.smaLong)
        smaMax = bt.ind.Max(self.smaShort, self.smaMid, self.smaLong)
        emaMin = bt.ind.Min(self.emaShort, self.emaMid, self.emaLong)
        emaMax = bt.ind.Max(self.emaShort, self.emaMid, self.emaLong)
        smaIntense = bt.If((smaMax - smaMin) < self.data * self.p.jxmj_ThresholdPctLimit, True, False)
        emaIntense = bt.If((emaMax - emaMin) < self.data * self.p.jxmj_ThresholdPctLimit, True, False)

        self.l.priceIntense = bt.And(smaIntense, emaIntense)
        self.l.bollIntense = JXMJDayFsumIndicator(self.boll_signal_Pct, period=self.p.period_short, func= lambda d: fsum((x < 1) for x in d) > self.p.period_short * 0.7 or fsum((x < 1.1 ) for x in d) > self.p.jxmj_ThresholdValue)
        self.l.natrIntense = JXMJDayFsumIndicator(self.natr_ema_Pct, period=self.p.period_short, func= lambda d: fsum((x < 1) for x in d) > self.p.period_short * 0.7 or fsum((x < 1.1 ) for x in d) > self.p.jxmj_ThresholdValue)

        self.l.JXMJ = bt.If(bt.And(self.priceIntense, bt.And(self.bollIntense, self.natrIntense)), 1, 0)

        self.l.JXMJHoldState = self.data - self.data
        self.l.JXMJBuySellPoint = self.data - self.data
        self.lastClosePrice = 0

        dfgl_cs = self.data - self.emaShort
        dfgl_sm = self.emaShort - self.emaMid
        dfgl_ml = self.emaMid - self.emaLong

        self.dfgl = bt.ind.PercentRank(abs(dfgl_sm), period=self.p.period_dfgl)
        self.l.DFGL = bt.If( bt.And(self.dfgl > self.p.dfgl_ThresholdValue, dfgl_sm > 0), 1, 0)

        self.holdStateLow = 9999
        self.holdStateHigh = 0

    def next(self):
        if self.data.datetime.date(0).isoformat() == '2013-06-26':
            print("111")

        if self.l.JXMJ[0] == 1:
            self.l.JXMJHoldState[0] = 1

        if self.l.JXMJ[0] == 0 and self.l.JXMJ[-1] == 1:
            self.lastClosePrice = self.data[-1]

        if self.l.JXMJHoldState[-1] == 1 and self.l.JXMJ[0] == 0:
            if self.data[0] < self.lastClosePrice * (1- (self.p.jxmj_lowPect / 100)) \
                    or self.l.DFGL[0] == 1\
                    or self.data[0] > self.holdStateLow * (1 + self.p.holdState_upper_ThresholdValue):
                self.l.JXMJHoldState[0] = 0
                self.holdStateHigh = 0
                self.holdStateLow = 9999
            else:
                self.l.JXMJHoldState[0] = 1
                if self.data[0] > self.holdStateHigh:
                    self.holdStateHigh = self.data[0]
                if self.data[0] < self.holdStateLow:
                    self.holdStateLow = self.data[0]



        if (self.l.JXMJHoldState[0] == 1 and self.l.JXMJ[0] == 0) or self.l.JXMJ[0] == 1:
            if self.l.BollRange[0] == 1:
                # 直接拉起
                self.l.JXMJBuySellPoint[0] = 1.5
                self.l.OrderPrice[0] = self.emaShort[0]
                self.l.PositionPercent[0] = 0.99
                # self.l.JXMJHoldState[0] = 0
            else:

                # 剔除放量跌的情况（2倍与5日均量以上为放量）
                if self.data.volume[0] > 2 * self.smaVolumeShort[0] and self.data.close[0] < self.data.open[0]:
                    self.l.JXMJHoldState[0] = 0
                    return
                # 震仓
                if self.l.BollRange[0] == -1:
                    if self.bollHisto[0] < self.bollHisto[-1]:
                        index = -1
                        bollIndex = 0
                        jxmjIndex = 0
                        while(index > -100):
                            if self.l.BollRange[index] == 0:
                                bollIndex = index
                            if self.l.JXMJ[index] == 1:
                                jxmjIndex = index
                            if bollIndex != 0 and jxmjIndex != 0:
                                break
                            index -= 1
                        if abs(bollIndex - jxmjIndex) < 5:
                            self.l.JXMJBuySellPoint[0] = 2
                            self.l.OrderPrice[0] = self.data[0]
                            self.l.PositionPercent[0] = 0.99
                            # self.l.JXMJHoldState[0] = 0




            # elif self.data.high[0] > self.boll.mid[0]:
            #     self.l.JXMJBuySellPoint[0] = 1
            #     if self.strat.position.size == 0:
            #         self.l.OrderPrice[0] = self.boll.mid[0]
            #         self.l.PositionPercent[0] = 0.99




'''
计算均线密集
在最近period个周期内，有多少个bar符合均线密集条件
'''
class JXMJDayFsumIndicator(BaseApplyN):
    # alias = ('PctRankAbs',)
    lines = ('JXMJFsum',)
    params = (
        ('period', 21),
        ('func', lambda d: fsum((x < 5) for x in d)),
    )

