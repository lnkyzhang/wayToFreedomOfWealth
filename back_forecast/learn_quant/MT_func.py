import calendar
import concurrent
import datetime
import time
from concurrent.futures.thread import ThreadPoolExecutor

from QUANTAXIS import QA_util_code_tolist, QA_util_time_stamp, QA_util_log_info, QA_util_to_datetime, \
    QA_util_datetime_to_strdate
from dateutil.relativedelta import relativedelta

import tushare as ts
import numpy as np
import pandas as pd

import pymongo

import QUANTAXIS as QA
import asyncio


# pd全局设置
pd.set_option('display.max_rows', 5000)
pd.set_option('display.max_columns', 100)
pd.set_option('display.width', 300)

# tushare 账户设置
ts.set_token('d79c15feb3718d16953d1524f8076a076a33f55efb9eafa0d5484310')

pro = ts.pro_api()

# 本地mongodb连接
mydbclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = mydbclient['mt']

def get_month_trade_date(start,end):
    '''
    从tushare获取交易日历
    @param start:
    @param end:
    @return: lsit 类型的交易日期
    '''
    stock_trade_date = pro.trade_cal(exchange='', start_date=start, end_date=end)
    stock_trade_date_month = stock_trade_date[stock_trade_date["is_open"] == 1]
    stock_trade_date_month['cal_date'] = stock_trade_date_month['cal_date'].apply(lambda x : pd.to_datetime(x, format='%Y%m%d'))
    stock_trade_date_month.index = stock_trade_date_month['cal_date']
    dfg = stock_trade_date_month.resample('M')
    business_end_day = dfg.apply({'cal_date': np.min})
    return business_end_day["cal_date"].reset_index(drop=True).tolist()


tread_date_df = pd.DataFrame()
def get_starttm_trade_date_by_count(count,end_date):
    '''
    根据输入的count获取指定日期end_tm之前的日期
    @param count: 输入的指定数量
    @param end_tm: 输入的指定日期
    @return: df
    '''

    global tread_date_df

    if tread_date_df.empty:
        today = datetime.date.today().strftime("%Y%m%d")
        tread_date_df = pro.trade_cal(exchange='', start_date='19930101', end_date=today)
        tread_date_df = tread_date_df[tread_date_df['is_open'] == 1]
        tread_date_df['index'] = range(tread_date_df.shape[0])
        tread_date_df.set_index('index',inplace=True)
        print("给交易日期赋值")

    end_date = end_date.strftime("%Y%m%d")
    end_tm_index = tread_date_df[tread_date_df['cal_date'] == end_date].index.values[0]
    start_date = tread_date_df.iloc[end_tm_index - count]['cal_date']
    start_date = datetime.datetime.strptime(start_date, '%Y%m%d')

    return start_date







def stock_data_add_ind(func,date,stock_day_data,res_adv):
    '''
    通过输入数据，计算参数
    用于选股银子比如pe等的计算
    @param func:apply中应用的方法
    @param date:日期,用来选择stock日线数据
    @param stock_day_data:股票日线数据
    @param res_adv:选股用的金融数据
    @return:返回通过func 计算的某个因子
    '''

    if func is None:
        raise RuntimeError('func is None')
    if stock_day_data is None:
        raise RuntimeError('stock_day_data is None')
    if date is None:
        raise RuntimeError('date is None')

    try:
        result = stock_day_data.data.xs(date,level=0).apply(func,axis=1,args=(date,res_adv,))
    except:
        result = stock_day_data.xs(date,level=0).apply(func,axis=1,args=(date,res_adv,))
    return result


def func_map_pe(x, date, res_adv):
    try:
        # date = datetime.datetime.strptime(date, '%Y-%m-%d')
        last_year_final_day = datetime.date(year=date.year - 1, month=12, day=31)
        result = x['close'] / res_adv.data['EPS'].xs(x.name, level=1).loc[last_year_final_day]
        return result
    except Exception :
        print('Exception')
        return 0


