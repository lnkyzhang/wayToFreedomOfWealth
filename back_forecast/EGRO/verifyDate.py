import pandas as pd

import QUANTAXIS as QA
import numpy as np

import statsmodels.api as sm
from statsmodels import regression

#显示所有列
pd.set_option('display.max_columns', None)
#显示所有行
pd.set_option('display.max_rows', None)
#设置value的显示长度为100，默认为50
pd.set_option('max_colwidth',100)
pd.set_option('display.width',200)
df_read = pd.read_csv('Result.csv')
df_read = df_read[df_read['eps'] > 0 ].sort_values(by='underRate',ascending=False)

data=QA.QA_fetch_stock_list_adv()
stock_list = list(data['code'])

stock_list = ['000651','000001']

multi_stock_daily2018 = QA.QA_fetch_stock_day_adv(stock_list,'2018-12-28').data
multi_stock_daily2019 = QA.QA_fetch_stock_day_adv(stock_list,'2019-11-08').data

print(multi_stock_daily2018)
print('==============')
print(multi_stock_daily2019)

s2018 = multi_stock_daily2019.xs('2019-11-08')['close']
s2019 = multi_stock_daily2018.xs('2018-12-28')['close']

result = s2019/s2018

print(result)

print(df_read)
print(df_read.assign(result))
# df_read.query("code=='{}'".format(stock_code))['close']

# print(df_read.reset_index(drop=True))