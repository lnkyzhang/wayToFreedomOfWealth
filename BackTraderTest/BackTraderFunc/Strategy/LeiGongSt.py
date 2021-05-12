import backtrader as bt


from BackTraderTest.BackTraderFunc.Indicator.JXMJInd import JXMJIndicator
from BackTraderTest.BackTraderFunc.Indicator.PositionManger import MACDBiasPositionManager

from BackTraderTest.BackTraderFunc.Indicator.StopTrailer import StopTrailer


class LeiGoneSt(bt.Strategy):
    params = dict(
        atrperiod=14,  # measure volatility over x days
        emaperiod=10,  # smooth out period for atr volatility
        stopfactor=18.0,  # actual stop distance for smoothed atr
        verbose=True,  # print out debug info
        samebar=True,  # close and re-open on samebar
    )

    def __init__(self):

        # self.peaks = PeaksInd()

        # 布林带测试
        # self.bollPosition = BollPositionManager(self.data)
        # self.bollPosition = SMAPositionManager(self.data2)
        # self.bollPosition = SMAPositionManager(self.data)
        # self.bollPosition = MACDSMAPositionManager(self.data)
        # self.macdBiasPosition60min = MACDBiasPositionManager(self.data)
        # self.macdBiasPosition60min = MACDBiasPositionManager(self.data, name='15min')
        self.macdBiasPositionDay = MACDBiasPositionManager(self.data3,  name='day')
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
        # self.sma60min60 = bt.talib.SMA(self.data1, timeperiod=60)1
        # self.ema120min60 = bt.talib.EMA(self.data1, timeperiod=120)
        # self.sma120min60 = bt.talib.SMA(self.data1, timeperiod=120)

        #self.ema20day = bt.talib.EMA(self.data, timeperiod=20)
        self.sma20day = bt.talib.SMA(self.data3, timeperiod=20)
        #self.ema60day = bt.talib.EMA(self.data, timeperiod=60)
        self.sma60day = bt.talib.SMA(self.data3, timeperiod=60)
        #self.ema120day = bt.talib.EMA(self.data, timeperiod=120)
        self.sma120day = bt.talib.SMA(self.data3, timeperiod=120)


        self.JXMJIndicator = JXMJIndicator(self.data3)

        # self.divergences = MACDEMAEntryPoint(self.data)
        # self.divergences1 = MACDEMAEntryPoint(self.data1)
        # self.divergences2 = MACDEMAEntryPoint(self.data2)



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

        self.macdDivergence = MACDEMAEntryPoint(self.data0, continueDivergence=True)
        self.macdDivergence = MACDEMAEntryPoint(self.data1)
        self.macdDivergence = MACDEMAEntryPoint(self.data2)
        self.macdDivergence = MACDEMAEntryPoint(self.data3)

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