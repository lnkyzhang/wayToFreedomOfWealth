import talib
from rqalpha.__main__ import entry_point
from rqalpha.api import *

import sys
sys.path.append("..")
from MT_func import *
import QUANTAXIS as QA

# 在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递。

'''
xshe:深证
xshg:上证
1.context中保存的东西，需要在每个周期清零。否则别用context这个全局的保存。容易造成不好解决的bug
'''

def init(context):

    context.res_adv = {}
    context.factor_data = pd.DataFrame()
    context.stock_counts = 20
    context.multi_stock_daily = None
    context.multi_stock_daily_qfq = None

    context.code_list = []
    context.code_list_last = []

    context.start_date = context.run_info.start_date
    context.end_date = context.run_info.end_date

    context.pre_start = pd.to_datetime(context.start_date, format='%Y-%m-%d')
    context.pre_start = context.pre_start - datetime.timedelta(days=365)

    # scheduler.run_monthly(handle_monthly, tradingday=1)


# 你选择的证券的数据更新将会触发此段逻辑，例如日或分钟历史数据切片或者是实时数据切片更新
def handle_bar(context, bar_dict):
    print(bar_dict['000651.XSHE'])
    order_percent('000651.XSHE', 1)

    print(context.portfolio.positions['000651.XSHE'])
    # pass

def handle_monthly(context,bar_dict):

    str_time_now = context.now.strftime("%Y-%m-%d")
    print("Runing time is :", str_time_now)
    trade_date = get_previous_trading_date(date=str_time_now)

    if len(context.code_list) == 0:
        context.code_list = get_index_code('399300.SZ', '2019-10-26')
    '''
    if set(context.code_list) == set(context.code_list_last):
        print("same code list")
    else:
        context.code_list_last = context.code_list
        context.multi_stock_daily = QA.QA_fetch_stock_day_adv(context.code_list, context.pre_start, context.end_date)
        context.res_adv = QA.QA_fetch_financial_report_adv(context.code_list, context.pre_start, context.end_date)

    stock_day = context.multi_stock_daily

    context.factor_data = pd.DataFrame()

    context.factor_data['pe'] = stock_data_add_ind(func_map_pe, trade_date, stock_day, context.res_adv)
    context.factor_data['pb'] = stock_data_add_ind(func_map_pb, trade_date, stock_day, context.res_adv)
    context.factor_data['marketcap'] = stock_data_add_ind(func_map_marketcap, trade_date, stock_day, context.res_adv)
    context.factor_data['roic'] = stock_data_add_ind(func_map_ROIC, trade_date, stock_day, context.res_adv)
    context.factor_data['npgr'] = stock_data_add_ind(func_map_NPGR, trade_date, stock_day, context.res_adv)
    context.factor_data['ors'] = stock_data_add_ind(func_map_ORS, trade_date, stock_day, context.res_adv)

    hold_list = select_stocklist(context.factor_data, context.stock_counts)
    '''

    df = pd.read_csv("holdlistQA.csv", header=None)
    df = df.drop_duplicates()
    df.columns = df.iloc[0, :]
    df = df.drop(0)
    df = df.reset_index(drop=True).set_index('date')
    hold_list = df.loc[str(trade_date)[:10]].to_list()
    hold_list = QA_util_code_tolist(hold_list)

    tem_df = pd.DataFrame([hold_list])
    tem_df["date"] = str(trade_date)[:10]
    tem_df.reset_index(drop=True).set_index('date').to_csv('holdlist.csv',mode='a')



    hold_list = add_suffix_name(hold_list)

    total_assert = context.portfolio.total_value
    # total_assert = cal_market_value(self.acc.positions) + self.acc.cash_available

    last_month_hold_list = list(context.portfolio.positions.keys())

    sell_list = set(last_month_hold_list).difference(set(hold_list))
    rebalance_list = set(last_month_hold_list).intersection(set(hold_list))
    buy_list = set(hold_list).difference(set(last_month_hold_list))

    print("sell_list : ", sell_list)
    print("rebalance_list : ", rebalance_list)
    print("buy_list : ", buy_list)

    # 1.卖出当月不在hold_list的持仓
    for code in sell_list:
        order_shares(code, -context.portfolio.positions[code].quantity)

    # 2.调整持仓
    for code in rebalance_list:
        ought_to_value = context.portfolio.total_value / context.stock_counts
        # order_value(code,ought_to_value - context.portfolio.positions[code].market_value)
        order_target_value(code, ought_to_value)

    # 3.买入新出现在hold_list的股票
    remain_cash = context.portfolio.cash
    for code in buy_list:
        print("code_name :", code)
        # order_value(code, remain_cash / len(buy_list))
        order_target_value(code,remain_cash / len(buy_list))

if __name__ == '__main__':

    time_start = datetime.datetime.now()
    entry_point()
    print("=============")
    time_end = datetime.datetime.now()
    print("total time :", (time_end - time_start).microseconds)