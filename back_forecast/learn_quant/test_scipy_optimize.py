import numpy as np
import scipy.stats as stats
import scipy.optimize as opt

import QUANTAXIS as QA

from jqdatasdk import *
import pandas as pd

# pd全局设置
pd.set_option('display.max_rows', 5000)
pd.set_option('display.max_columns', 100)
pd.set_option('display.width', 300)






# df = pd.read_csv("holdlistQA.csv",header=None)
# df = df.drop_duplicates()
# df.columns = df.iloc[0,:]
# df = df.drop(0)
# df = df.reset_index(drop=True).set_index('date')
#
# print(df.loc['2010-10-29'].to_list())

if __name__ == '__main__':
    auth('15640316927', '316927')  # 账号是申请时所填写的手机号；密码为聚宽官网登录密码，新申请用户默认为手机号后6位

    print("剩余条数 :", get_query_count())
    # q = query(finance.STK_SHAREHOLDERS_SHARE_CHANGE).filter(finance.STK_SHAREHOLDERS_SHARE_CHANGE.code=='000651.XSHE',finance.STK_SHAREHOLDERS_SHARE_CHANGE.end_date>'2017-01-01').limit(10)

    stocks_list_before = get_index_stocks('000300.XSHG', '2018-12-31')
    stocks_list = get_index_stocks('000300.XSHG', '2018-01-01')

    different = set(stocks_list_before).difference(set(stocks_list))
    print(different)

    # df=finance.run_query(q)
    print(stocks_list_before)
    print("剩余条数 :", get_query_count())

