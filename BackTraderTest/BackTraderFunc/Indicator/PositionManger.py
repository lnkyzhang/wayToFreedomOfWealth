import backtrader as bt

'''
布林带仓位管理
'''
class BollPositionManager(bt.Indicator):

    lines = ('PositionPercent', )
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

    lines = ('PositionPercent', 'OrderPrice', 'sma20Slope', 'ema20Slope', 'macd','macdsignal', 'macdhist')
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

        self.macd = bt.ind.MACDHisto(self.data, period_me1=20,period_me2=60,period_signal=9)
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
        if self.strat.position.size > 0 :
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

    lines = ('PositionPercent', 'OrderPrice', 'sma20Slope', 'ema20Slope', 'macd','macdsignal', 'macdhist')
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

        self.macd = bt.ind.MACDHisto(self.data, period_me1=20,period_me2=60,period_signal=9)
        self.l.macd = self.macd.macd
        self.l.macdsignal = self.macd.signal
        self.l.macdhist = self.macd.histo

        self.pctRank = bt.ind.PercentRank(self.l.macdsignal, period=200)
        # self.macdhistSlope = bt.talib.LINEARREG_SLOPE(self.l.macdhist, timeperiod=2)

    def next(self):
        '''
        卖出：20日EMA或20日SMA任一个拐头向下
        买入：20日EMA或20日SMA全部拐头向上
        '''
        # if self.pctRank[0] > 0.95:
        #     print("date %s, pctRank %f, diff :%f", self.data.datetime.date(0).isoformat(), self.pctRank[0], self.l.macdsignal[0])

        if self.data.datetime.date(0).isoformat() < '2015-04-17':
            return

        if self.data.datetime.date(0).isoformat() == '2017-07-21':
            print("123123")
        if self.data.datetime.date(0).isoformat() == '2018-01-30':
            print("123123")
        if self.strat.position.size > 0 :
            if self.l.macdsignal[0] < 0:
                # todo 这个位置还需要继续衡量
                if self.l.macdhist[0] < self.l.macdhist[-1] - 0.025:
                    self.l.OrderPrice[0] = max(self.ema20[0], self.data[-19])
                    self.l.PositionPercent[0] = 0
            elif self.l.macdsignal[0] > 0 and self.pctRank[0] < 0.99:
                pass
            elif self.pctRank[0] > 0.99:
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




