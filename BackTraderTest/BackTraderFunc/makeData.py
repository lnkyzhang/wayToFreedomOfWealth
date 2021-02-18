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

def QAStockMin2btData(code, startDate, endDate, period):
    dataframe = QA.QA_fetch_stock_min_adv(code, startDate, endDate, frequence=period).to_qfq().data
    dataframe = dataframe.reset_index(1)
    return dataframe

def QAGetStockList():
    return QA.QA_fetch_stock_list_adv().code.to_list()



if __name__ == '__main__':
    # a = QAIndex2btData("512000", '2017-01-01', '2020-10-13')
    # print(a)

    dataframe = QAStockMin2btData("000651", '2020-07-01', '2020-08-13', "60min")

    # a = QAGetStockList()
    print("1")