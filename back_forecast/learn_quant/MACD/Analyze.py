from rqalpha.api import *
from rqalpha import run_func

import talib
import pandas as pd


#显示所有列
pd.set_option('display.max_columns', None)
#显示所有行
pd.set_option('display.max_rows', None)
#设置value的显示长度为100，默认为50
pd.set_option('max_colwidth',100)
pd.set_option('display.width',200)



result_dict = pd.read_pickle('result2.pkl')

print(type(result_dict))
print(result_dict.keys())
print(result_dict['summary'])
print(result_dict['trades'])
print(result_dict['trades']['transaction_cost'].sum())
# print('trade',result_dict['trades'])
# print('protfolio',result_dict['protfolio'])
# print('benchmark_portfolio',result_dict['benchmark_portfolio'])
# print('stock_account',result_dict['stock_account'])
# print('stock_positions',result_dict['stock_positions'])
# print(result_dict['summary'].keys())