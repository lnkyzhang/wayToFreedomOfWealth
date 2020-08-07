from rqalpha.api import *
import numpy as np
import talib
import math
import sys
import QUANTAXIS as QA
import pandas as pd
import datetime
import tushare as ts

# pd全局设置
pd.set_option('display.max_rows', 5000)
pd.set_option('display.max_columns', 100)
pd.set_option('display.width', 300)

# tushare 账户设置
ts.set_token('50c48ae25bd98b7480a1512e5fd326ed186f88130eeb1ce8df9bfdd2')
pro = ts.pro_api()

data=QA.QA_fetch_stock_list_adv()
stock_list = list(data['code'])
# stock_list = ['000001','000002','000004']
stock_list = stock_list[0:100]

sort_up = ['market_cap', 'pe_ratio', 'pb_ratio']

start = '2010-01-01'
end = '2019-11-22'
multi_stock_daily_data = QA.QA_fetch_stock_day_adv(stock_list,start,end)
res_adv = QA.QA_fetch_financial_report_adv(stock_list,'2009-12-31',end)



def init(context):
    context.stocknum = 20

    context.up = ['market_cap', 'pe_ratio', 'pb_ratio']

    scheduler.run_monthly(score_select, tradingday=1)


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


def get_month_trade_date(start,end):
    # 从tushare获取交易日历
    stock_trade_date = pro.trade_cal(exchange='', start_date=start, end_date=end)
    stock_trade_date_month = stock_trade_date[stock_trade_date["is_open"] == 1]
    stock_trade_date_month['cal_date'] = stock_trade_date_month['cal_date'].apply(lambda x : pd.to_datetime(x, format='%Y%m%d'))
    stock_trade_date_month.index = stock_trade_date_month['cal_date']
    dfg = stock_trade_date_month.resample('M')
    business_end_day = dfg.apply({'cal_date': np.min})
    return business_end_day["cal_date"].reset_index(drop=True).tolist()



def get_fundamentalData():
    pass



def score_select(context, bar_dict):
    """打分法选股函数
    """
    print(context.now)
    # 1、选出因子数据、进行缺失值处理
    get_fundamentals
    q = query(
        fundamentals.eod_derivative_indicator.market_cap,
        fundamentals.eod_derivative_indicator.pe_ratio,
        fundamentals.eod_derivative_indicator.pb_ratio,
        fundamentals.financial_indicator.return_on_invested_capital,
        fundamentals.financial_indicator.inc_revenue,
        fundamentals.financial_indicator.inc_profit_before_tax
    )

    fund = get_fundamentals(q)

    factors_data = fund.T

    factors_data = factors_data.dropna()

    # 2、定义打分函数、确定股票池
    select_stocklist(context, factors_data)

    # 3、定义调仓函数
    rebalance(context)


def select_stocklist(context, factors_data):
    """打分的具体步骤、返回股票池
    因子升序从小到大分10组，第几组为所在组得分
        市值-market_cap、市盈率-pe_ratio、市净率-pb_ratio
    因子降序从大到小分10组，第几组为所在组得分
        ROIC-return_on_invested_capital、inc_revenue-营业总收入 和inc_profit_before_tax-利润增长率
    """
    # 循环每个因子去处理
    for name in factors_data.columns:

        # 因子升序的，进行升序排序
        if name in context.up:

            factor = factors_data.sort_values(by=name)[name]

        else:
            # 因子降序的，进行降序排序

            factor = factors_data.sort_values(by=name, ascending=False)[name]

        # 对单个因子进行打分处理
        # 新建一个因子分数列
        factor = pd.DataFrame(factor)

        factor[name + 'score'] = 0

        # 进行打分
        # 先求出每组数量，然后根据数量一次给出分数
        stock_groupnum = len(factors_data) // 10

        for i in range(10):

            if i == 9:
                factor[name + 'score'][(i + 1) * stock_groupnum:] = i + 1

            factor[name + 'score'][i * stock_groupnum: (i + 1) * stock_groupnum] = i + 1

        # 把每个因子的得分进行合并到原来因子数据当中
        factors_data = pd.concat([factors_data, factor[name + 'score']], axis=1)

    # logger.info(factors_data)
    # 对6个因子的分数列进行求和
    all_score = factors_data[
        ['market_capscore', 'pe_ratioscore', 'pb_ratioscore', 'return_on_invested_capitalscore', 'inc_revenuescore',
         'inc_profit_before_taxscore']].sum(1).sort_values()

    # 定义股票池
    context.stock_list = all_score.index[:context.stocknum]

    logger.info(context.stock_list)


def rebalance(context):
    """
    调仓函数
    卖出、买入
    """
    # 卖出
    for stock in context.portfolio.positions.keys():

        if stock not in context.stock_list:
            order_target_percent(stock, 0)

    # 买入
    for stock in context.stock_list:
        order_target_percent(stock, 1.0 / len(context.stock_list))


def before_trading(context):
    pass


def handle_bar(context, bar_dict):
    result = history_bars(context.s, 1, '1d', 'close', adjust_type='pre')
    print(result)


def after_trading(context):
    pass