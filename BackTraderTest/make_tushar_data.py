
import tushare as ts
import pandas as pd

ts.set_token('d79c15feb3718d16953d1524f8076a076a33f55efb9eafa0d5484310')

pro = ts.pro_api()

df = pro.index_daily(ts_code='000001.SH')
colsused = ['date',
            'open', 'high', 'low', 'close', 'volume', 'openinterest']

df.rename(columns={'trade_date': 'date', 'vol': 'volume'}, inplace=True)
df['openinterest'] = ''
df['date'] = pd.to_datetime(df['date'])
df = df[colsused]
df.set_index(["date"], inplace=True)
df.sort_index(inplace=True)
df.to_csv('shindex.csv')
print(df)

