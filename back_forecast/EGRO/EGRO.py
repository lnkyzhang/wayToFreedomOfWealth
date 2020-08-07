import QUANTAXIS as QA
import pandas as pd
import numpy as np

import statsmodels.api as sm
from statsmodels import regression

from matplotlib import pyplot as plt

pd.set_option('display.max_rows', 5000)
pd.set_option('display.max_columns', 100)
pd.set_option('display.width', 300)

# res=QA.QA_fetch_financial_report(['000001','600100'],['2017-03-31','2017-06-30','2017-09-31','2017-12-31','2018-03-31'])



# QA.QA_util_log_info('指数列表')

data=QA.QA_fetch_stock_list_adv()
stock_list = list(data['code'])

# stock_list = ['000540']

multi_stock_daily_data = QA.QA_fetch_stock_day_adv(stock_list,'2018-12-28')
multi_stock_daily_data_now = QA.QA_fetch_stock_day_adv(stock_list,'2019-11-01')
res_adv = QA.QA_fetch_financial_report_adv(stock_list,'2013-12-31','2018-12-31')




# '''

df_result = pd.DataFrame(columns=['code','egro','avg','eps','valuation','underRate','price'])
count = 1
for stock_code in stock_list:
    count += 1;
    print("current stock id:",stock_code)
    print("count",count)

    df = res_adv.data[res_adv.data['code'].str.match(stock_code)]

    # 匹配年终报表
    # df_12 = df[df['report_date'].apply(str).str.match('[0-9]{4}1231.*')]
    df_12 = df[df['report_date'].dt.is_year_end]
    df_03 = df[df['report_date'].dt.month == 3]
    df_06 = df[df['report_date'].dt.month == 6]
    df_09 = df[df['report_date'].dt.month == 9]

    if df_12.shape[0] < 5:
        continue

    df_list = [df_12,df_03,df_06,df_09]

    # print("同比:")
    df_pctChange = df['report_date']
    for df_i in df_list:
        # df_i_reverse = df_i.iloc[::-1]
        df_i_pct = df_i.netProfitsBelongToParentCompanyOwner.pct_change()
        df_i_pct.name = df_i['report_date'].iloc[0].month
        df_pctChange = pd.concat([df_pctChange, df_i_pct], axis=1)

    # print(df_pctChange)
    # print(df_pctChange.columns)
    # 线性回归
    df_re12 = df_pctChange[12].dropna()[:5]
    X = np.arange(len(df_re12))
    x = sm.add_constant(X)
    model = regression.linear_model.OLS(df_re12, x).fit()
    a = model.params[0]
    b = model.params[1]
    # 得到增长中枢线
    Y_hat = X * b + a

    XX = np.column_stack((X, X**2))
    xx = sm.add_constant(XX)
    model1 = sm.OLS(df_re12,xx).fit()
    aa = model1.params[0]
    bb = model1.params[1]
    cc = model1.params[2]
    y_fitted = X * bb + aa

    # y_fitted = model1.fittedvalues
    # fig, ax = plt.subplots(figsize=(8, 6))
    # ax.plot(X, df_re12, 'o', label='data')
    # ax.plot(X, Y_hat, 'r--.', label='OLS')
    # ax.plot(X, y_fitted, 'r--.', label='2OLS')
    # plt.show()

    # 均值计算
    avg = df_pctChange[12].dropna()[:5].mean()
    eps = df_12['EPS'].iloc[-1]

    egro_1 = 5 * b + a
    egro_2 = 5 * bb + 5*5 * cc + aa
    egro = min(egro_1, egro_2, avg)

    valuation = ((2*egro*100) + 8.5)*eps
    price = multi_stock_daily_data.data.query("code=='{}'".format(stock_code))['close']
    if price.empty:
        continue
    try:
        price_now = multi_stock_daily_data_now.data.query("code=='{}'".format(stock_code))['close']
        price_scale = price_now.xs('2019-11-01') / price.xs('2018-12-28')
    except:
        price_now_struct = QA.QA_fetch_stock_day_adv(stock_code, '2018-12-28','2019-11-01')
        if price_now_struct is None:
            continue
        price_now = price_now_struct.to_qfq().data.iloc[-1]
        price_scale = price_now['close'] / price.xs('2018-12-28')

    underRate = valuation/price

    name = data.loc[stock_code]['name']

    dict_value = {'code':stock_code,'egro':egro,'egro_1':egro_1,'egro_2':egro_2,'avg':avg,'eps':eps,'valuation':valuation,'underRate':underRate,'price':price.iloc[0],'price_now':price_now.iloc[0],'price_scale':price_scale.iloc[0],'name':name}
    df_value = pd.DataFrame(data=dict_value)

    df_result = df_result.append(df_value, ignore_index=True)
# '''

print(df_result)
df_result.to_csv('Result.csv')