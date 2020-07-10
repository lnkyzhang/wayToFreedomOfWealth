import pandas as pd
import talib

pd.set_option('display.max_rows', 5000)
pd.set_option('display.max_columns', 100)
pd.set_option('display.width', 300)

def macd_extend_data(df):
    '''
    如果这个bar发生了金叉或死叉，根据交叉点查找3种极值[MACD，CLOSE, DIF]，并在当前bar，记录极值产生的时间
    :param df:
    :return:
    '''

    res_df = df

    dif, dem, histogram = talib.MACD(df['close'], fastperiod=12, slowperiod=26, signalperiod=9)

    df_cross = dif > dem
    df_cross_last = df_cross.shift(1)

    res_df['gold_cross'] = df_cross < df_cross_last
    res_df['death_cross'] = df_cross > df_cross_last

    print("123123")



if __name__ == '__main__':

    df = pd.read_csv("000651.csv")

    macd_extend_data(df)

