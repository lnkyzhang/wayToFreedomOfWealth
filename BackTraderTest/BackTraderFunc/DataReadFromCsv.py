import pandas as pd

from BackTraderTest.BackTraderFunc.DataResample import data_min_resample
import pymongo

host = 'localhost'
port = 27017
_client = pymongo.MongoClient(host, port)
db = _client["stockMinDb"]


def read_dataframe(filename, years, typeList=[]):
    '''

    :param filename:
    :param years:
    :param typeList:
    :return: dataframe list
    '''
    colnames = ['ticker', 'period', 'date', 'time',
                'open', 'high', 'low', 'close', 'volume', 'amount']

    colsused = ['date',
                'open', 'high', 'low', 'close', 'volume']



    res = []

    df = pd.read_csv(filename,
                     skiprows=0,  # using own column names, skip header
                     header=0,
                     names=None,
                     usecols=colsused,
                     parse_dates=['date'],
                     infer_datetime_format=True,
                     index_col='date')

    if years:  # year or year range specified
        ysplit = years.split('-')

        # left side limit
        mask = df.index >= ((ysplit[0] or '0001') + '-01-01')  # support -YYYY

        # right side liit
        if len(ysplit) > 1:  # multiple or open ended (YYYY-ZZZZ or YYYY-)
            if ysplit[1]:  # open ended if not years[1] (YYYY- format)
                mask &= df.index <= (ysplit[1] + '-12-31')
        else:  # single year specified YYYY
            mask &= df.index <= (ysplit[0] + '-12-31')

        df = df.loc[mask]  # select the given date range

    # df['code'] = '002694'
    # df.index.rename('datetime', inplace=True)
    # # df['datetime'] = df.index

    if len(typeList) > 0:
        for i in typeList:
            res.append(data_min_resample(df, i))

    else:
        res.append(df)

    return res


def readFromDb(code, fq, years, typeList=[]):
    res = []

    if code in db.list_collection_names():

        collection = db[code]
        flt = {}
        cursor = collection.find(flt, {'_id': 0}).sort('date')

        df = pd.DataFrame(list(cursor))

        df.set_index('date', drop=True, inplace=True)

        if years:  # year or year range specified
            ysplit = years.split('-')

            # left side limit
            mask = df.index >= ((ysplit[0] or '0001') + '-01-01')  # support -YYYY

            # right side liit
            if len(ysplit) > 1:  # multiple or open ended (YYYY-ZZZZ or YYYY-)
                if ysplit[1]:  # open ended if not years[1] (YYYY- format)
                    mask &= df.index <= (ysplit[1] + '-12-31')
            else:  # single year specified YYYY
                mask &= df.index <= (ysplit[0] + '-12-31')

            df = df.loc[mask]  # select the given date range

        if fq == "qfq":
            adjFactor = df['factor'] / df['factor'].tail(1).values[0]
        elif fq == 'hfq':
            adjFactor = df['factor'] / df['factor'].head(1).values[0]
        else:
            adjFactor = df['factor'] / df['factor']

        adjFactor = adjFactor.values.reshape((adjFactor.shape[0], 1))

        # 价格相关
        prices = df[['open', 'high', 'low', 'close']].values
        df[['open', 'high', 'low', 'close']] = prices * adjFactor

        # 成交量
        df[['volume']] = df[['volume']].values / adjFactor


        if len(typeList) > 0:
            for i in typeList:
                res.append(data_min_resample(df, i))

        else:
            res.append(df)

    return res