import backtrader as bt

'''
常规跟踪止损
'''
class StopTrailer(bt.Indicator):
    _nextforce = True  # force system into step by step calcs

    lines = ('stop_long', )
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
        self.s_l = self.data - self.stop_dist

    def next(self):
        # When entering the market, the stop has to be set
        if self.strat.entering > 0:  # entering long
            self.l.stop_long[0] = self.s_l[0]
            # todo 策略的变量不应该在这里更改 self.strat.entering
            self.strat.entering = 0
        elif self.strat.entering < 0:  # entering short
            self.l.stop_short[0] = self.s_s[0]

        else:  # In the market, adjust stop only in the direction of the trade
            if self.strat.position.size > 0:
                self.l.stop_long[0] = max(self.s_l[0], self.l.stop_long[-1])


'''
动态止损
'''
class StopTrailerDynamic(bt.Indicator):
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