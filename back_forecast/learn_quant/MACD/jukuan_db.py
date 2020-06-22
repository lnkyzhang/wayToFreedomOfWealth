# -*- encoding:utf-8 -*-
from math import ceil

import QUANTAXIS as QA
from QUANTAXIS.QAUtil.QADate import QA_util_datetime_to_strdatetime

from MT_func import *
from MT_get_data import MT_get_bars
from jukuan_macd_config import *

"""
普量学院量化投资课程系列案例源码包
普量学院版权所有
仅用于教学目的，严禁转发和用于盈利目的，违者必究
Plouto-Quants All Rights Reserved

普量学院助教微信：niuxiaomi3
"""

"""
聚宽数据查询
"""


class QADBBase:
    # 数据获取
    def __init__(self):

        pass

    @classmethod
    def get_bars(cls, code, count, end_tm, unit, fields):
        """
        获取历史数据，可查询多个标的多个数据字段，返回数据格式为 DataFrame
        :param code:    要获取数据的股票
        :param count:   数量, 返回的结果集的行数
        :param end_tm:  字符串或者 [datetime.datetime]/[datetime.date] 对象, 结束时间.包含此日期。
                        注意: 当取分钟数据时, 如果 end_date 只有日期, 则日内时间等同于 00:00:00,
                        所以返回的数据是不包括 end_date 这一天的.

        :param unit:    单位时间长度, 几天或者几分钟, 现在支持'Xd','Xm', X是一个正整数,
                        分别表示X天和X分钟(不论是按天还是按分钟回测都能拿到这两种单位的数据),
                        注意, 当X > 1时, field只支持['open', 'close', 'high', 'low', 'volume', 'money']这几个标准字段.
        :param fields: 获取的数据类型，包含：['open', ' close', 'low', 'high', 'volume', 'money', 'factor', '
                        high_limit',' low_limit', 'avg', ' pre_close', 'paused']
        :return:
        """


        return MT_get_bars(code, count, end_tm, unit, fields)


