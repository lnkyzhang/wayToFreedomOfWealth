import numpy
from QUANTAXIS import DATABASE, QA_DataStruct_Stock_day, datetime, QA_DataStruct_Index_day, QA_DataStruct_Index_min, QA_DataStruct_Stock_min, \
    QA_util_code_tolist, QA_util_date_stamp, QA_util_date_valid, QA_util_to_json_from_pandas, QA_util_log_info, \
    QA_util_time_stamp, pd
import QUANTAXIS as QA


# pd全局设置
from QUANTAXIS.QAUtil.QADate import QA_util_datetime_to_strdatetime

#from DyCommon.IntraDayMACD.MT_macd_config import ADJ_FACTOR
ADJ_FACTOR = 'adj'

pd.set_option('display.max_rows', 5000)
pd.set_option('display.max_columns', 100)
pd.set_option('display.width', 300)

def MT_fetch_stock_day_adv(
        code,
        count, end=None,
        if_drop_index=True,
        # 🛠 todo collections 参数没有用到， 且数据库是固定的， 这个变量后期去掉
        collections=DATABASE.stock_day):
    '''

    :param code:  股票代码
    :param start: 开始日期
    :param end:   结束日期
    :param if_drop_index:
    :param collections: 默认数据库
    :return: 如果股票代码不存 或者开始结束日期不存在 在返回 None ，合法返回 QA_DataStruct_Stock_day 数据
    '''
    '获取股票日线'
    # end = start if end is None else end
    # start = str(start)[0:10]
    end = str(end)[0:10]

    # if start == 'all':
    #     start = '1990-01-01'
    #     end = str(datetime.date.today())

    res = MT_fetch_stock_day(code, count, end, format='pd')
    if res is None:
        # 🛠 todo 报告是代码不合法，还是日期不合法
        print(
            "QA Error QA_fetch_stock_day_adv parameter code=%s , start=%s, end=%s call QA_fetch_stock_day return None" % (
                code, count, end))
        return None
    else:
        res_reset_index = res.set_index(['date', 'code'], drop=if_drop_index)
        # if res_reset_index is None:
        #     print("QA Error QA_fetch_stock_day_adv set index 'datetime, code' return None")
        #     return None
        return QA_DataStruct_Stock_day(res_reset_index)


def MT_fetch_stock_min_adv(
        code,
        count, end=None,
        frequence='1min',
        if_drop_index=True,
        # 🛠 todo collections 参数没有用到， 且数据库是固定的， 这个变量后期去掉
        collections=DATABASE.stock_min):
    '''
    '获取股票分钟线'
    :param code:  字符串str eg 600085
    :param start: 字符串str 开始日期 eg 2011-01-01
    :param end:   字符串str 结束日期 eg 2011-05-01
    :param frequence: 字符串str 分钟线的类型 支持 1min 1m 5min 5m 15min 15m 30min 30m 60min 60m 类型
    :param if_drop_index: Ture False ， dataframe drop index or not
    :param collections: mongodb 数据库
    :return: QA_DataStruct_Stock_min 类型
    '''
    if frequence in ['1min', '1m']:
        frequence = '1min'
    elif frequence in ['5min', '5m']:
        frequence = '5min'
    elif frequence in ['15min', '15m']:
        frequence = '15min'
    elif frequence in ['30min', '30m']:
        frequence = '30min'
    elif frequence in ['60min', '60m']:
        frequence = '60min'
    else:
        print(
            "QA Error QA_fetch_stock_min_adv parameter frequence=%s is none of 1min 1m 5min 5m 15min 15m 30min 30m 60min 60m" % frequence)
        return None

    # __data = [] 未使用

    # end = start if end is None else end
    # if len(start) == 10:
    #     start = '{} 09:30:00'.format(start)

    if len(end) == 10:
        end = '{} 15:00:00'.format(end)

    # if start == end:
    #     # 🛠 todo 如果相等，根据 frequence 获取开始时间的 时间段 QA_fetch_stock_min， 不支持start end是相等的
    #     print(
    #         "QA Error QA_fetch_stock_min_adv parameter code=%s , start=%s, end=%s is equal, should have time span! " % (
    #             code, start, end))
    #     return None

    # 🛠 todo 报告错误 如果开始时间 在 结束时间之后

    res = MT_fetch_stock_min(
        code, count, end, format='pd', frequence=frequence)
    if res is None:
        print(
            "QA Error QA_fetch_stock_min_adv parameter code=%s , count=%s, end=%s frequence=%s call QA_fetch_stock_min return None" % (
                code, count, end, frequence))
        return None
    else:
        res_set_index = res.set_index(['datetime', 'code'], drop=if_drop_index)
        # if res_set_index is None:
        #     print("QA Error QA_fetch_stock_min_adv set index 'datetime, code' return None")
        #     return None
        return QA_DataStruct_Stock_min(res_set_index)

