import trendln
import matplotlib.pyplot as plt
import talib as ta
import pandas as pd

from BackTraderTest.BackTraderFunc.makeData import QAStock2btData, QAGetStockList
import yfinance as yf
import scipy.signal
import numpy as np
import os
import pandas_profiling
import talib as ta
import seaborn as sns

# pd全局设置
from mt_com_func import mt_add_suffix_name
from mt_read_data import mt_read_index_codes

pd.set_option('display.max_rows', 5000)
pd.set_option('display.max_columns', 100)
pd.set_option('display.width', 300)

# tick = yf.Ticker('^GSPC') # S&P500
# hist = tick.history(period="max", rounding=True)
# trendln.plot_support_resistance(hist[-100:].Close)

# dataframe = QAStock2btData("000651", '2014-01-01', '2020-10-13')
# trendln.plot_sup_res_date(dataframe[-350:-200].close,idx=dataframe[-350:-200].index)
# plt.savefig('suppres.svg', format='svg')
# plt.show()
# plt.clf() #clear figure


def makeDfListBySMA(df, period_s=20, period_m=60, period_l=120, minDays=None):
    '''
    根据输入的dataframe，筛选出多头排列的部分
    :param df:
    :param period_s:
    :param period_m:
    :param period_l:
    :param minDays:
    :return: dataframe的列表，包含多头排列的部分
    '''
    df['sma20'] = ta.SMA(df.close, period_s)
    df['sma60'] = ta.SMA(df.close, period_m)
    df['sma120'] = ta.SMA(df.close, period_l)
    df.loc[(df['sma20'] > df['sma60']) & (df['sma60'] > df['sma120']), 'long'] = 1
    df['long_shift_1'] = df['long'].shift()
    longStartDf = df.loc[(df['long'] == 1) & (df['long_shift_1'] != 1)]
    longEndDf = df.loc[(df['long'] != 1) & (df['long_shift_1'] == 1)]
    if len(longEndDf) < len(longStartDf):
        longEndDf = longEndDf.append(df.iloc[-1])
    dfList = []
    for index in range(len(longStartDf)):
        dfList.append(df.loc[longStartDf.iloc[index].name:longEndDf.iloc[index].name])
    return dfList

def makeDfListByTopPrice(df):
    '''
    获取dataframe的列表，其中每个dataframe都包含一个最高点到下一个最高点的bar。。
    :param df:
    :return:
    '''
    indexes = scipy.signal.argrelextrema(
        np.array(df.close),
        comparator=np.greater, order=1
    )
    dfList = []
    topPrice = df.iloc[0].close
    lastIndex = 0
    # print("未经过处理的 point：%s"%(indexes[0]))
    for index in indexes[0]:
        # print("未经过处理的 时间 %s"%(df.iloc[index].name))
        if df.iloc[index].close > topPrice:
            topPrice = df.iloc[index].close
            dfList.append(df.iloc[lastIndex:index + 1])   # iloc 前闭后开
            lastIndex = index
    # 添加最后一个最高点到多头排列结束的部分
    if lastIndex < len(df) - 1:
        dfList.append(df.iloc[lastIndex:])  # iloc 前闭后开

    return dfList
    # print("经过处理的 point :%s"%indexlist)
    # for i in indexlist:
    #     print("经过处理的 时间 %s"%(df.iloc[i].name))

def stopPriceStatistic(df):
    dataframe = df

    dfList = makeDfListBySMA(dataframe)

    resultDf = pd.DataFrame(
        columns=['code', 'lossRate', 'startDate', 'endDate', 'minDate', 'isLastSmallPeriod', 'smallPeriodDays',
                 'bigPeriodDays', 'riseRange'])

    for df in dfList:
        smallPeriodDfList = makeDfListByTopPrice(df)
        isLastSP = False
        for sdfIndex in range(len(smallPeriodDfList)):
            sdf = smallPeriodDfList[sdfIndex]
            isLastSP = True if sdfIndex == len(smallPeriodDfList) - 1 else False
            resultDf.loc[len(resultDf) + 1] ={'code':df.code[0], 'lossRate': (sdf.close.min() / sdf.close[0]) - 1, 'startDate': sdf.iloc[0].name, 'endDate':sdf.iloc[-1].name,'isLastSmallPeriod':isLastSP,
                             'minDate': sdf.close.idxmin(), 'smallPeriodDays': len(sdf), 'bigPeriodDays':len(df) , 'riseRange':df.close[-1]/df.close[0]}

    return resultDf




