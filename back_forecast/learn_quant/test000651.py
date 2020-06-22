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

    hasSell = False
    hasBuy = False

    def user_init(self):
        pass


    def on_bar(self, bar):
        # pass
        print("==============",self.running_time,"=================")

        if str(self.running_time)[:10] == "2019-09-09":
            print("over Sell order!")
            self.send_order('SELL', 'CLOSE', code=bar.name[1], price=bar['close'], volume=1)


        try:
            signal = self.macd().iloc[-1]['MACD']
            if self.hasBuy is False:
                print("Buy order!")
                print("cash_available:",self.acc.cash_available)

                # print(self.acc.hold.index)
                # print("acc.hold is :",self.acc.hold)
                # print(self.market_data["close"])
                # print("price is : ",bar["close"])

                if self.acc.cash_available > bar["close"] * 200:
                    buy_volume = int(self.acc.cash_available / bar["close"] / 100 ) * 100

                    self.send_order('BUY', 'OPEN',code=bar.name[1], price=bar['close'], volume=buy_volume)
                    self.acc.settle()
                    self.hasBuy = True
                    print("buy_volumes:",buy_volume)
                    print("market_value :",cal_market_value(self.acc.positions))

            elif signal <= 0.0 :
                print("Sell order!")
                self.send_order('SELL', 'CLOSE', code=bar.name[1], price=bar['close'], volume=0)
                self.hasSell = True

            else:
                pass
        except:
            pass

    def macd(self,):
        # print(QA.QA_indicator_MACD(self.market_data, 12, 26, 9))
        return QA.QA_indicator_MACD(self.market_data, 12, 26, 9)




    def on_month_1st_day(self):
        pass



    def on_dailyopen(self):
        pass




if __name__ == '__main__':

    stock_list = ['000651']

    start = '2015-01-01'
    end = '2019-09-09'

    time_start = datetime.datetime.now()

    data = QA.QA_fetch_stock_day_adv('000651','2015-01-01','2019-09-09').to_qfq()
    print(data.data)

    s = Strategy(code=stock_list, frequence='day', strategy_id= 'xxx4', start=start, end=end,portfolio="x668")

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

    print("====================")

    print(s.acc.cash)
    print(s.acc.positions)
    print(cal_market_value(s.acc.positions))

    print(result_analysis_stock_profit(s.acc.positions))

    print("====================")