import QUANTAXIS as QA
import pandas as pd



def QAIndex2btData(code, startDate, endDate):
    dataframe = QA.QA_fetch_index_day_adv(code, startDate, endDate).data
    dataframe = dataframe.reset_index(1)
    # dataframe.rename(columns={'vol': 'volume'}, inplace=True)
    return dataframe

def QAStock2btData(code, startDate, endDate):
    dataframe = QA.QA_fetch_stock_day_adv(code, startDate, endDate).to_qfq().data
    dataframe = dataframe.reset_index(1)
    # dataframe.rename(columns={'vol': 'volume'}, inplace=True)
    return dataframe

def QAStock2btDataOnline(code, startDate, endDate):
    dataframe = QA.QAFetch.QATdx.QA_fetch_get_stock_day(code, startDate, endDate,'01')
    dataframe = dataframe.reset_index(1)
    # dataframe.rename(columns={'vol': 'volume'}, inplace=True)
    return dataframe


if __name__ == '__main__':
    a = QAIndex2btData("512000", '2017-01-01', '2020-10-13')
    print(a)