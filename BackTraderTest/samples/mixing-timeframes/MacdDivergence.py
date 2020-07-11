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

    # make data with limit of cross
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

    # find divergence
    divergence_detect_cross_count = 5
    res_df['divergence_top'] = False
    res_df['divergence_bottom'] = False
    res_df['divergence_lastPoint'] = None

    def findDiverse(cross_df):
        for ii in range(len(cross_df) - 1, -1, -1):
            if ii > divergence_detect_cross_count:
                detect_count = divergence_detect_cross_count
            else:
                detect_count = ii

            divergence_type = None

            for jj in range(1, detect_count + 1):
                if cross_df.iloc[ii].gold_cross:
                    if cross_df.iloc[ii]['close'] < cross_df.iloc[ii - jj]['close'] \
                            and cross_df.iloc[ii]['dif'] > cross_df.iloc[ii - jj]['dif']:
                        divergence_type = 'divergence_bottom'

                else:
                    if cross_df.iloc[ii]['close'] > cross_df.iloc[ii - jj]['close'] \
                            and cross_df.iloc[ii]['dif'] < cross_df.iloc[ii - jj]['dif']:
                        divergence_type = 'divergence_top'

                if divergence_type is not None:
                    res_df.loc[cross_df.iloc[ii].name, [divergence_type]] = True
                    res_df.loc[cross_df.iloc[ii].name, ['divergence_lastPoint']] = cross_df.iloc[ii - jj][
                        'date']
                    break


    findDiverse(gold_cross_df)
    findDiverse(death_cross_df)
    print("123123123")

    # todo
    # 1.condition to recognize divergence
    # 2.how to make this macd divergence to backtrader lines
    




    # for ii in range(len(gold_cross_df) - 1, -1, -1):
    #     if ii > divergence_detect_cross_count:
    #         detect_count = divergence_detect_cross_count
    #     else:
    #         detect_count = ii
    #
    #     for jj in range(1, detect_count + 1):
    #         if gold_cross_df.iloc[ii]['close'] < gold_cross_df.iloc[ii - jj]['close']\
    #                 and gold_cross_df.iloc[ii]['dif'] > gold_cross_df.iloc[ii - jj]['dif']:
    #             res_df.loc[gold_cross_df.iloc[ii].name, ['divergence_bottom']] = True
    #             res_df.loc[gold_cross_df.iloc[ii].name, ['divergence_lastPoint']] = gold_cross_df.iloc[ii - jj]['date']
    #             break

    print("123123")


    cross_df = df[(df.index < cross_tm) & (df[pre_cross_type])]





if __name__ == '__main__':

    df = pd.read_csv("000651.csv")

    macd_extend_data(df)

