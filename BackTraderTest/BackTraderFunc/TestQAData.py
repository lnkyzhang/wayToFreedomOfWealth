import QUANTAXIS as QA
import pandas as pd


def close_ema(series, N=20):
    return pd.Series.ewm(series, span=N, min_periods=N - 1, adjust=True).mean()

def increase_rate(series,N=1):
    return series.pct_change(N)

def LC_stockFilter_ind(dataframe):
    close = dataframe.close

    ema20 = close_ema(close, 20)
    ema60 = close_ema(close, 60)
    ema120 = close_ema(close, 120)

    c_s = (close - ema20) / ema20
    s_m = (ema20 - ema60) / ema60
    m_l = (ema60 - ema120) / ema120

    pct1 = increase_rate(close, 1)
    pct5 = increase_rate(close, 5)
    pct20 = increase_rate(close, 20)

    return pd.DataFrame({'c_s':c_s, 's_m':s_m, 'm_l':m_l, 'pct1':pct1, 'pct5':pct5, 'pct20':pct20})


def LC_sotckFilter_sta(stock_data, index_data, baseDate, futureDate):
    """
    测试雷公的91法则
    :param dataframe:
    :param inputDate: 输入的日期
    :param baseDate: 比较的日期
    :return:
    """

    # todo 判断输入的日期是否是交易日

    stock_base_data = stock_data.loc[baseDate, :]


    # 1.选
    # 获取大盘指数的数据
    indName = 'm_l'
    index_base_data = index_data.loc[baseDate, :]
    baseIndValue = index_base_data[indName].iloc[0]
    select_stock = stock_base_data[stock_base_data[indName] > baseIndValue]
    unselect_stock = stock_base_data[stock_base_data[indName] < baseIndValue]
    select_stock_list = select_stock.index.get_level_values(1).to_list()
    unselect_stock_list = unselect_stock.index.get_level_values(1).to_list()

    # 2.比
    index_future_data = index_data.loc[futureDate, :].iloc[0]
    select_curDate = stock_data.loc[futureDate, select_stock_list,:]
    unselect_curDate = stock_data.loc[futureDate, unselect_stock_list,:]

    return select_curDate['pct20'].mean() - index_future_data['pct20']









if __name__ == '__main__':
    stock_list = QA.QA_fetch_stock_list_adv()
    print(stock_list)

    stock_data = QA.QA_fetch_stock_day_adv(stock_list['code'].to_list()[:1000], '2010-01-01', '2020-10-13')
    index_data = QA.QA_fetch_index_day_adv('000001', '2017-01-01', '2020-10-13')

    print(stock_data.data)



    stock_ind = stock_data.to_qfq().add_func(LC_stockFilter_ind)
    index_ind = index_data.add_func(LC_stockFilter_ind)

    print(LC_sotckFilter_sta(stock_ind, index_ind,'2020-09-04', '2020-10-12'))

    # print(result)

    # tradeData = QA.QA_util_get_pre_trade_date('2020-10-12', 1)
    #
    # print(tradeData)  -0.010575086116018904