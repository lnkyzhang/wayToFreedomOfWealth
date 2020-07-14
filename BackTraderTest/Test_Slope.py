import pandas as pd
import talib
import ta

from BackTraderTest.BackTraderFunc.DataReadFromCsv import read_dataframe
from BackTraderTest.BackTraderFunc.DataResample import data_min_resample

df = pd.DataFrame()

df['close'] = [2,2,2,2,2,3,4,2,2,2]

b = talib.LINEARREG_SLOPE(df['close'], 4)

df = read_dataframe("000651.csv", "2015-2016", "d")[0]

c = ta.add_volume_ta(df, high="high", low="low", close="close", volume="volume")

print(b)



