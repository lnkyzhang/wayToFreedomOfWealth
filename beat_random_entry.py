#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
# Copyright (C) 2019 Daniel Rodriguez - MIT License
#  - https://opensource.org/licenses/MIT
#  - https://en.wikipedia.org/wiki/MIT_License
###############################################################################
import argparse
import random

import pandas as pd

import backtrader as bt
from backtrader.analyzers import (SQN, AnnualReturn, TimeReturn, SharpeRatio,
                                  TradeAnalyzer)


def read_dataframe(filename, years):
    colnames = ['ticker', 'period', 'date', 'time',
                'open', 'high', 'low', 'close', 'volume', 'openinterest']

    colsused = ['date',
                'open', 'high', 'low', 'close', 'volume', 'openinterest']

    df = pd.read_csv(filename,
                     skiprows=1,  # using own column names, skip header
                     names=colsused,
                     usecols=colsused,
                     parse_dates=['date'],
                     index_col='date')

    if years:  # year or year range specified
        ysplit = years.split('-')

        # left side limit
        mask = df.index >= ((ysplit[0] or '0001') + '-01-01')  # support -YYYY

        # right side liit
        if len(ysplit) > 1:  # multiple or open ended (YYYY-ZZZZ or YYYY-)
            if ysplit[1]:  # open ended if not years[1] (YYYY- format)
                mask &= df.index <= (ysplit[1] + '-12-31')
        else:  # single year specified YYYY
            mask &= df.index <= (ysplit[0] + '-12-31')

        df = df.loc[mask]  # select the given date range

    return df


# DEFAULTS - CAN BE CHANGED VIA COMMAND LINE OPTIONS
COMMINFO_DEFAULT = dict(
    stocklike=False,  # Futures-like
    commtype=bt.CommissionInfo.COMM_FIXED,  # fixed price per asset
    commission=2.0,  # Standard IB Price for futures
    mult=1000.0,  # multiplier
    margin=2000.0,  # $50 x 50 => $2500
)


class PercentRiskSizer(bt.Sizer):
    '''Sizer modeling the Percentage Risk sizing model of Van K. Tharp'''
    params = dict(percrisk=0.01)  # 1% percentage risk

    def _getsizing(self, comminfo, cash, data, isbuy):
        # Risk per 1 contract
        risk = comminfo.p.mult * self.strategy.stoptrailer.stop_dist[0]
        # % of account value to risk
        torisk = self.broker.get_value() * self.p.percrisk
        return torisk // risk  # size to risk


class CoinFlip(bt.Indicator):
    lines = ('coinflip',)
    HEAD, TAIL = 1, 0

    def next(self):
        self.l.coinflip[0] = 0.5  # midway
        pass

    def flip(self):
        # self.l.coinflip[0] = cf = random.randrage(-1, 2, 2)  # -1 or 1
        self.l.coinflip[0] = cf = random.randint(0, 1)
        return cf

    def head(self, val=None):
        if val is None:
            return self.lines[0] == self.HEAD

        return val == self.HEAD


class StopTrailer(bt.Indicator):
    _nextforce = True  # force system into step by step calcs

    lines = ('stop_long', 'stop_short',)
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
        self.s_s = self.data + self.stop_dist

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


class St1(bt.Strategy):
    SHORT, NONE, LONG = -1, 0, 1

    params = dict(
        atrperiod=14,  # measure volatility over x days
        emaperiod=10,  # smooth out period for atr volatility
        stopfactor=3.0,  # actual stop distance for smoothed atr
        verbose=True,  # print out debug info
        samebar=True,  # close and re-open on samebar
    )

    def __init__(self):
        self.coinflip = CoinFlip()

        # Trailing Stop Indicator
        self.stoptrailer = st = StopTrailer(atrperiod=self.p.atrperiod,
                                            emaperiod=self.p.emaperiod,
                                            stopfactor=self.p.stopfactor)

        # Exit Criteria (Stop Trail) for long / short positions
        self.exit_long = bt.ind.CrossDown(self.data,
                                          st.stop_long, plotname='Exit Long')
        self.exit_short = bt.ind.CrossUp(self.data,
                                         st.stop_short, plotname='Exit Short')

        self.entering = None

    def start(self):
        self.entering = 0
        self.start_val = self.broker.get_value()

    def stop(self):
        self.stop_val = self.broker.get_value()
        self.pnl_val = self.stop_val - self.start_val
        self.log('Start Value: {:.2f}', self.start_val)
        self.log('Final Value: {:.2f}', self.stop_val)
        self.log('PNL   Value: {:.2f}', self.pnl_val)

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

        self.entering = None

    def next(self):
        self.logdata()
        # Check if an order is pending ... if yes, we cannot send a 2nd one
        print("self.broker.getvalue : ", self.broker.get_value())
        print("self.broker.getcash : ", self.broker.get_cash())
        if self.entering:
            return

        # logic
        closing = None
        if self.position.size > 0:  # In the market - Long
            self.log('Long Stop Price: {:.2f}', self.stoptrailer.stop_long[0])
            if self.exit_long:
                closing = self.close()

        elif self.position.size < 0:  # In the market - Short
            self.log('Short Stop Price {:.2f}', self.stoptrailer.stop_short[0])
            if self.exit_short:
                closing = self.close()

        self.entering = self.NONE
        if not self.position or (closing and self.p.samebar):
            # Not in the market or closing pos and reenter in samebar
            if self.coinflip.flip():
                self.entering = self.LONG if self.buy() else self.NONE
                #self.entering = self.order_target_percent(target=1)
            else:
                self.entering = self.LONG if self.buy() else self.NONE
                #self.entering = self.order_target_percent(target=1)
                # self.entering = self.SHORT if self.sell() else self.NONE

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


