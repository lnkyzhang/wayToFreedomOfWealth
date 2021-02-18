# 选股相关所做分析
import pandas as pd
# pd全局设置
from BackTraderTest.BackTraderFunc.makeData import QAStock2btData
from TestTradeIn import IndicateBias, ReadDataFormLocal
from mt_com_func import mt_add_suffix_name
from mt_read_data import mt_read_index_codes



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
        df = IndicateBias(df, 20, 60, 120)
        df = IndicatePctChange(df, 1)
        df = IndicatePctChange(df, 3)
        df = IndicatePctChange(df, 5)
        df = IndicatePctChange(df, 10)
        df = IndicatePctChange(df, 20)
        df = IndicatePctChange(df, 60)
        df = IndicatePctChange(df, 120)
        df = IndicatePctChange(df, 1, True)
        df = IndicatePctChange(df, 3, True)
        df = IndicatePctChange(df, 5, True)
        df = IndicatePctChange(df, 10, True)
        df = IndicatePctChange(df, 20, True)

        df = IndicateBias(df, 20, 60, 120)
        df.to_csv('./selectStock/' + stock + '.csv')
        count += 1
        print("current code is :%s"%stock)
        resultTemp = pd.concat([resultTemp, df])
        if count > 5000:
            break


def IndicatePctChange(df, days, reverse=False):
    '''
    增加环比数据
    :param df:
    :param days: 天数，也就是环比周期
    :param reverse: True:逆向环比
    :return:
    '''
    if reverse:
        df["pct_r_" + str(days)] = (-df.iloc[::-1].close.diff(days))/df.iloc[::-1].close
    else:
        df["pct_" + str(days)] = df.close.pct_change(days)
    return df


if __name__ == '__main__':
    df = ReadDataFormLocal("selectStock")
    print(df.corr())