def func_map_pb(x,date,res_adv):
    try:
        # date = datetime.datetime.strptime(date, '%Y-%m-%d')
        last_year_final_day = datetime.date(year=date.year - 1, month=12, day=31)
        result = x['close'] / res_adv.data['netAssetsPerShare'].xs(x.name, level=1).loc[last_year_final_day]
        return result
    except Exception:
        print('Exception')
        return 0


def func_map_marketcap(x,date,res_adv):
    try:
        # date = datetime.datetime.strptime(date, '%Y-%m-%d')
        last_year_final_day = datetime.date(year=date.year - 1, month=12, day=31)
        result = x['close'] * res_adv.data['totalCapital'].xs(x.name, level=1).loc[last_year_final_day]
        return result
    except Exception:
        print('Exception')
        return 0


def func_map_ROIC(x,date,res_adv):
    try:
        last_quarter_final_day = date - pd.tseries.offsets.QuarterEnd()
        result = res_adv.data['rateOfReturnOnInvestmentIncome'].xs(x.name, level=1).loc[last_quarter_final_day]
        return result
    except Exception:
        print('Exception')
        return 0


def func_map_NPGR(x,date,res_adv):
    try:
        last_quarter_final_day = date - pd.tseries.offsets.QuarterEnd()
        result = res_adv.data['netProfitGrowthRate'].xs(x.name, level=1).loc[last_quarter_final_day]
        return result
    except Exception:
        print('Exception')
        return 0


def func_map_ORS(x,date,res_adv):
    try:
        last_quarter_final_day = date - pd.tseries.offsets.QuarterEnd()
        result = res_adv.data['operatingRevenueSingle'].xs(x.name, level=1).loc[last_quarter_final_day]
        return result
    except Exception:
        print('Exception')
        return 0


def select_stocklist(factors_data,stock_counts):
    """
    首先处理NaN值情况.选股时的日线数据不能是复权的数据，否则计算的pe等值是不正确的
    打分的具体步骤、返回股票池
    因子升序从小到大分10组，第几组为所在组得分
    市值-market_cap、市盈率-pe_ratio、市净率-pb_ratio
    因子降序从大到小分10组，第几组为所在组得分
    ROIC-return_on_invested_capital、inc_revenue-营业总收入 和inc_profit_before_tax-利润增长率
    @param stock_counts: 排名前多少个
    @param factors_data:
    @return:
    """
    factors_data.to_csv('factor.csv', mode='a')
    # 循环每个因子去处理
    factors_data = factors_data.dropna(axis=0,how='all')

    sort_up = ['market_cap', 'pe_ratio', 'pb_ratio']
    for name in factors_data.columns:
        if name in sort_up:
            factor = factors_data.sort_values(by=name)[name]
        else:
            factor = factors_data.sort_values(by=name, ascending=False)[name]

        factor = pd.DataFrame(factor)
        factor[name + '_score'] = 0

        # 进行打分
        # 先求出每组数量，然后根据数量一次给出分数
        stock_groupnum = len(factors_data) // 10
        for i in range(10):
            if i == 9:
                factor.loc[(i + 1) * stock_groupnum:,name + '_score'] = i + 1
            factor.loc[i * stock_groupnum: (i + 1) * stock_groupnum,name + '_score'] = i + 1
        factors_data = pd.concat([factors_data, factor[name + '_score']], axis=1,sort=False)

    all_score = factors_data[
        ['marketcap_score', 'pe_score', 'pb_score', 'roic_score', 'ors_score',
         'npgr_score']].sum(1).sort_values()

    # tem_df = pd.DataFrame([factors_data])
    # tem_df["date"] = str(self.running_time)[:10]
    factors_data.to_csv('all_score.csv', mode='a')



    hold_list = all_score.index[:stock_counts].tolist()
    return hold_list


