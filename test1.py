from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])

# Import the backtrader platform
import backtrader as bt
import pymongo
import tushare as ts
from datetime import datetime
import pandas as pd
import QUANTAXIS as QA
import datetime
import pandas_market_calendars as mcal
from mt_com_func import *

# tushare 账户设置
from dateutil.relativedelta import relativedelta

from QUANTAXIS import QA_fetch_financial_report_adv
from dateutil.relativedelta import relativedelta

from tradedaysfiller import tradedaysfiller
from test_quick_start import TestStrategy
#
# ts.set_token('d79c15feb3718d16953d1524f8076a076a33f55efb9eafa0d5484310')
#
# pro = ts.pro_api()
#
# # pd全局设置
# pd.set_option('display.max_rows', 5000)
# pd.set_option('display.max_columns', 100)
# pd.set_option('display.width', 300)


def mt_select_stock(stock_list, date):
    # 获取PE、PB、市值
    df = mt_read_dailyBasic_from_JQData(stock_list, date, date)
    df_part1 = df[["code", "pe_ratio", "pb_ratio", "market_cap"]]
    df_part1.set_index('code', inplace=True)

    ''' 获取
    营业收入：单季度营业收入operatingRevenueSingle
    净利润增长率：netProfitGrowthRate
    投资回报率（ROIC）：rateOfReturnOnInvestmentIncome
    '''
    code_list = []
    for stock in stock_list:
        code_list.append(stock.split('.')[0])
    columns = ['operatingRevenueSingle', 'netProfitGrowthRate', 'rateOfReturnOnInvestmentIncome']
    date_tm = datetime.strptime(date, "%Y-%m-%d")
    last_quarter_final_day = date_tm - pd.tseries.offsets.QuarterEnd()
    res_adv = QA_fetch_financial_report_adv(
        code_list, (date_tm - relativedelta(years=1)), date_tm).get_key(code_list, last_quarter_final_day, columns)

    res_adv.reset_index(inplace=True)
    res_adv['code'] = res_adv['code'].apply(mt_add_suffix_name, args=(2,))
    res_adv.reset_index(inplace=True)
    res_adv.set_index('code', inplace=True)
    del res_adv['index']

    df_factor = df_part1.join(res_adv)
    df_factor.rename(columns={'operatingRevenueSingle': 'ors', 'netProfitGrowthRate': 'npgr',
                              'rateOfReturnOnInvestmentIncome': 'roic'}, inplace=True)

    '''
    根据factor，计算排名
    '''
    hold_list = mt_select_stocklist(df_factor, 10)
    return hold_list


class pandas_PB_PE(bt.feeds.PandasData):
    # Add a 'pe' line to the inherited ones from the base class
    lines = ('pe_ratio', 'pb_ratio',)

    # openinterest in GenericCSVData has index 7 ... add 1
    # add the parameter to the parameters inherited from the base class
    params = (('pe_ratio', 8), ('pb_ratio', 9),)


# Create a Stratey
class TestStrategy1(bt.Strategy):
    params = dict(
        when=bt.timer.SESSION_START,
        timer=True,
        cheat=False,
        offset=datetime.timedelta(),
        repeat=datetime.timedelta(),
        weekdays=[],
        monthdays=[1],

        maperiod=15,
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.getdatabyname("000001.SZ").datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):

        self.add_timer(
            when=self.p.when,
            offset=self.p.offset,
            repeat=self.p.repeat,
            weekdays=self.p.weekdays,
            monthdays=self.p.monthdays,
        )

        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

        # Add a MovingAverageSimple indicator
        self.sma = bt.indicators.SimpleMovingAverage(
            self.getdatabyname("000001.SZ"), period=self.params.maperiod)

        # self.sma1 = bt.indicators.SimpleMovingAverage(
        #     self.datas[1], period=self.params.maperiod)

        # bt.indicators.SimpleMovingAverage(
        #     self.datas[1], period=self.params.maperiod)

        # Indicators for the plotting show
        # bt.indicators.ExponentialMovingAverage(self.datas[0], period=25)
        # bt.indicators.WeightedMovingAverage(self.datas[0], period=25,
        #                                     subplot=True)
        # bt.indicators.StochasticSlow(self.datas[0])
        # bt.indicators.MACDHisto(self.datas[0])
        # rsi = bt.indicators.RSI(self.datas[0])
        # bt.indicators.SmoothedMovingAverage(rsi, period=10)
        # bt.indicators.ATR(self.datas[0], plot=False)

    def start(self):
        # Activate the fund mode and set the default value at 100
        self.broker.set_fundmode(fundmode=True, fundstartval=100.00)

        self.cash_start = self.broker.get_cash()
        self.val_start = 100.0

    def notify_timer(self, timer, when, *args, **kwargs):
        print('strategy notify_timer with tid {}, when {} cheat {}'.
              format(timer.p.tid, when, timer.p.cheat))
        print("current date is : ", when)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.getpositionbyname('000001.SZ'):
            # Not yet ... we MIGHT BUY if ...
            if self.dataclose[0] > self.sma[0]:
                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                # self.order = self.buy(data='000651.SZ')
                self.order_target_value(data=self.getdatabyname('000001.SZ'), target=self.broker.get_cash())

        else:
            if self.dataclose[0] < self.sma[0]:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                # self.order = self.sell(data='000651.SZ')
                self.order_target_value(data=self.getdatabyname('000001.SZ'), target=0)

    def stop(self):
        self.roi = (self.broker.get_value() / self.cash_start) - 1.0
        self.froi = self.broker.get_fundvalue() - self.val_start
        print('ROI:        {:.2f}%'.format(self.roi))
        print('Fund Value: {:.2f}%'.format(self.froi))




