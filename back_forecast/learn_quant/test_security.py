'''
0.指标：
    营业收入：单季度营业收入operatingRevenueSingle
    净利润增长率：netProfitGrowthRate
    投资回报率（ROIC）：rateOfReturnOnInvestmentIncome
    市盈率-pe_ratio：价格/每股收益 EPS
    市净率-pb_ratio：价格/每股净资产 netAssetsPerShare
    市值： 价格*股本 totalCapital
1.totalCapital是总股本，总共有多少股票
2.pd.asfreq('M',method='ffill',how='end')  按月提取每月最后一天数据，以便按月回测
3.MultiIndex用xs来选取 pd.xs(['000001','2018-12-31'],level=[0,2])
4.Series的name属性，返回值就是index
5.对Dataframe的每一行进行计算，可以使用apply
6.datetime.date可以用来生成日期对象
7.object数据转换到时间数据 pd.to_datetime(trade_date_month['cal_date'], format='%Y%m%d')
8.to_period 是按日期统计数据
9.series重置索引为默认数字 reset_index(drop=True)。
10.通过日期来获取上一个季度的最后一天，可以通过 日期偏移量pd.tseries.offsets.QuarterEnd
11.MultiIndex获取索引可以通过 multi_stock_day.data.index.levels[0].date[0]

'''

import QUANTAXIS as QA
import numpy as np
import pandas as pd
import datetime
import tushare as ts

from QAStrategy import QAStrategyCTABase

# pd全局设置
pd.set_option('display.max_rows', 5000)
pd.set_option('display.max_columns', 100)
pd.set_option('display.width', 300)

# tushare 账户设置
ts.set_token('50c48ae25bd98b7480a1512e5fd326ed186f88130eeb1ce8df9bfdd2')
pro = ts.pro_api()

# 定义模拟用变量
# create account
user = QA.QA_User(username='lnkyzhang', password='lnkyzhang')
portfolio = user.new_portfolio('qatestportfolio')

Account = portfolio.new_account(account_cookie='security_stock', init_cash=1000000)
Broker = QA.QA_BacktestBroker()

data=QA.QA_fetch_stock_list_adv()
stock_list = list(data['code'])
# stock_list = ['000001','000002','000004']
stock_list = stock_list[0:100]

sort_up = ['market_cap', 'pe_ratio', 'pb_ratio']
stock_counts = 20
order_list = []

start = '2010-01-01'
end = '2019-11-22'
multi_stock_daily_data = QA.QA_fetch_stock_day_adv(stock_list,start,end).select_time_with_gap(start,5,"gt").pivot(['open', 'high', 'low', 'close', 'volume'])
print(multi_stock_daily_data)


print(stock_list)
res_adv = QA.QA_fetch_financial_report_adv(stock_list,'2009-12-31',end)


print(res_adv.data.loc[['2019-09-30','2019-06-30']][['operatingRevenue','operatingProfit','EPS']])

print("-------------------------------")
A = QA.QA_fetch_stock_day_adv('000669','2016-01-01',end='2018-07-17')
# print(A.data)

# print(res_adv.data['rateOfReturnOnInvestmentIncome'])

#
# print(type(res_adv.data['EPS']))

# print(multi_stock_daily_data.data['close'])
# print(multi_stock_daily_data.data['close'].index)
# print(res_adv.data['EPS'].loc["2017"])

# print(res_adv.data.loc[pd.date_range('2013-12-30', '2014-12-03')])



# d = multi_stock_daily_data.data['close'] / res_adv.data['EPS']
# print(d)
# a = d.xs(['000001','2018-12-31'],level=[0,2])
#
# print(a)
# b = multi_stock_daily_data.data.xs('000001',level=1).asfreq('Q',method='ffill',how='end')
# print(b)
# b.resample('M')

# print("===================")
# print(res_adv.data['totalCapital'])
# print(res_adv.data['listedAShares'])
# print(res_adv.data['netProfitsBelongToParentCompanyOwner'])
# print("===================jinglirun")
# print(res_adv.data['netProfit'])
#
# print("===================shaoshuquanyi")
# print(res_adv.data['minorityProfitAndLoss'])
# print("===================chufa")
# print(res_adv.data['netProfitsBelongToParentCompanyOwner']/res_adv.data['totalCapital'])
# print("===================eps")
# print(res_adv.data['EPS'])
#
# print("--------------------------")
#
# d = QA.QA_fetch_stock_day(stock_list,'2018-12-01','2019-11-22')
# print(pd.DataFrame(d))
# print(type(d))
print("++++++++++++++++++++++")


def func_map_pe(x,date):
    try:
        # date = datetime.datetime.strptime(date, '%Y-%m-%d')
        last_year_final_day = datetime.date(year=date.year - 1, month=12, day=31)
        result = x['close'] / res_adv.data['EPS'].xs(x.name, level=1).loc[last_year_final_day]
        return result
    except Exception :
        print('Exception')
        return 0


