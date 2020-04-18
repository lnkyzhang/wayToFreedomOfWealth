import pymongo
import tushare as ts
import pandas as pd
import datetime
from jqdatasdk import auth

ts.set_token('d79c15feb3718d16953d1524f8076a076a33f55efb9eafa0d5484310')

pro = ts.pro_api()

# pd全局设置
pd.set_option('display.max_rows', 5000)
pd.set_option('display.max_columns', 100)
pd.set_option('display.width', 300)

# 登录jqdata
auth('15640316927', '316927')  # 账号是申请时所填写的手机号；密码为聚宽官网登录密码，新申请用户默认为手机号后6位

myClient = pymongo.MongoClient('mongodb://localhost:27017/')