def cal_market_value(positions):
    '''
    计算账户市值。要计算资产需要加上cash
    @param positions: 传入的是模拟账户的position。比如self.acc.positions
    @return: 市值
    '''
    cost_value = 0
    profit_value = 0
    for key in positions:
        cost_value += positions[key].position_cost_long
        profit_value += positions[key].position_profit_long

        # if positions[key].open_cost_long + positions[key].position_profit_long > 0:
        #     print("code is :%s , market_value is :%s" %(key,positions[key].open_cost_long + positions[key].position_profit_long))

    return cost_value + profit_value

def cal_buy_volume(money,comissions_coeff,price):
    '''
    计算可以购买的手数
    每手100股
    交易佣金最少5元
    @param money: 购买股票的资金
    @param comissions_coeff: 交易佣金费率
    @param price: 股票价格
    @return: 可以购买手数
    '''
    volume = money / (price * (1 + comissions_coeff))
    volume = int(volume / 100) * 100
    # 交易佣金最少5元
    if volume * comissions_coeff * price < 5:
        volume = (money - 5) / price
        volume = int(volume / 100) * 100
    return volume
    # return money * ( 1 - comissions_coeff) / price


def get_index_code(index,date, suffix=False):
    '''
    获取指数权重股
    MSCI:
    CSI:中证指数
    SSE:上交所指数
    SZSE:深交所指数
    CICC:中金所指数

    沪深300 ： '399300.SZ'
    SW:申万指数
    @param index: 指数代码,需要加上交易所缩写。比如沪深300 399300.SZ
    @param date: 查询日期
    @param suffix: 是否包含后缀名
    @return: 返回指数list
    '''
    date = datetime.datetime.strptime(date, '%Y-%m-%d')
    monthRange = calendar.monthrange(date.year, date.month)[1]

    firstDay = datetime.date(year=date.year, month=date.month, day=1).strftime("%Y%m%d")
    lastDay = datetime.date(year=date.year, month=date.month, day=monthRange).strftime("%Y%m%d")

    df = pro.index_weight(index_code=index, start_date=firstDay, end_date=lastDay)

    if suffix:
        code_list = df['con_code'].to_list()
    else:
        # 只保留股票代码，不保留小数点后的英文字母
        # df['con_code'].apply(lambda x:re.sub('\..+','',x),axis=1)
        code_list = df['con_code'].apply(lambda x:x.split('.')[0]).to_list()
    return code_list


def result_analysis_stock_profit(positions):
    '''
    分析回测结果，包括各股票的profit、持仓时间、交易次数
    @param position: 账户的positions
    @return: df
    '''

    result_df = pd.DataFrame(columns=['code','profit'])

    cost_value = 0
    profit_value = 0
    for key in positions:
        profit_value += positions[key].position_profit_long
        result_df = result_df.append({'code':key,'profit':profit_value},ignore_index=True)

    result_df = result_df.sort_values(by='profit', ascending=False)

    result_df.to_excel("profit.xls")

    return result_df


def test_repeat():
    '''
    测试沪深300权重股票的变化
    @return:
    '''
    begin = datetime.date(2010, 6, 1)
    end = datetime.date(2019, 6, 7)

    day = begin
    code_list_last = []
    while(day < end):
        day += relativedelta(months=+1)
        print(day)
        code_list = get_index_code('399300.SZ', day.strftime("%Y-%m-%d"))
        if len(code_list_last) == 0:
            code_list_last = code_list

        diff_list = set(code_list).difference(set(code_list_last))
        if len(diff_list) > 0:
            print("交集: ", set(code_list).intersection(set(code_list_last)))
            print("新增: ", diff_list)
            print("删除: ", set(code_list_last).difference(set(code_list)))
        code_list_last = code_list


code_df = pd.DataFrame()


