import pandas as pd
import talib
import numpy as np
import ta

from BackTraderTest.BackTraderFunc.DataReadFromCsv import read_dataframe
from BackTraderTest.BackTraderFunc.DataResample import data_min_resample

pd.set_option('display.max_rows', 5000)
pd.set_option('display.max_columns', 100)
pd.set_option('display.width', 300)


def TripleScreen_extend_data(df, timeScaleSmall, timeScaleLarge):


    df_large = data_min_resample(df, timeScaleLarge)
    df_large['slope'] = talib.LINEARREG_SLOPE(df_large['close'], 13)
    df_large['dif'], df_large['dem'], df_large['histogram'] = talib.MACD(df_large['close'], fastperiod=12, slowperiod=26, signalperiod=9)
    df_large['histogram_pre'] = df_large.shift(1)['histogram']
    df_large['macdTrade'] = df_large['histogram'] > df_large['histogram_pre']
    df_large['firstSignal'] = 0
    df_large.loc[(df_large['slope'] > 0) & (df_large['macdTrade']), 'firstSignal'] = True
    df_large.loc[(df_large['slope'] > 0) & (df_large['macdTrade'] == False), 'firstSignal'] = False

    df_small = data_min_resample(df, timeScaleSmall)
    df_small['fi'] = ta.volume.ForceIndexIndicator(close=df_small['close'], volume=df_small["volume"], n=2,
                                                   fillna=False).force_index()
    df_small['fi_pre'] = df_small['fi'].shift()
    df_small.loc[(df_small['fi'] > 0) & (df_small['fi_pre'] < 0), 'secondSignal'] = True

    df_temp = df_large.resample("d", ).pad()['firstSignal']
    res_df = pd.concat([df_small, df_temp], axis=1, join_axes=[df_small.index])

    res_df['buyPoint'] = 0
    res_df.loc[(res_df['secondSignal']) & (res_df['firstSignal']), 'buyPoint'] = True

    return res_df

















if __name__ == '__main__':

    df = read_dataframe("../samples/mixing-timeframes/000651.csv", "2010-2020", ["60min"])

    TripleScreen_extend_data(df[0], "d", 'w')
