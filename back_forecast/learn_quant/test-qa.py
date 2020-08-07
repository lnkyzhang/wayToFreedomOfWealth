from QAStrategy import QAStrategyCTABase
from QAStrategy.qastockbase import QAStrategyStockBase
import QUANTAXIS as QA
import matplotlib.pyplot as plt
import pandas as pd
from QUANTAXIS import QA_Risk

from MT_func import *
import datetime

import profile


'''
1.position 中的 position_profit_long 是根据last_price计算的，而last_price又是用户在send_order中传入的。
2.输出不了图，就包图保存到本地
3.risk中计算的是前复权的market_value
'''


# pd全局设置
pd.set_option('display.max_rows', 5000)
pd.set_option('display.max_columns', 100)
pd.set_option('display.width', 300)

class Strategy(QAStrategyStockBase):
    stock_list = []
    res_adv = {}
    factor_data = pd.DataFrame()
    stock_counts = 20
    multi_stock_daily = None
    multi_stock_daily_qfq = None

    code_list = []
    code_list_last = []

    pre_start = None

    def user_init(self):
        # 初始化当前账户

        self.pre_start = pd.to_datetime(self.start, format='%Y-%m-%d')
        self.pre_start = self.pre_start - datetime.timedelta(days=365)

        # self.multi_stock_daily = QA.QA_fetch_stock_day_adv(self.code, pre_start, self.end)

        # self.res_adv = QA.QA_fetch_financial_report_adv(self.code, pre_start, self.end)

        self.code_list = get_index_code('399300.SZ', '2019-10-26')





    def on_bar(self, bar):
        pass
    #     print("==============",self.running_time,"=================")
    #     try:
    #         signal = self.macd().iloc[-1]['MACD']
    #         if signal > 0.0:
    #             print("Buy order!")
    #
    #             # print(self.acc.hold.index)
    #             # print("acc.hold is :",self.acc.hold)
    #             # print(self.market_data["close"])
    #             # print("price is : ",bar["close"])
    #
    #             if self.acc.cash_available > bar["close"] * 200:
    #                 buy_volume = int(self.acc.cash_available / bar["close"] / 100 / 2) * 100
    #             else:
    #                 buy_volume = 100
    #
    #             self.send_order('BUY', 'OPEN',code=bar.name[1], price=bar['close'], volume=buy_volume)
    #
    #         elif signal <= 0.0:
    #             print("Send order!")
    #
    #             self.send_order('SELL', 'CLOSE', code=bar.name[1], price=bar['close'], volume=10)
    #         else:
    #             pass
    #     except:
    #         pass
    #
    # def macd(self,):
    #     # print(QA.QA_indicator_MACD(self.market_data, 12, 26, 9))
    #     return QA.QA_indicator_MACD(self.market_data, 12, 26, 9)




    def on_month_1st_day(self):
        print("Runing time is :",self.running_time)
        trade_date = datetime.datetime.strptime(self.running_time[0:10], '%Y-%m-%d')


        if set(self.code_list) == set(self.code_list_last):
            print("same code list")
        else:
            self.code_list_last = self.code_list
            self.multi_stock_daily = QA.QA_fetch_stock_day_adv(self.code_list, self.pre_start, self.end)
            self.res_adv = QA.QA_fetch_financial_report_adv(self.code_list, self.pre_start,
                                                            self.end)
        #
        # stock_day = self.multi_stock_daily
        #
        # self.factor_data['pe'] = stock_data_add_ind(func_map_pe, trade_date, stock_day,self.res_adv)
        # self.factor_data['pb'] = stock_data_add_ind(func_map_pb, trade_date, stock_day,self.res_adv)
        # self.factor_data['marketcap'] = stock_data_add_ind(func_map_marketcap, trade_date, stock_day,self.res_adv)
        # self.factor_data['roic'] = stock_data_add_ind(func_map_ROIC, trade_date, stock_day,self.res_adv)
        # self.factor_data['npgr'] = stock_data_add_ind(func_map_NPGR, trade_date, stock_day,self.res_adv)
        # self.factor_data['ors'] = stock_data_add_ind(func_map_ORS, trade_date, stock_day,self.res_adv)
        #
        # hold_list = select_stocklist(self.factor_data,self.stock_counts)
        #
        #
        #
        # tem_df = pd.DataFrame([hold_list])
        # tem_df["date"] = str(self.running_time)[:10]
        # tem_df.reset_index(drop=True).set_index('date').to_csv('holdlist.csv', mode='a')

        df = pd.read_csv("holdlistQA.csv", header=None)
        df = df.drop_duplicates()
        df.columns = df.iloc[0, :]
        df = df.drop(0)
        df = df.reset_index(drop=True).set_index('date')
        hold_list = df.loc[str(trade_date)[:10]].to_list()
        hold_list = QA_util_code_tolist(hold_list)


        total_assert = cal_market_value(self.acc.positions) + self.acc.cash_available

        last_month_hold_list = self.acc.hold_available.index.tolist()
        sell_list = set(last_month_hold_list).difference(set(hold_list))
        rebalance_list = set(last_month_hold_list).intersection(set(hold_list))
        buy_list = set(hold_list).difference(set(last_month_hold_list))

        print("sell_list : ",sell_list)
        print("rebalance_list : ", rebalance_list)
        print("buy_list : ", buy_list)

        # 1.卖出当月不在hold_list的持仓
        for code in sell_list:
            close_price = self.get_qfq_Close(str(self.running_time)[0:10], code, self.multi_stock_daily)
            if close_price is not None:
                self.send_order('SELL', 'CLOSE', code=code, price=(close_price), volume=int(self.acc.hold_available[code]))

        # 2.调整持仓
        for code in rebalance_list:
            # 计算期望的仓位
            close_price = self.get_qfq_Close(str(self.running_time)[0:10], code,self.multi_stock_daily)
            if close_price is not None:

                ought_to_volume = cal_buy_volume(total_assert / self.stock_counts, self.acc.commission_coeff, close_price)
                ought_to_volume = int(ought_to_volume / 100) * 100

                if ought_to_volume == self.acc.positions[code].volume_long:
                    continue
                elif ought_to_volume > self.acc.positions[code].volume_long:
                    buy_amount = ought_to_volume - self.acc.positions[code].volume_long
                    self.send_order('BUY', 'OPEN', code=code, price=(close_price), volume=int(buy_amount))
                else:
                    sell_amount = self.acc.positions[code].volume_long - ought_to_volume
                    self.send_order('SELL', 'CLOSE', code=code, price=(close_price), volume=int(sell_amount))


        # 3.买入新出现在hold_list的股票
        remain_cash = self.acc.cash_available
        for code in buy_list:
            close_price = self.get_qfq_Close(str(self.running_time)[0:10], code, self.multi_stock_daily)
            if close_price is not None:
                buy_amount = cal_buy_volume(remain_cash / len(buy_list),self.acc.commission_coeff,close_price)
                print("BUY NEW   money : %s ,code : %s , buy amount :%s ， price : %s"%(remain_cash / len(buy_list),code,buy_amount,close_price))

                self.send_order('BUY', 'OPEN', code=code, price=(close_price), volume=int(buy_amount))


        print("hold_avilable :",self.acc.hold_available)
        print("hold_counts :", len(self.acc.hold_available))
        print("cash :", self.acc.cash_available)
        print("assert :",self.acc.cash_available + cal_market_value(self.acc.positions))

    def on_dailyopen(self):
        pass


    def get_qfq_Close(self,date,code,daily_data):
        '''
        1.验证是否停牌
        2.获取某只股票前复权的收盘数据
        @param daily_data: 获取到的所有股票的日线数据
        @param date: 日期
        @param code: 股票代码
        @return: 如果停牌返回null，否则返回前复权数据
        '''
        if self.multi_stock_daily_qfq is None:
            self.multi_stock_daily_qfq = daily_data
            # pass

        code_data = self.multi_stock_daily_qfq.data.xs((date, code), level=[0, 1])
        if code_data.empty:
            print("停牌 日期:%s 股票:%s " % (code,date))
            return None
        else:
            return code_data['close'][0]