def MT_fetch_index_day_adv(
        code,
        count, end=None,
        if_drop_index=True,
        # 🛠 todo collections 参数没有用到， 且数据库是固定的， 这个变量后期去掉
        collections=DATABASE.index_day):
    '''
    :param code: code:  字符串str eg 600085
    :param start:  字符串str 开始日期 eg 2011-01-01
    :param end:  字符串str 结束日期 eg 2011-05-01
    :param if_drop_index: Ture False ， dataframe drop index or not
    :param collections:  mongodb 数据库
    :return:
    '''
    '获取指数日线'
    # end = start if end is None else end
    # start = str(start)[0:10]
    end = str(end)[0:10]

    # 🛠 todo 报告错误 如果开始时间 在 结束时间之后
    # 🛠 todo 如果相等

    res = MT_fetch_index_day(code, count, end, format='pd')
    if res is None:
        print(
            "QA Error QA_fetch_index_day_adv parameter code=%s count=%s end=%s call QA_fetch_index_day return None" % (
                code, count, end))
        return None
    else:
        res_set_index = res.set_index(['date', 'code'], drop=if_drop_index)
        # if res_set_index is None:
        #     print("QA Error QA_fetch_index_day_adv set index 'date, code' return None")
        #     return None
        return QA_DataStruct_Index_day(res_set_index)

def MT_fetch_index_min_adv(
        code,
        count, end=None,
        frequence='1min',
        if_drop_index=True,
        collections=DATABASE.index_min):
    '''
    '获取股票分钟线'
    :param code:
    :param start:
    :param end:
    :param frequence:
    :param if_drop_index:
    :param collections:
    :return:
    '''
    if frequence in ['1min', '1m']:
        frequence = '1min'
    elif frequence in ['5min', '5m']:
        frequence = '5min'
    elif frequence in ['15min', '15m']:
        frequence = '15min'
    elif frequence in ['30min', '30m']:
        frequence = '30min'
    elif frequence in ['60min', '60m']:
        frequence = '60min'

    # __data = [] 没有使用

    # end = start if end is None else end
    # if len(start) == 10:
    #     start = '{} 09:30:00'.format(start)
    if len(end) == 10:
        end = '{} 15:00:00'.format(end)

    # 🛠 todo 报告错误 如果开始时间 在 结束时间之后

    # if start == end:
    # 🛠 todo 如果相等，根据 frequence 获取开始时间的 时间段 QA_fetch_index_min_adv， 不支持start end是相等的
    # print("QA Error QA_fetch_index_min_adv parameter code=%s , start=%s, end=%s is equal, should have time span! " % (code, start, end))
    # return None

    res = MT_fetch_index_min(
        code, count, end, format='pd', frequence=frequence)
    if res is None:
        print(
            "QA Error QA_fetch_index_min_adv parameter code=%s count=%s end=%s frequence=%s call QA_fetch_index_min return None" % (
                code, count, end, frequence))
    else:
        res_reset_index = res.set_index(
            ['datetime', 'code'], drop=if_drop_index)
        # if res_reset_index is None:
        #     print("QA Error QA_fetch_index_min_adv set index 'date, code' return None")
        return QA_DataStruct_Index_min(res_reset_index)




def MT_fetch_index_day(code, count, end, format='numpy', collections=DATABASE.index_day):
    '获取指数日线'
    # start = str(start)[0:10]
    end = str(end)[0:10]
    code = QA_util_code_tolist(code)
    if QA_util_date_valid(end) == True:

        cursor = collections.find({
            'code': {'$in': code}, "date_stamp": {
                "$lte": QA_util_date_stamp(end),
                # "$gte": QA_util_date_stamp(start)
            }}, {"_id": 0}, batch_size=10000).sort([("date_stamp", -1)]).limit(count)

        res = pd.DataFrame([item for item in cursor])
        try:
            res = res.assign(volume=res.vol, date=pd.to_datetime(
                res.date)).drop_duplicates((['date', 'code'])).set_index('date', drop=False)
        except:
            res = None

        if format in ['P', 'p', 'pandas', 'pd']:
            return res
        elif format in ['json', 'dict']:
            return QA_util_to_json_from_pandas(res)
        # 多种数据格式
        elif format in ['n', 'N', 'numpy']:
            return numpy.asarray(res)
        elif format in ['list', 'l', 'L']:
            return numpy.asarray(res).tolist()
        else:
            print("QA Error QA_fetch_index_day format parameter %s is none of  \"P, p, pandas, pd , n, N, numpy !\" " % format)
            return None
    else:
        QA_util_log_info(
            'QA Error QA_fetch_index_day data parameter count=%s end=%s is not right' % (count, end))