def runstrat(args):
    cerebro = bt.Cerebro()

    # Data feed kwargs
    dataargs = dict(dataname=read_dataframe(args.data, args.years))
    dataargs.update(eval('dict(' + args.dargs + ')'))
    cerebro.adddata(bt.feeds.PandasData(**dataargs))

    # Strategy
    cerebro.addstrategy(St1, **eval('dict(' + args.strat + ')'))

    # Broker
    brokerargs = dict(cash=args.cash)
    brokerargs.update(eval('dict(' + args.broker + ')'))
    cerebro.broker = bt.brokers.BackBroker(**brokerargs)

    # Commission
    commargs = COMMINFO_DEFAULT
    commargs.update(eval('dict(' + args.commission + ')'))
    cerebro.broker.setcommission(**commargs)

    # Sizer
    szcls = PercentRiskSizer if args.percrisk else bt.sizers.FixedSize
    cerebro.addsizer(szcls, **(eval('dict(' + args.sizer + ')')))

    # Analyze the trades
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')

    cerebro.addanalyzer(TimeReturn, timeframe=bt.TimeFrame.Years, _name='timeReturn')
    cerebro.addanalyzer(SharpeRatio, timeframe=bt.TimeFrame.Years, _name='sharpRatio')

    # Execute
    strats = cerebro.run(**eval('dict(' + args.cerebro + ')'))

    if args.plot:  # Plot if requested to
        cerebro.plot(**eval('dict(' + args.plot + ')'))

    return strats[0]


def run(args=None):
    args = parse_args(args)

    results = []
    sum_won_trades = 0
    sum_total_trades = 0

    for i in range(0, args.iterations):
        strat = runstrat(args)
        pnl = strat.pnl_val
        results.append(pnl)
        trades = strat.analyzers.trades.get_analysis()

        timeReturn = strat.analyzers.timeReturn.get_analysis()
        sharpRatio = strat.analyzers.sharpRatio.get_analysis()

        print('**** Iteration: {:4d}'.format(i + 1))
        print('-- PNL: {:.2f}'.format(pnl))
        total_trades = trades.total.closed
        total_won = trades.won.total
        perc_won = total_won / total_trades
        print('--   Trades {} - Won {} - %_Won: {:.2f}'.format(
            total_trades, total_won, perc_won))

        print('timeReturn: ', timeReturn)
        print('sharpRatio: ', sharpRatio)

        sum_won_trades += total_won
        sum_total_trades += total_trades

    total = len(results)
    won = sum(1 for x in results if x > 0)
    print('**** Summary of Runs')
    print('-- Total       : {:8d}'.format(total))
    print('-- Won         : {:8d}'.format(won))
    print('-- % Won       : {:.2f}'.format(won / total))

    perc_won = sum_won_trades / sum_total_trades
    print('**** Summary of Trades')
    print('-- Total       : {:8d}'.format(sum_total_trades))
    print('-- Total Won   : {:8d}'.format(sum_won_trades))
    print('-- % Total Won : {:.2f}'.format(perc_won))

    print("pnl avg : ", sum(results) / len(results))

    if args.scatter:
        import numpy as np
        import matplotlib.pyplot as plt
        x = np.linspace(min(results), max(results), num=len(results))
        y = np.asarray(results)
        plt.scatter(x, y)
        plt.show()


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Van K. Tharp/Basso Random Entry Scenario',
    )

    parser.add_argument('--iterations', default=1, type=int,
                        help='Number of iterations to run the system')

    pgroup = parser.add_argument_group(title='Data Options')
    pgroup.add_argument('--data', default='shindex.csv',
                        help='Data to read in')

    pgroup.add_argument('--years', default='',
                        help='Formats: YYYY-ZZZZ / YYYY / YYYY- / -ZZZZ')

    parser.add_argument('--dargs', required=False, default='',
                        metavar='kwargs', help='kwargs in key=value format')

    pgroup = parser.add_argument_group(title='Cerebro Arguments')
    pgroup.add_argument('--cerebro', default='', metavar='kwargs',
                        help='Cerebro kwargs in key=value format')

    pgroup = parser.add_argument_group(title='Commission Arguments')
    pgroup.add_argument('--commission', default=str(COMMINFO_DEFAULT),
                        metavar='kwargs',
                        help='CommInfo kwargs in key=value format')

    pgroup = parser.add_argument_group(title='Broker Arguments')
    pgroup.add_argument('--broker', default='', metavar='kwargs',
                        help='Broker kwargs in key=value format')

    pgroup.add_argument('--cash', default=1000000.0, type=float,
                        help='Default cash')

    pgroup = parser.add_argument_group(title='Strategy Arguments')
    pgroup.add_argument('--strat', default='', metavar='kwargs',
                        help='Strategy kwargs in key=value format')

    pgroup = parser.add_argument_group(title='Sizer Options')
    pgroup.add_argument('--sizer', default='', metavar='kwargs',
                        help='Sizer kwargs in key=value format')

    pgroup = pgroup.add_mutually_exclusive_group()
    pgroup.add_argument('--percrisk', action='store_true',
                        help='Use Percrisk Sizer')

    pgroup.add_argument('--fixedsize', action='store_true',
                        help='Use Fixed Statke Sizer')

    pgroup = parser.add_argument_group(title='Plotting Options')
    pgroup.add_argument('--plot', default='', nargs='?', const='{}',
                        metavar='kwargs', help='kwargs in key=value format')

    pgroup.add_argument('--scatter', action='store_true',
                        help='Plot a scatter diagram of PNL results')

    return parser.parse_args(pargs)


if __name__ == '__main__':
    run()