def func_map_pb(x,date):
    try:
        # date = datetime.datetime.strptime(date, '%Y-%m-%d')
        last_year_final_day = datetime.date(year=date.year - 1, month=12, day=31)
        result = x['close'] / res_adv.data['netAssetsPerShare'].xs(x.name, level=1).loc[last_year_final_day]
        return result
    except Exception:
        print('Exception')
        return 0


def func_map_marketcap(x,date):
    try:
        # date = datetime.datetime.strptime(date, '%Y-%m-%d')
        last_year_final_day = datetime.date(year=date.year - 1, month=12, day=31)
        result = x['close'] * res_adv.data['totalCapital'].xs(x.name, level=1).loc[last_year_final_day]
        return result
    except Exception:
        print('Exception')
        return 0


def func_map_ROIC(x,date):
    try:
        last_quarter_final_day = date - pd.tseries.offsets.QuarterEnd()
        result = res_adv.data['rateOfReturnOnInvestmentIncome'].xs(x.name, level=1).loc[last_quarter_final_day]
        return result
    except Exception:
        print('Exception')
        return 0


def func_map_NPGR(x,date):
    try:
        last_quarter_final_day = date - pd.tseries.offsets.QuarterEnd()
        result = res_adv.data['netProfitGrowthRate'].xs(x.name, level=1).loc[last_quarter_final_day]
        return result
    except Exception:
        print('Exception')
        return 0


def func_map_ORS(x,date):
    try:
        last_quarter_final_day = date - pd.tseries.offsets.QuarterEnd()
        result = res_adv.data['operatingRevenueSingle'].xs(x.name, level=1).loc[last_quarter_final_day]
        return result
    except Exception:
        print('Exception')
        return 0


def stock_data_add_ind(func,date,stock_day_data):

    if func is None:
        raise RuntimeError('func is None')
    if stock_day_data is None:
        raise RuntimeError('stock_day_data is None')
    if date is None:
        raise RuntimeError('date is None')
    return stock_day_data.data.xs(date,level=0).apply(func,axis=1,args=(date,))


# multi_stock_daily_data.data.to_csv('Result.csv')

def get_month_trade_date(start,end):
    # 从tushare获取交易日历
    stock_trade_date = pro.trade_cal(exchange='', start_date=start, end_date=end)
    stock_trade_date_month = stock_trade_date[stock_trade_date["is_open"] == 1]
    stock_trade_date_month['cal_date'] = stock_trade_date_month['cal_date'].apply(lambda x : pd.to_datetime(x, format='%Y%m%d'))
    stock_trade_date_month.index = stock_trade_date_month['cal_date']
    dfg = stock_trade_date_month.resample('M')
    business_end_day = dfg.apply({'cal_date': np.min})
    return business_end_day["cal_date"].reset_index(drop=True).tolist()


def select_stocklist(factors_data):
    """打分的具体步骤、返回股票池
    因子升序从小到大分10组，第几组为所在组得分
        市值-market_cap、市盈率-pe_ratio、市净率-pb_ratio
    因子降序从大到小分10组，第几组为所在组得分
        ROIC-return_on_invested_capital、inc_revenue-营业总收入 和inc_profit_before_tax-利润增长率
    """
    # 循环每个因子去处理
    for name in factors_data.columns:
        if name in sort_up:
            factor = factors_data.sort_values(by=name)[name]
        else:
            factor = factors_data.sort_values(by=name, ascending=False)[name]

        factor = pd.DataFrame(factor)
        factor[name + '_score'] = 0

        # 进行打分
        # 先求出每组数量，然后根据数量一次给出分数
        stock_groupnum = len(factors_data) // 10
        for i in range(10):
            if i == 9:
                factor.loc[(i + 1) * stock_groupnum:,name + '_score'] = i + 1
            factor.loc[i * stock_groupnum: (i + 1) * stock_groupnum,name + '_score'] = i + 1
        factors_data = pd.concat([factors_data, factor[name + '_score']], axis=1,sort=False)

    all_score = factors_data[
        ['marketcap_score', 'pe_score', 'pb_score', 'roic_score', 'ors_score',
         'npgr_score']].sum(1).sort_values()

    hold_list = all_score.index[:stock_counts].tolist()
    print(hold_list)
    return hold_list


def cal_account_market_value(hold_series,multi_stock_day):
    '''
    根据持仓计算给定的某天股票总市值
    :param hold_series: 持仓。index为stock_code，值为数量
    :param multi_stock_day:给定的某天股票价格
    :return:股票总市值
    '''
    market_value = 0
    # # 获取日期
    # date = multi_stock_day.data.index.levels[0].date[0]
    # # 获取当天停复牌信息
    # suspend_data = get_suspend_stock_info(date)

    for stock,counts in hold_series.items():
        try:
            market_value += multi_stock_day.select_code(stock).data['close'][0] * counts
        except:
            print('==========================================')
            print(multi_stock_day)
            market_value += 0

    return market_value