def MT_fetch_index_min(
        code,
        count, end,
        format='numpy',
        frequence='1min',
        collections=DATABASE.index_min):
    '获取股票分钟线'
    if frequence in ['1min', '1m']:
        frequence = '1min'
    elif frequence in ['5min', '5m']:
        frequence = '5min'
    elif frequence in ['15min', '15m']:
        frequence = '15min'
    elif frequence in ['30min', '30m']:
        frequence = '30min'
    elif frequence in ['60min', '60m']:
        frequence = '60min'
    _data = []
    code = QA_util_code_tolist(code)
    cursor = collections.find({
        'code': {'$in': code}, "time_stamp": {
            # "$gte": QA_util_time_stamp(start),
            "$lte": QA_util_time_stamp(end)
        }, 'type': frequence
    }, {"_id": 0}, batch_size=10000).sort([("time_stamp", -1)]).limit(count)
    if format in ['dict', 'json']:
        return [data for data in cursor]
    # for item in cursor:
    _data = pd.DataFrame([item for item in cursor])
    _data = _data.assign(datetime=pd.to_datetime(_data['datetime']))
    # _data.append([str(item['code']), float(item['open']), float(item['high']), float(
    #     item['low']), float(item['close']), int(item['up_count']), int(item['down_count']), float(item['vol']), float(item['amount']), item['datetime'], item['time_stamp'], item['date'], item['type']])

    # _data = DataFrame(_data, columns=[
    #     'code', 'open', 'high', 'low', 'close', 'up_count', 'down_count', 'volume', 'amount', 'datetime', 'time_stamp', 'date', 'type'])

    # _data['datetime'] = pd.to_datetime(_data['datetime'])
    _data = _data.set_index('datetime', drop=False)
    if format in ['numpy', 'np', 'n']:
        return numpy.asarray(_data)
    elif format in ['list', 'l', 'L']:
        return numpy.asarray(_data).tolist()
    elif format in ['P', 'p', 'pandas', 'pd']:
        return _data



def MT_fetch_stock_day(code, count, end, format='numpy', frequence='day', collections=DATABASE.stock_day):
    """'获取股票日线'

    Returns:
        [type] -- [description]

        感谢@几何大佬的提示
        https://docs.mongodb.com/manual/tutorial/project-fields-from-query-results/#return-the-specified-fields-and-the-id-field-only

    """

    # start = str(start)[0:10]
    end = str(end)[0:10]
    #code= [code] if isinstance(code,str) else code

    # code checking
    code = QA_util_code_tolist(code)

    if QA_util_date_valid(end):

        cursor = collections.find({
            'code': {'$in': code}, "date_stamp": {
                "$lte": QA_util_date_stamp(end),
                # "$gte": QA_util_date_stamp(start)
            }}, {"_id": 0}, batch_size=10000).sort([("date_stamp", -1)]).limit(count)
        #res=[QA_util_dict_remove_key(data, '_id') for data in cursor]

        res = pd.DataFrame([item for item in cursor])
        try:
            res = res.assign(volume=res.vol, date=pd.to_datetime(
                res.date)).drop_duplicates((['date', 'code'])).query('volume>1').set_index('date', drop=False)
            res = res.loc[:, ['code', 'open', 'high', 'low',
                             'close', 'volume', 'amount', 'date']]
        except:
            res = None
        if format in ['P', 'p', 'pandas', 'pd']:
            return res
        elif format in ['json', 'dict']:
            return QA_util_to_json_from_pandas(res)
        # 多种数据格式
        elif format in ['n', 'N', 'numpy']:
            return numpy.asarray(res)
        elif format in ['list', 'l', 'L']:
            return numpy.asarray(res).tolist()
        else:
            print("QA Error QA_fetch_stock_day format parameter %s is none of  \"P, p, pandas, pd , json, dict , n, N, numpy, list, l, L, !\" " % format)
            return None
    else:
        QA_util_log_info(
            'QA Error QA_fetch_stock_day data parameter count=%s end=%s is not right' % (count, end))