if __name__ == '__main__':

    data = QA.QA_fetch_stock_list_adv()
    stock_list = list(data['code'])
    # stock_list = ['000001','000002','000004']
    stock_list = stock_list[0:100]
    # stock_list = ['000001','000651']
    # stock_list = get_index_code("399300.SZ","2019-10-26")

    start = '2010-01-01'
    # start = '2018-01-01'
    # start = '2016-01-01'
    end = '2019-09-09'

    time_start = datetime.datetime.now()

    s = Strategy(code=stock_list, frequence='day', strategy_id= 'xxx4', start=start, end=end,portfolio="x765")

    # 如果需要自动保存account数据，需要在初始化account时候，参数auto_load指定为false，否则会读取上次的history
    s.debug()

    time_end = datetime.datetime.now()

    print("total time :" ,(time_end - time_start).microseconds)


    risk = QA_Risk(s.acc)
    risk.save()
    plt_curve = risk.plot_assets_curve()

    plt_curve.savefig('temp.png')

    print(risk.assets)
    print(risk.message)

    # print(risk.market_value)
    #
    # print(risk.market_value.sum(axis=1))
    # print(risk.account.daily_cash)

    print("====================")

    print(s.acc.cash)
    print(s.acc.positions)
    print(cal_market_value(s.acc.positions))

    print(result_analysis_stock_profit(s.acc.positions))


    print("====================")