
import pandas_market_calendars as mcal
from datetime import time
import pandas as pd
import talib as ta
import QUANTAXIS as QA

# # Create a calendar
# sse = mcal.get_calendar('SSE', open_time=time(9, 30), close_time=time(15, 00))
# print(sse.tz.zone)
# print('open, close: %s, %s' % (sse.open_time, sse.close_time))
# # Show available calendars
# # print(mcal.get_calendar_names())
# early = sse.schedule(start_date='2000-01-01', end_date='2000-04-10')
#
# print(early)
#
from BackTraderTest.BackTraderFunc.makeData import QAStock2btData
from matplotlib import pyplot as plt
import sympy

dataframe = QAStock2btData("600036", '2012-01-01', '2029-01-13')


# 测试natr
# a = ta.ATR(dataframe.high, dataframe.low, dataframe.close)
# ema20 = ta.EMA(dataframe.close)
#
# a = a / ema20

real = ta.PPO(dataframe.close,fastperiod=20, slowperiod=60)


fig, ax = plt.subplots(figsize=(10, 7))
ax.hist(real, bins=20, rwidth=0.5)
ax.set_title("Simple Histogram")


print("low 0.1 :%f, mid 0.5 :%f , high 0.9 :%f"%(real.quantile(q=0.1), real.quantile(q=0.5),real.quantile(q=0.9)))
print("-5-5 :%f"%((len(real[real<5][real>-5]))/len(real)))
plt.show()



# 测试macd柱线图差值分布
# dif, dem, histogram = ta.MACD(dataframe.close,fastperiod=60, slowperiod=120, signalperiod=9)
# histlast = histogram.shift(1)
# histDif = histogram - histlast
# plt.show()


# 测试解方程
# def solveShortMidCrossPrice(shortSMA, shortEndData, shortN, midSMA, midEndData, midN):
#     '''
#     推算sma20和sma60交叉时的价格
#     :param shortEMA:
#     :param shortEndData:
#     :param shortN:
#     :param midEMA:
#     :param minEndData:
#     :param midN:
#     :return:
#     '''
#     x = sympy.symbols('x')
#     return sympy.solve(shortSMA + (x / shortN) - (shortEndData / shortN) - midSMA - (x / midN) + (midEndData / midN) , x)
#
# a = solveShortMidCrossPrice(66.05,63.82,20,61.87,55.70,60)
# print(a)