def MT_fetch_stock_min(code, count, end, format='numpy', frequence='1min', collections=DATABASE.stock_min):
    '获取股票分钟线'
    if frequence in ['1min', '1m']:
        frequence = '1min'
    elif frequence in ['5min', '5m']:
        frequence = '5min'
    elif frequence in ['15min', '15m']:
        frequence = '15min'
    elif frequence in ['30min', '30m']:
        frequence = '30min'
    elif frequence in ['60min', '60m']:
        frequence = '60min'
    else:
        print("QA Error QA_fetch_stock_min parameter frequence=%s is none of 1min 1m 5min 5m 15min 15m 30min 30m 60min 60m" % frequence)

    _data = []
    # code checking
    code = QA_util_code_tolist(code)

    cursor = collections.find({
        'code': {'$in': code}, "time_stamp": {
            # "$gte": QA_util_time_stamp(start),
            "$lte": QA_util_time_stamp(end)
        }, 'type': frequence
    }, {"_id": 0}, batch_size=10000).sort([("time_stamp", -1)]).limit(count)

    res = pd.DataFrame([item for item in cursor])
    try:
        res = res.assign(volume=res.vol, datetime=pd.to_datetime(
            res.datetime)).query('volume>1').drop_duplicates(['datetime', 'code']).set_index('datetime', drop=False)
        # return res
    except:
        res = None
    if format in ['P', 'p', 'pandas', 'pd']:
        return res
    elif format in ['json', 'dict']:
        return QA_util_to_json_from_pandas(res)
    # 多种数据格式
    elif format in ['n', 'N', 'numpy']:
        return numpy.asarray(res)
    elif format in ['list', 'l', 'L']:
        return numpy.asarray(res).tolist()
    else:
        print("QA Error QA_fetch_stock_min format parameter %s is none of  \"P, p, pandas, pd , json, dict , n, N, numpy, list, l, L, !\" " % format)
        return None


stock_list_df = QA.QA_fetch_stock_list_adv()
def MT_get_bars(code, count, end_tm, unit, fields=None):
    '''
    在rqalpha或者其他环境中获取股票数据（QA数据库中的股票数据）。因为其他框架的code命名与QA规范不一致.默认前复权，没有给出控制复权因子的参数
    返回的数据包含end_tm当天，如果不想包含end_tm当天，需要处理
    由于QA不支持：
    1.股票和指数统一接口
    2.日线和分钟线统一接口
    3.指定某日期end_tm，获取该日期前count数量的数据
    @param code: 指数或日线代码
    @param count: 数量
    @param end_tm: 指定结束日期
    @param unit: 级别。日线 分钟
    @param fields: 返回columns
    @return: 返回df
    '''

    # print("code is : %s ,count is %s , unit is : %s , end_tm is : %s" % (code,count,unit,str(end_tm)))

    # 1.区别code是指数还是股票
    # 聚宽股票代码格式      '600000.XSHG'   XSHE
    # Tushare股票代码格式   '600000.SH'      SZ


    if code.isdigit():
        print("Pleace input suffix name.")
        return

    code_front= code.split(".")[0]
    code_back = code.split(".")[1]

    if 'XSHG' in code_back or 'SH' in code_back:
        code_back = 'sh'
    elif 'XSHE' in code_back or 'SZ' in code_back:
        code_back = 'sz'

    if isinstance(end_tm, datetime.datetime):
        end_date = QA_util_datetime_to_strdatetime(end_tm)
    elif isinstance(end_tm, str):
        end_date = end_tm

    tmp = stock_list_df[(stock_list_df['code'] == code_front) & (stock_list_df['sse'] == code_back)]
    if tmp.empty:
        # index
        if "d" in unit:
            result = MT_fetch_index_day_adv(code_front, count, end_date)
        elif "m" in unit:
            result = MT_fetch_index_min_adv(code, count, end_date, unit)
    else:
        # stock
        if "d" in unit:
            result = MT_fetch_stock_day_adv(code_front, count, end_date)
        elif "m" in unit:
            result = MT_fetch_stock_min_adv(code, count, end_date, unit)

    # 默认前复权
    try:
        result = result.to_qfq().data
    except:
        result = result.data

    if fields is not None:
        if ADJ_FACTOR in fields:
            # 日线有除权信息，分钟线没有
            # stock有除权，index没有
            if "m" in unit:
                print("分钟线没有复权信息。请通过日线获取")
                return
            if tmp.empty:
                # index
                result[ADJ_FACTOR] = 1

        result = result[fields]

    else:
        result = result

    if result is None:
        return pd.DataFrame()

    result.reset_index(inplace=True)

    if 'date' in result.columns:
        index_name = 'date'
    elif 'datetime' in result.columns:
        index_name = 'datetime'

    result = result.set_index(index_name)
        
    return result


if __name__ == '__main__':
    # data = MT_fetch_index_min_adv('000300',5,'2017-01-01','1min')
    # print(data.data)
    # data = MT_fetch_index_day_adv('000300',5,'2017-01-01')
    # print(data.data)
    # data = MT_fetch_stock_min_adv('000651',5,'2019-10-15','1min')
    # print(data.data)
    # data = MT_fetch_stock_day_adv('000651',5,'2017-01-01')
    # print(data.data)

    data = QA.QA_fetch_stock_day_adv('000651','2019-02-01',end="2012-03-26")
    # data = MT_get_bars('000651.XSHE', 2, '2019-02-26', 'daily', fields=[ADJ_FACTOR])

    # self.dbkline.get_bars(code, count=2, end_tm=last_tm, unit='daily', fields=[ADJ_FACTOR])

    print(data)
