import pandas as pd

from BackTraderTest.BackTraderFunc.DataResample import data_min_resample


def read_dataframe(filename, years, typeList=[]):
    '''

    :param filename:
    :param years:
    :param typeList:
    :return: dataframe list
    '''
    colnames = ['ticker', 'period', 'date', 'time',
                'open', 'high', 'low', 'close', 'volume', 'openinterest']

    colsused = ['date',
                'open', 'high', 'low', 'close', 'volume', 'openinterest']

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