if __name__ == '__main__':

    # 获取交易日历
    #sse = mcal.get_calendar('SSE')

    # Create a cerebro entity
    # cerebro = bt.Cerebro()
    #
    # # Add a strategy
    # cerebro.addstrategy(TestStrategy)
    '''
    # Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath, '../../datas/orcl-1995-2014.txt')

    # Create a Data Feed
    data = bt.feeds.YahooFinanceCSVData(
        dataname=datapath,
        # Do not pass values before this date
        fromdate=datetime.datetime(2000, 1, 1),
        # Do not pass values before this date
        todate=datetime.datetime(2000, 12, 31),
        # Do not pass values after this date
        reverse=False)
        
    '''
    # dataframe = pro.index_daily(ts_code='399300.SZ')
    # dataframe = ts.pro_bar(ts_code='000651.SZ', adj='qfq', start_date='20100101', end_date='20200401')
    # dataframe['trade_date'] = dataframe['trade_date'].apply(lambda x: datetime.strptime(x, '%Y%m%d'))
    # dataframe.rename(columns={"trade_date": 'datetime', 'vol': 'volume'},inplace=True)
    # dataframe['openinterest'] = 0.0

    # stock_basic_df = mt_read_stock_basic("2000-01-01")
    # # stock_list = ['000001.SH','000001.SZ', '000002.SZ', '000651.SZ']
    # stock_list = []
    # stock_list.extend(stock_basic_df["ts_code"].to_list())
    # stock_list = stock_list[:1]
    #
    # stock_list = ['000001.SH']
    #
    # start_day = "2010-01-01"
    # end_day = "2019-11-11"

    # for stock in stock_list:
    #     print(stock)
    #     df_day = mt_read_stockDay_from_TuShare(stock, start_day, end_day, True)
    #     if len(df_day) == 0:
    #         print("current stock " + stock + "is empty in mongodb! ")
    #         continue
    #
    #     df_day['datetime'] = df_day['datetime'].apply(lambda x: x.strftime('%Y-%m-%d'))
    #     dataframe = df_day
    #     dataframe['openinterest'] = 0.0
    #     dataframe['datetime'] = dataframe['datetime'].apply(lambda x: datetime.datetime.strptime(x, '%Y-%m-%d'))
    #
    #     # Pass it to the backtrader datafeed and add it to the cerebro
    #     data = bt.feeds.PandasData(dataname=dataframe, fromdate=datetime.datetime(2012, 1, 1),
    #                                todate=datetime.datetime(2018, 12, 31), datetime='datetime', nocase=True, )
    #
    #     # 按照交易日历补齐数据
    #     # data.addfilter(tradedaysfiller, sse.valid_days(start_day, end_day), fillclose=True)
    #
    #     # if stock == '000001.SZ':
    #     #     benchmark = data
    #
    #     # Add the Data Feed to Cerebro
    #     cerebro.adddata(data, stock)

    #
    #
    # # Set our desired cash start
    # cerebro.broker.setcash(70000.0)
    #
    # # Add a FixedSize sizer according to the stake
    # cerebro.addsizer(bt.sizers.FixedSize, stake=10)
    #
    # # cerebro.addobserver(bt.observers.Benchmark, data=benchmark, timeframe=bt.TimeFrame.NoTimeFrame)
    # # cerebro.addanalyzer(bt.analyzers.TimeReturn, timeframe=bt.TimeFrame.Years)
    #
    # # Set the commission
    # cerebro.broker.setcommission(commission=0.0)
    #
    # # Print out the starting conditions
    # print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    #
    # # Run over everything
    # result = cerebro.run()
    #
    # # Print out the final result
    # print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    #
    # # print(result[0].analyzers.getbyname('timereturn').get_analysis())
    #
    # # Plot the result
    # cerebro.plot()


    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(TestStrategy)

    # Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath, './datas/orcl-1995-2014.txt')

    # Create a Data Feed
    data = bt.feeds.YahooFinanceCSVData(
        dataname=datapath,
        # Do not pass values before this date
        fromdate=datetime.datetime(2000, 1, 1),
        # Do not pass values before this date
        todate=datetime.datetime(2000, 12, 31),
        # Do not pass values after this date
        reverse=False)

    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(1000.0)

    # Add a FixedSize sizer according to the stake
    cerebro.addsizer(bt.sizers.FixedSize, stake=10)

    # Set the commission
    cerebro.broker.setcommission(commission=0.0)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Plot the result
    cerebro.plot()
