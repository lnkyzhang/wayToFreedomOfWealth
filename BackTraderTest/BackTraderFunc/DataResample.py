import pandas as pd


def data_min_resample(min_data, type_='5min'):
    """分钟线采样成大周期


    分钟线采样成子级别的分钟线


    time+ OHLC==> resample
    Arguments:
        min {[type]} -- [description]
        raw_type {[type]} -- [description]
        new_type {[type]} -- [description]
    """

    CONVERSION = {
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'vol': 'sum',
        'amount': 'sum'
    } if 'vol' in min_data.columns else {
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum',
        'amount': 'sum'
    }
    min_data = min_data.loc[:, list(CONVERSION.keys())]

    if "min" in type_:
        idx = min_data.index
        part_1 = min_data.iloc[idx.indexer_between_time('9:30', '11:30')]
        part_1_res = part_1.resample(
            type_,
            base=30,
            closed='right',
            loffset=type_
        ).apply(CONVERSION)
        part_2 = min_data.iloc[idx.indexer_between_time('13:00', '15:00')]
        part_2_res = part_2.resample(
            type_,
            base=0,
            closed='right',
            loffset=type_
        ).agg(CONVERSION)
        part_1_res['type'] = part_2_res['type'] = type_ if (type_ !='1D') else 'day'
        return pd.concat(
            [part_1_res,
             part_2_res]
        ).dropna().sort_index()
    else:
         df = min_data.resample(
            type_,
            base=0,
            closed='right'
        ).agg(CONVERSION).dropna()

         df.index = df.index.map(lambda t: t.replace(hour=15))
         return df