def get_suspend_stock_info(date):
    '''
    通过Tushare获取某天的停复牌信息
    :param date: 日期,datetime格式
    :return: 停复牌信息的Dataframe
    '''
    string_date = date.strftime('%Y%m%d')
    suspend_stock_info = pro.query('suspend', ts_code='', suspend_date=string_date, resume_date='', fields='')
    df = pro.query('daily', ts_code='000669.SZ', start_date='', end_date='20180718')

    return suspend_stock_info



def rebalance(hold_list,date,multi_stock_1day):
    """
    调仓函数
    卖出、买入
    """
    capture = cal_account_market_value(Account.hold,multi_stock_1day) + Account.cash_available

    # 卖出。不在新选的股票列表全部卖出，股票仓位大于应有份额卖出
    for stock in Account.hold.keys():
        sell_amount = 0
        if stock not in hold_list:
            sell_amount = Account.sell_available[stock]
        else:
            # 计算当前股票市值
            stock_close_price = multi_stock_1day.select_code(stock).data['close'][0]
            stock_market_value = Account.hold[stock] * stock_close_price
            if stock_market_value > capture / stock_counts:
                sell_amount = (stock_market_value - (capture / stock_counts)) / stock_close_price
        if sell_amount < 100:
            continue
        # print("Account.hold")
        # print("stock : ",stock)
        # print("sell_amount : ",sell_amount)
        # print(Account.hold)
        # print("capture : ",capture)
        # print("stock_market_value : ", stock_market_value)
        # 形成order
        order = Account.send_order(
            code=stock,
            time=date,
            amount=sell_amount,
            towards=QA.ORDER_DIRECTION.SELL,
            price=0,
            order_model=QA.ORDER_MODEL.CLOSE,
            amount_model=QA.AMOUNT_MODEL.BY_AMOUNT
        )
        # print(item.to_json()[0])
        Broker.receive_order(QA.QA_Event(order=order))
        trade_mes = Broker.query_orders(Account.account_cookie, 'filled')
        res = trade_mes.loc[order.account_cookie, order.realorder_id]
        order.trade(res.trade_id, res.trade_price,
                    res.trade_amount, res.trade_time)

    # 买入。在新选的股票列表按照期望仓位买入，股票仓位小于应有份额补仓
    for stock in hold_list:
        buy_amount = 0
        # 当前股票收盘价
        stock_close_price = multi_stock_1day.select_code(stock).data['close'][0]
        # 计算期望的仓位
        ought_to_position = (Account.cash_available + cal_account_market_value(Account.hold, multi_stock_1day)) / stock_counts / stock_close_price
        # 如果该股票的期望仓位小于已持有仓位
        if stock in Account.hold.keys():
            buy_amount = ought_to_position - Account.hold[stock]
        else:
            buy_amount = ought_to_position

        if buy_amount < 100:
            continue

        print("++++++++++++++++++Account.hold++++++++++++++++++++")
        print("stock : ",stock)
        print("sell_amount : ",buy_amount)
        print(Account.hold)
        print("ought_to_position : ",ought_to_position)

        order = Account.send_order(
            code=stock,
            time=date,
            amount=buy_amount,
            towards=QA.ORDER_DIRECTION.BUY,
            price=0,
            order_model=QA.ORDER_MODEL.CLOSE,
            amount_model=QA.AMOUNT_MODEL.BY_AMOUNT
        )
        # print(item.to_json()[0])

        Broker.receive_order(QA.QA_Event(order=order))
        trade_mes = Broker.query_orders(Account.account_cookie, 'filled')
        res = trade_mes.loc[order.account_cookie, order.realorder_id]
        order.trade(res.trade_id, res.trade_price,
                    res.trade_amount, res.trade_time)

    print("after all Account.hold")
    print(Account.hold)
    Account.settle()


trade_date_month = get_month_trade_date('2018-01-01','2019-01-01')
print(trade_date_month)

factor_data = pd.DataFrame()
for item in range(len(trade_date_month)):
    trade_date = trade_date_month[item]
    # factor_data['trade_date'] = trade_date_month[item]
    factor_data['pe'] = stock_data_add_ind(func_map_pe,trade_date,multi_stock_daily_data)
    factor_data['pb'] = stock_data_add_ind(func_map_pb, trade_date, multi_stock_daily_data)
    factor_data['marketcap'] = stock_data_add_ind(func_map_marketcap, trade_date, multi_stock_daily_data)
    factor_data['roic'] = stock_data_add_ind(func_map_ROIC, trade_date, multi_stock_daily_data)
    factor_data['npgr'] = stock_data_add_ind(func_map_NPGR, trade_date, multi_stock_daily_data)
    factor_data['ors'] = stock_data_add_ind(func_map_ORS, trade_date, multi_stock_daily_data)

    hold_list = select_stocklist(factor_data)

    rebalance(hold_list,trade_date,multi_stock_daily_data.select_time(start=trade_date,end=trade_date))


