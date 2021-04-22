import pandas as pd
import talib
import numpy as np

pd.set_option('display.max_rows', 5000)
pd.set_option('display.max_columns', 100)
pd.set_option('display.width', 300)

def macd_extend_data(df):
    '''
    如果这个bar发生了金叉或死叉，根据交叉点查找3种极值[MACD，CLOSE, DIF]，并在当前bar，记录极值产生的时间
    index:timeframe
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
    for i in range(len(cross_df) - 1, -1, -1):
        cur_index = cross_df.iloc[i].name
        if i > 1:
            last_index = cross_df.iloc[i-1].name
        else:
            last_index = cross_df.iloc[i].name

        temp_df = res_df.loc[last_index: cur_index, :][['close', 'dif', 'histogram']]

        if cross_df.iloc[i].gold_cross:
            temp_row = temp_df.min(axis=0)
        else:
            temp_row = temp_df.max(axis=0)

        res_df.loc[cur_index, 'limit_close'] = temp_row['close']
        res_df.loc[cur_index, 'limit_dif'] = temp_row['dif']
        res_df.loc[cur_index, 'limit_histogram'] = temp_row['histogram']

    # find divergence
    divergence_detect_cross_count = 3
    res_df['divergence_top'] = False
    res_df['divergence_bottom'] = False
    res_df['divergence_lastPoint'] = None

    gold_cross_df = res_df[res_df['gold_cross']]
    death_cross_df = res_df[res_df['death_cross']]

    def get_abs_median(series, num):
        """
        获取近num个bar内，正数负数，取中位数的绝对值最大值
        :param series: Series类型
        :param num: 数量。最近多少个bar内计算最大值
        :return:
        """
        ser2 = series.iloc[-num:]
        op_media = np.median(ser2[ser2 > 0])
        ne_media = np.median(ser2[ser2 < 0])
        return np.nanmax([abs(op_media), abs(ne_media)])

    def findDiverse(cross_df):
        for ii in range(len(cross_df) - 1, -1, -1):
            if ii > divergence_detect_cross_count:
                detect_count = divergence_detect_cross_count
            else:
                detect_count = ii

            divergence_type = None

            for jj in range(1, detect_count + 1):
                if cross_df.iloc[ii].gold_cross:
                    if cross_df.iloc[ii]['limit_close'] < cross_df.iloc[ii - jj]['limit_close'] \
                            and cross_df.iloc[ii]['limit_dif'] > cross_df.iloc[ii - jj]['limit_dif']:
                        divergence_type = 'divergence_bottom'

                else:
                    if cross_df.iloc[ii]['limit_close'] > cross_df.iloc[ii - jj]['limit_close'] \
                            and cross_df.iloc[ii]['limit_dif'] < cross_df.iloc[ii - jj]['limit_dif']:
                        divergence_type = 'divergence_top'

                if divergence_type is not None:
                    # 解决DIF和DEA纠缠的问题：要求两个背离点对应的macd值不能太小。
                    cur_macd = cross_df.iloc[ii]['limit_histogram']
                    last_macd = cross_df.iloc[ii - jj]['limit_histogram']
                    median_macd = get_abs_median(res_df.loc[:cross_df.iloc[ii].name]['histogram'], 250)
                    if abs(cur_macd / last_macd) < 0.3 \
                        or max([abs(cur_macd), abs(last_macd)]) <= median_macd:
                        break

                    # 对背离点高度(dif)的要求：
                    cur_dif = cross_df.iloc[ii]['limit_dif']
                    last_dif = cross_df.iloc[ii - jj]['limit_dif']
                    median_dif = get_abs_median(res_df.loc[:cross_df.iloc[ii].name]['dif'], 250) * 0.5
                    if abs(cur_dif) < median_dif and abs(last_dif) < median_dif:
                        break

                    # DIF和价格的差，至少有一个比较显著才能算显著背离。
                    cur_close = cross_df.iloc[ii]['limit_close']
                    last_close = cross_df.iloc[ii - jj]['limit_close']
                    significance = abs((cur_dif - last_dif) / last_dif) + abs(cur_close - last_close) / last_close
                    if significance < 0.1:
                        break

                    res_df.loc[cross_df.iloc[ii].name, [divergence_type]] = True
                    res_df.loc[cross_df.iloc[ii].name, ['divergence_lastPoint']] = cross_df.iloc[ii - jj].name
                    break

    def findContinueDiverse(df):
        df.loc[df['divergence_top'] == True, "divergence_continue"] = df.loc[
            df[df['divergence_top'] == True]['divergence_lastPoint'], 'divergence_top'].values

        df.loc[df['divergence_bottom'] == True, "divergence_continue"] = df.loc[
            df[df['divergence_bottom'] == True]['divergence_lastPoint'], 'divergence_bottom'].values

    findDiverse(gold_cross_df)
    findDiverse(death_cross_df)

    findContinueDiverse(res_df)

    return res_df

    # todo
    # 1.condition to recognize divergence:
    # 2.how to make this macd divergence to backtrader lines : ALLN is a indicater can combine this to backtrader
    # 3.learn benchmark
    # 4.data feed from pandas and extendPandasData   :  pandasData inherit







if __name__ == '__main__':

    df = pd.read_csv(r"D:\script\waytofreedom\wayToFreedomOfWealth\BackTraderTest\BackTraderFunc\600029.csv")

    macd_extend_data(df[:100])

