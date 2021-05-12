import backtrader as bt



class MacdDivergenceSt(bt.Strategy):
    params = dict(
        atrperiod=14,  # measure volatility over x days
        emaperiod=10,  # smooth out period for atr volatility
        stopfactor=18.0,  # actual stop distance for smoothed atr
        verbose=True,  # print out debug info
        samebar=True,  # close and re-open on samebar
    )

    def __init__(self):


        self.order = None
        self.entering = None
        self.stop_large = True

        self.macdDivergence = MACDEMAEntryPoint(self.data0, continueDivergence=True)
        self.macdDivergence = MACDEMAEntryPoint(self.data1)
        self.macdDivergence = MACDEMAEntryPoint(self.data2)
        self.macdDivergence = MACDEMAEntryPoint(self.data3)

        # self.stoptrailer = st = StopTrailer(atrperiod=14,
        #                                     emaperiod=10,
        #                                     stopfactor=100)

        # self.exit_long = bt.ind.CrossDown(self.data,
        #                                   self.stoptrailer.stop_long, plotname='Exit Long')

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