def add_suffix_name(code, rule=1):
    '''
    给rqalpha添加后缀名，比如000651返回000651.xshe
    如果传入的code是包含后缀名的，则直接返回
    .xshe:深证    SZ
    .xshg:上海    SH
    @param code: 股票的string
    @return: 返回带有后缀名的string
    @param rule:    rule=1,则添加后缀名为.XSHE XSHG .
                    rule=2，则添加后缀名为SZ,SH
    '''

    global code_df
    if code_df.empty:
        code_df = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol')

        def func(x):
            code_str = x['ts_code']
            if '.SZ' in code_str:
                result = code_str.replace('.SZ', '.XSHE')
            elif '.SH' in code_str:
                result = code_str.replace('.SH', '.XSHG')

            return result
        if rule == 1:
            code_df['suffix_name'] = code_df.apply(func,axis=1,args=())
        elif rule == 2:
            code_df['suffix_name'] = code_df['ts_code']

    if isinstance(code, list):
        code_suffix = code_df.loc[code_df['symbol'].isin(code)]['suffix_name'].to_list()
    elif isinstance(code, str):
        if ".XSH" in code:
            return code
        code_suffix = code_df[code_df['symbol'] == code]['suffix_name'].values[0]

    return code_suffix


def mt_get_stock_min(code, start, end, frequence='1min', collections=mydb.stock_min):
    '获取股票分钟线'
    _data = []
    code = QA_util_code_tolist(code)
    cursor = collections.find({
        'code': {'$in': code},
        "time_stamp": {"$gte": QA_util_time_stamp(start), "$lte": QA_util_time_stamp(end)},
        'type': frequence},
        {"_id": 0},
        batch_size=10000)
    # for item in cursor:
    _data = pd.DataFrame([item for item in cursor])
    # print(_data)
    _data = _data.assign(datetime=pd.to_datetime(_data['datetime']))
    _data = _data.set_index('datetime', drop=False)

    return _data


def remove_mongodb_duplicate_data():
    '''
    删除QA数据库中的重复数据
    该重复数据是由于通过tick数据生成分钟数据时所产生。（错误操作）
    删除代码留下供未来参考
    @return:
    '''
    # 条件删除
    QA.DATABASE.stock_min.delete_many({'type': {"$exists": False}})
    # 删除结果验证
    date = QA.DATABASE.stock_min.find({'type': {"$exists": False}})
    for index in date:
        print(index)

# stock_list_df = QA.QA_fetch_stock_list_adv()
def mt_download_min_data(code, start_time):
    '''
    下载指数的分钟线的数据,保存到QA数据库中
    不占内存，下载完就保存到数据库
    @param start_time: 开始时间
    @param code: 指数代码
    @return:
    '''

    if code.isdigit():
        print("Pleace input suffix name.")
        return

    code_front= code.split(".")[0]
    code_back = code.split(".")[1]

    if 'XSHG' in code_back or 'SH' in code_back:
        code_back = 'sh'
    elif ('XSHE' in code_back) or ('SZ' in code_back):
        code_back = 'sz'

    tmp = stock_list_df[(stock_list_df['code'] == code_front) & (stock_list_df['sse'] == code_back)]
    if tmp.empty:
        # index
        mydb = QA.DATABASE.index_min
        fetch_1min_func = QA.QA_fetch_index_min_adv
        fetch_trans_func = QA.QA_fetch_get_index_transaction

    else:
        # stock
        mydb = QA.DATABASE.stock_min
        fetch_1min_func = QA.QA_fetch_stock_min_adv
        fetch_trans_func = QA.QA_fetch_get_stock_transaction

    code = str(code)[0:6]

    for type in ['1min', '5min', '15min', '30min', '60min']:

        def save2mongodb(data_1min, type):
            data_1min = data_1min.reset_index().set_index('datetime').sort_index()
            data = QA.QA_data_min_resample(data_1min, type)
            data = data.reset_index()
            data = data.assign(time_stamp=data.datetime.apply(QA.QA_util_time_stamp), type=type)

            if 'volume' in data.columns:
                # QA的内部方法会识别是否包含名称为volume的列，不包含的话就不能获取到值
                data.rename(columns={'volume': 'vol'}, inplace=True)

            mydb.insert_many(QA.QA_util_to_json_from_pandas(data))


        ref_ = mydb.find({'code': str(code)[0:6], 'type': type})

        if ref_.count() > 0:
            # start_time = ref_[ref_.count() - 1]['datetime']
            end_time = ref_[0]['datetime']
            print("end_time is :", end_time)
            end_time = QA.QA_util_to_datetime(end_time) + datetime.timedelta(days=-1)  # 减去一天
            end_time = QA.QA_util_datetime_to_strdate(end_time)
            print("end_time - 1 is :", end_time)

            if start_time >= end_time:
                print(print(
                    "code : %s , type : %s ,start_time is bigger than end_time,check please." % (type, code)))
            else:
                try:
                    # 1.先从数据库中取1min数据
                    data_1min = fetch_1min_func(code, start_time, end_time, frequence='1min').data

                except:
                    end_time = QA.QA_util_to_datetime(end_time)
                    start_time = QA.QA_util_to_datetime(start_time)

                    for i in range((end_time - start_time).days + 1):
                        download_time = end_time - datetime.timedelta(i)
                        print("download_time :", download_time)

                        download_time = QA.QA_util_datetime_to_strdate(download_time)

                        tick_data = fetch_trans_func('tdx', code, download_time, download_time)
                        if tick_data is not None:
                            # 2.如果数据为空，则下载并保存到数据库。（此条件仅在1min条件下进入）
                            data_1min = QA.QA_data_tick_resample_1min(tick_data, '1min').reset_index()
                            save2mongodb(data_1min, type)
                    start_time = QA.QA_util_datetime_to_strdate(start_time)

                save2mongodb(data_1min, type)