# vector = [
#     0, 6, 25, 20, 15, 8, 15, 6, 0, 6, 0, -5, -15, -3, 4, 10, 8, 13, 8, 10, 3,
#     1, 20, 7, 3, 0 ]
# import scipy.signal
# print('Detect peaks with order (distance) filter.')
# indexes = scipy.signal.argrelextrema(
#     np.array(vector),
#     comparator=np.less,order=1
# )
# print('Peaks are: %s' % (indexes[0]))


# scipy.signal.find_peaks

def ReadDataFormLocal(dirName):
    '''
    从指定文件夹读取数据
    :return:
    '''
    count = 0
    df = pd.DataFrame()
    path = "./" + dirName
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            if ".csv" in filename:
                count += 1
                print("current count :%d"%count)
                df = pd.concat([df, pd.read_csv(dirpath + '/' +filename, index_col=0)], ignore_index=True)
    return df

def MakeDataToCsv():
    '''
    生成沪深300的股票数据到指定的文件夹
    :return:
    '''
    stockList = mt_read_index_codes('000300.SH')
    stockList = list(map(lambda x: x.split(".")[0], stockList))
    stockList = list(map(mt_add_suffix_name, stockList))
    count = 0
    resultTemp = pd.DataFrame()
    for stock in stockList:
        df = QAStock2btData(stock,  '2010-01-01', '2020-10-10')
        df_indBias = IndicateBias(df, 20, 60, 120)
        df= stopPriceStatistic(df)
        df = df.merge(df_indBias[["s_bias","m_bias","l_bias"]], left_on="startDate", right_index=True)
        df.to_csv('./analysisData/' + stock + '.csv')
        count += 1
        print("current code is :%s"%stock)
        resultTemp = pd.concat([resultTemp, df])
        if count > 5000:
            break

def LossRateDataPretreatment(df, bigPeriodMin):
    '''
    预处理lossRate数据
    删除loseRate为0 的数据
    :param bigPeriodMin:
    :return:
    '''
    if "lossRate" in df.columns:
        df = df[~(df["lossRate"] == 0)]
    if "bigPeriodDays" in df.columns:
        df = df[df["bigPeriodDays"] > bigPeriodMin]
    return df

def IndicateBias(df, p_s, p_m, p_l):
    '''
    给dataframe 添加乖离率指标
    :param df:
    :param p_s:
    :param p_m:
    :param p_l:
    :return:
    '''
    s_series = ta.SMA(df.close, timeperiod=p_s)
    m_series = ta.SMA(df.close, timeperiod=p_m)
    l_series = ta.SMA(df.close, timeperiod=p_l)
    df["s_bias"] = (df.close / s_series) - 1
    df["m_bias"] = (s_series / m_series) - 1
    df["l_bias"] = (m_series / l_series) - 1
    return df



if __name__ == '__main__':
    # fig, ax = plt.subplots(figsize=(10, 7))
    # ax.hist(resultTemp['riseRange'], bins=20, rwidth=0.5)
    # ax.set_title("Simple Histogram")
    # plt.show()
    # MakeDataToCsv()



    df = ReadDataFormLocal("analysisData")
    df = LossRateDataPretreatment(df, 10)

    # profile = df.profile_report(title='Titanic Dataset')
    # profile.to_file(output_file='./result/titanic_report_deleteLoseRate0.html')

    dfNor = df[df["isLastSmallPeriod"] == False]
    dfLst = df[df["isLastSmallPeriod"] == True]
    dfNor = dfNor[df["smallPeriodDays"] > 5]

    # dfNor = dfNor[df["lossRate"] < -0.07]
    print(dfNor.corr())
    # dfNor = dfNor[df["s_bias"] < 0.1232301735]
    # print(dfNor.corr())
    sns.pairplot(dfNor)
    plt.show()

    # profile = dfNor.profile_report(title='筛选lossRate小于-0.07')
    # profile.to_file(output_file='./result/筛选lossRate小于-0.07.html')
    #
    # profile = dfLst.profile_report(title='Titanic Dataset')
    # profile.to_file(output_file='./result/titanic_report_deleteLoseRate0Last.html')


