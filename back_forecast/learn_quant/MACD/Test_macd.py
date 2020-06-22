from QAStrategy import QAStrategyCTABase
from QAStrategy.qastockbase import QAStrategyStockBase
import QUANTAXIS as QA
import matplotlib.pyplot as plt
import pandas as pd
from QUANTAXIS import QA_Risk

from MT_func import *
import datetime

import profile

# pd全局设置
pd.set_option('display.max_rows', 5000)
pd.set_option('display.max_columns', 100)
pd.set_option('display.width', 300)

data = QA.QA_fetch_stock_list_adv()
stock_list = list(data['code'])
stock_list = ['000001','000002','000004']

start = '2016-01-01'
end = '2019-11-22'

df = multi_stock_daily = QA.QA_fetch_stock_day_adv(stock_list, start, end)

print(df.data)