def cal_father_question():
    x = 1
    while(True):
        x += 1
        if ( x % 2 == 1 \
                and x % 3 == 0 \
                and x % 4 == 1 \
                and x % 5 == 1 \
                and x % 6 == 3 \
                and x % 7 == 0 \
                and x % 8 == 1 \
                and x % 9 == 0):
            print(x)
        if x > 100000:
            return



if __name__ == '__main__':
    cal_father_question()
    # df = pro.index_weight(index_code='000016.SH', start_date='20180901', end_date='20180930')
    # df = pro.index_basic(market='SSE')
    # print(df)
    # df = pro.index_weight(index_code='000016.SH', start_date='20190910', end_date='20190920')
    # df = pro.index_basic(market='SZSE')
    # print(df)

    # print(get_index_code('399300.SZ','2019-10-06'))

    # test_repeat()
    #
    # print(get_start_trade_date_by_count(3,'19930201'))
    # print('============================')

    # mt_download_min_data('000651.XSHE', '2017-01-03')

    # # 条件删除
    # QA.DATABASE.stock_min.delete_many({'type': {"$in": ['5min', '15min', '30min', '60min']}, 'code': '000651','volume': {"$exists": True}})
    # # 删除结果验证
    # date = QA.DATABASE.stock_min.find({'type': {"$in": ['5min', '15min', '30min', '60min']}, 'code': '000651','volume': {"$exists": True}})
    # for index in date:
    #     print(index)

    # ref_ = QA.DATABASE.stock_day.find({'code': str('000651')[0:6], "date_stamp": {
    #         "$gte": QA_util_time_stamp('2017-01-03'),
    #         "$lte": QA_util_time_stamp('2018-01-01')
    #     }, })
    # for index in ref_:
    #     print(index)

    # data = QA.QA_fetch_stock_day_adv('000651',end='2020-01-05')
    # # print(data.data)
    # tushare_start_date = '2018-01-06'
    # end_date = '2018-02-01'
    # print(end_date.replace('-', ''))
    # df = pro.adj_factor(ts_code='000651.SZ', start_date=tushare_start_date.replace('-', ''), end_date=end_date.replace('-', ''))
    # print(df)

    # code_list = get_index_code('399300.SZ', '2019-10-26')
    # print(code_list)
    # if '600100' in code_list:
    #     print('yes')
    # mt_get_bars('000001.XSHG')

    # def count():
    #     print("One")
    #     time.sleep(1)
    #     print("Two")
    #     return "over"
    #
    #
    # for _, pos in self._curPos.items():
    #     if not pos.onOpen(date, self._dataEngine):
    #         return False
    #
    # import concurrent.futures as cf
    #
    # async def async_account_open():
    #     with cf.ThreadPoolExecutor(max_workers=2) as executor:
    #         loop = asyncio.get_event_loop()
    #         futures = (loop.run_in_executor(None, pos.onOpen,date, self._dataEngine ) for _, pos in self._curPos.items())
    #         for result in await asyncio.gather(*futures):
    #             if not result:
    #                 return False
    #
    #
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(async_account_open())
    #
    #
    # import concurrent.futures as cf
    #
    # async def main():
    #     with cf.ThreadPoolExecutor(max_workers=2) as executor:
    #         loop = asyncio.get_event_loop()
    #         futures = (loop.run_in_executor(None, count, ) for i in range(10))
    #         for result in await asyncio.gather(*futures):
    #             print(result)
    #             pass



    # ref_ = QA.DATABASE.stock_min.find({'code': str('000651')[0:6], 'type': "1min"})
    # for index in ref_:
    #     print(index)



    # a = mt_get_stock_min('000651',("2019-01-03"),("2019-05-01"))
    # print(a)
    # print(df)

    # mt_download_min_data('000651.SZ','2019-01-01')

    # df.apply(func,axis=1)

    # df = pro.index_weight(index_code='000015.sh', start_date='20200101', end_date='20200201')[:300]
    # a = df["con_code"].apply(lambda x: x[:6]).to_list()
    # # for i in range(len(a)):
    # #     a[i] = int(a[i])
    # b = str(a)
    #
    # print(b.replace("'", ""))

    # str_list = "603888, 603883, 603877, 603868, 603816, 603806, 603766, 603658, 603589, 603569, 603568, 603556, 603528, 603515, 603444, 603377, 603369, 603355, 603328, 603228, 603225, 603198, 603188, 603169, 603077, 603025, 603019, 603001, 603000, 601969, 601928, 601880, 601811, 601777, 601717, 601699, 601689, 601678, 601311, 601233, 601231, 601200, 601168, 601128, 601127, 601020, 601016, 601002, 601001, 601000, 600996, 600993, 600978, 600971, 600970, 600967, 600939, 600936, 600917, 600908, 600894, 600885, 600884, 600881, 600880, 600879, 600875, 600874, 600872, 600869, 600863, 600862, 600859, 600848, 600839, 600835, 600826, 600823, 600811, 600808, 600801, 600787, 600776, 600773, 600770, 600765, 600759, 600757, 600755, 600754, 600751, 600750, 600748, 600743, 600737, 600729, 600718, 600717, 600694, 600687, 600673, 600664, 600657, 600655, 600651, 600648, 600645, 600643, 600642, 600640, 600639, 600635, 600633, 600628, 600623, 600618, 600614, 600611, 600600, 600598, 600597, 600594, 600587, 600584, 600582, 600580, 600578, 600575, 600572, 600158, 600155, 600151, 600143, 600141, 600138, 600126, 600125, 600122, 600120, 600108, 600098, 600094, 600086, 600079, 600073, 600064, 600062, 600060, 600059, 600058, 600056, 600053, 600039, 600037, 600026, 600022, 600017, 600006, 600004, 300383, 300376, 300324, 300297, 300291, 300287, 300274, 300273, 300266, 300257, 300253, 300244, 300202, 300199, 300197, 300182, 300166, 300159, 300147, 300146, 300134, 300133, 300116, 300115, 300113, 300088, 300058, 300055, 300043, 300039, 300032, 300026, 300010, 300002, 300001, 002818, 002815, 002807, 002745, 002709, 002707, 002701, 002699, 002690, 002681, 002672, 002670, 002665, 002663, 002657, 002642, 002640, 002635, 002603, 002589, 002588, 002583, 002573, 002551, 002544, 002517, 002512, 002506, 002505, 002503, 002491, 002489, 002482, 002479, 002477, 002463, 002444, 002440, 002439, 002437, 002434, 002431, 002428, 002422, 002416, 002414, 002410, 002408, 002407, 002405, 002400, 002392, 002390, 002384, 002375, 002373, 002371, 002368, 002366, 002359, 002358, 002354, 002353, 002345, 002344, 002342, 002340, 002332, 002325, 002317, 002311, 002308, 002299, 002285, 002281, 002280, 002277, 002276, 002273, 002271, 002269, 002268, 002266, 002261, 002254, 002251, 002250, 002249, 002244, 002242, 002233, 002223, 002221, 002195, 002191, 002190, 002183, 002179, 002176, 002155, 002152, 002147, 002131, 002128, 002127, 002123, 002122, 002118, 002106, 002093, 002092, 002078, 002073, 002064, 002063, 002056, 002051, 002050, 002049, 002048, 002041, 002038, 002032, 002030, 002028, 002022, 002019, 002018, 002013, 002011, 002005, 002004, 002002, 002001, 001696, 000999, 000998, 000997, 000990, 000988, 000987, 000981, 000979, 000977, 000975, 000970, 000969, 000960, 000939, 000937, 000930, 000926, 000897, 000887, 000878, 000877, 000860, 000848, 000830, 000829, 000825, 000816, 000807, 000806, 000786, 000778, 000777, 000766, 000762, 000761, 000758, 000732, 000729, 000727, 000718, 000712, 000703, 000690, 000685, 000681, 000680, 000669, 000667, 000662, 000661, 000656, 000652, 000636, 000612, 000600, 000598, 000596, 000592, 000587, 000581, 000572, 000566, 000563, 000552, 000547, 000543, 000541, 000536, 600566, 600565, 600563, 600557, 600545, 600536, 600525, 600521, 600517, 600516, 600511, 600503, 600500, 600499, 600481, 600478, 600466, 600460, 600458, 600438, 600435, 600428, 600426, 600422, 600418, 600416, 600410, 600409, 600395, 600393, 600392, 600388, 600380, 600366, 600348, 600346, 600338, 600335, 600329, 600325, 600317, 600316, 600315, 600312, 600307, 600300, 600298, 600292, 600291, 600289, 600284, 600282, 600280, 600277, 600270, 600267, 600266, 600260, 600259, 600256, 600240, 600216, 600201, 600195, 600187, 600184, 600183, 600179, 600176, 600171, 600169, 600166, 600161, 600160, 000528, 000519, 000513, 000501, 000488, 000426, 000418, 000401, 000400, 000158, 000156, 000099, 000090, 000089, 000078, 000066, 000062, 000061, 000050, 000049, 000039, 000031, 000028, 000027, 000025, 000021, 000012, 000009, 000006"
    # print(str_list.replace(" ",""))

    # a = QA.QA_fetch_financial_report_adv('000651', '2018-12-01', '2019-12-01')
    # print(a.data)

    # trade_date = pro.trade_cal(exchange='', start_date='20150101', end_date='20181231')
    #
    # trade_date = trade_date[trade_date['is_open'] == 1]
    #
    # for index, row in trade_date['cal_date'].iteritems():
    #     print("trade date is :",row,"=====================")
    #     result = pro.daily_basic(trade_date=row)
    #     print(result)


    # result = pro.daily_basic(start_date='20151010' , end_date="20161010")
    # print(result)


    pass


# {'_id': ObjectId('5e3d619d15dd7f15edc4ae39'), 'datetime': '2017-01-03 10:30:00', 'code': '000651', 'open': 24.7, 'high': 25.22, 'low': 24.7, 'close': 25.03, 'volume': 26236000.0, 'amount': 6559418.6000000015, 'time_stamp': 1483410600.0, 'type': '60min'}
# {'_id': ObjectId('5e3a44bbc3f46294cbcc1e37'), 'open': 61.45, 'close': 61.36, 'high': 61.48, 'low': 60.66, 'vol': 10755300.0, 'amount': 656681984.0, 'datetime': '2020-02-04 14:00:00', 'code': '000651', 'date': '2020-02-04', 'date_stamp': 1580745600.0, 'time_stamp': 1580796000.0, 'type': '60min'}

