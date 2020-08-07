import pandas as pd

#显示所有列
pd.set_option('display.max_columns', None)
#显示所有行
pd.set_option('display.max_rows', None)
#设置value的显示长度为100，默认为50
pd.set_option('max_colwidth',100)
pd.set_option('display.width',200)
df_read = pd.read_csv('Result.csv')
df_read = df_read[df_read['eps'] > 0 ].sort_values(by='underRate',ascending=False)
# print(df_read.reset_index(drop=True))

df_price_scale_gt1 = df_read[df_read['underRate'] > 1.0]
print(df_price_scale_gt1['price_scale'].mean())

df_price_scale_ls1 = df_read[df_read['underRate'] < 1.0]
print(df_price_scale_ls1['price_scale'].mean())