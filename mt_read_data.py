from mt_com_setting import *

def mt_read_dailyBasic_from_JQData(code, startDate, endDate):
    mydb = myClient['stockCommonDbTuShare']
    myCollection = mydb['stockDailyBasicJQData']

    flt = {'code': {'$in': code}, 'datetime': {'$gte': startDate, '$lte': endDate}}

    ref_ = myCollection.find(flt)
    df = pd.DataFrame(list(ref_))
    return df


def mt_read_stockDay_from_TuShare(code, startDate, endDate, qfq=False):
    mydb = myClient['stockDaysDbTuShare']
    myCollection = mydb[code]

    dateStart = datetime.datetime.strptime(startDate, '%Y-%m-%d')
    dateEnd = datetime.datetime.strptime(endDate + ' 23:00:00', '%Y-%m-%d %H:%M:%S')

    flt = {'datetime': {'$gte': dateStart, '$lt': dateEnd}}

    ref_ = myCollection.find(flt)
    df = pd.DataFrame(list(ref_))

    stand_adj = df.iloc[-1]['adjfactor']
    columns = ['close', 'open', 'low', 'high']
    if qfq:
        for column in columns:
            df[column] = df[column] * df['adjfactor'] / stand_adj

    return df


def mt_read_index_codes(index, date = ""):
    '''
    从数据库中获取指数成分股
    :param index: 指数代码
    :param date: 日期
    :return: []
    '''
    mydb = myClient['stockCommonDbTuShare']
    myCollection = mydb['stockIndexStocksJQData']

    if date == "":
        ref_ = myCollection.find({'index': index}).sort([('datetime',-1)]).limit(1)
    else:

        if date[5:7] >= "07":
            date = date[0:5] + "07-01"
        else:
            date = date[0:5] + "01-01"

        ref_ = myCollection.find({'index': index, 'datetime': {"$gt": date}}).limit(1)

    for d in ref_:
        print(d['codes'])
        return d['codes'].split(",")


def mt_read_stock_basic(list_date):
    mydb = myClient['stockCommonDbTuShare']
    myCollection = mydb['stockBasicTuShare']

    list_date = list_date.replace("-", "")
    ref_ = myCollection.find({'list_date': {"$lte": list_date}})

    result_df = pd.DataFrame(list(ref_))
    del result_df["_id"]
    return result_df
