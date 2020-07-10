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

    res_df['dif'] = dif
    res_df['dem'] = dem
    res_df['histogram'] = histogram

    df_cross = dif > dem
    df_cross_last = df_cross.shift(1)

    res_df['death_cross'] = df_cross < df_cross_last
    res_df['gold_cross'] = df_cross > df_cross_last

    gold_cross_df = res_df[res_df['gold_cross']]
    death_cross_df = res_df[res_df['death_cross']]

    res_df['limit_close'] = None
    res_df['limit_dif'] = None
    res_df['limit_histogram'] = None

    cross_df = pd.concat([gold_cross_df, death_cross_df], axis=0).sort_index()

    for i in range(len(cross_df) - 1, 0, -1):
        cur_index = cross_df.iloc[i].name
        last_index = cross_df.iloc[i-1].name
        temp_df = res_df.loc[last_index + 1: cur_index - 1, :][['close', 'dif', 'histogram']]

        if cross_df.iloc[i].gold_cross:
            temp_row = temp_df.min(axis=0)
        else:
            temp_row = temp_df.max(axis=0)

        res_df.loc[cur_index, 'limit_close'] = temp_row['close']
        res_df.loc[cur_index, 'limit_dif'] = temp_row['dif']
        res_df.loc[cur_index, 'limit_histogram'] = temp_row['histogram']


    for index, row in cross_df.iloc[::-1].iterrows():
        front_row = cross_df.loc[cross_df.index < index][-1].index

    for gold_index, gold_row in gold_cross_df.iloc[::-1].iterrows():
        death_index = death_cross_df[death_cross_df.index < gold_index].iloc[-1].name
        temp_row = res_df.loc[death_index:gold_index, :][['close', 'dif', 'histogram']].min(axis=0)
        res_df.loc[gold_index, 'limit_close'] = temp_row['close']
        res_df.loc[gold_index, 'limit_dif'] = temp_row['dif']
        res_df.loc[gold_index, 'limit_histogram'] = temp_row['histogram']

    for death_index, death_row in death_cross_df.iloc[::-1].iterrows():
        gold_index = gold_cross_df[gold_cross_df.index < death_index].iloc[-1].name
        temp_row = res_df.loc[gold_index:death_index, :][['close', 'dif', 'histogram']].max(axis=0)
        res_df.loc[death_index, 'limit_close'] = temp_row['close']
        res_df.loc[death_index, 'limit_dif'] = temp_row['dif']
        res_df.loc[death_index, 'limit_histogram'] = temp_row['histogram']




    cross_df = df[(df.index < cross_tm) & (df[pre_cross_type])]

    print("123123")



if __name__ == '__main__':

    df = pd.read_csv("000651.csv")

    macd_extend_data(df)

